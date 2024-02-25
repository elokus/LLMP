# Decide how version history should be handled. When storing an instruction and a set of examples ids
# per version, we need to track also the version of the examples. When rolling back, we need to decide whether to
# roll back the examples as well.
#
# Option 1: Roll back the examples as well. This is the most straightforward option, but so that the previous metrics stay
# consistent. However, this might not be the best option, because the examples might have been updated for a reason.
#
# Option 2: Keep the newest version of the examples. This should be preferred option on default. However, this might
# cause issues when rolling back, because the metrics might not be consistent with the updated examples. So we need to
# recompute the metrics for the previous version.
# TODO: add a flag to rollback method for "hard" or "soft" rollback
#
# ---
# # Generation History
# The generation history is a list of generation logs. Each generation log is a dictionary with the following keys:
#     - timestamp: The timestamp of the generation.
#     - input: The input object that was used for the generation.
#     - output: The output object that was generated.
#     - kwargs: Additional keyword arguments that were used for the generation.
#     - example_idx: The index of the example that was used for the generation.
#     - version: The version of the job that was used for the generation.
#
# While tracking the generation we want to add each generation to example records. While performing generations on
# existing examples we want to add update the example output if the new output has a higher validation rank.
#
# # TODO: Move example adding to ExampleManager?
# For this we need to update the add_generation method and remove the example creation from it. This will mean that we
# won't be able to log an example_idx in the generation history as a reference to the example record.
# Instead we could add log the event_id of the generation event.
# This will allow us to use example_manager to add examples from generation history without diluting the size of examples.


import json
from uuid import uuid4

from pathlib import Path
from structgenie.pydantic_v1 import BaseModel, UUID4, Field, validator, root_validator, PrivateAttr
from typing import List, Dict, Optional, Any, Union, Type

from llmp.data_model.events import Event
from llmp.data_model.example_record import ExampleRecord
from llmp.types import EventType
from llmp.utils.encoder import JSONEncoder
from llmp.utils.helper import get_timestamp
from llmp.integration.structgenie import (
    Example,
    InputModel,
    OutputModel,
    Engine,
    ExampleSelector,
    PromptBuilder,
)
from llmp.utils.io_model import hash_from_io_models
from llmp.utils.signature import is_valid_uuid


class JobRecord(BaseModel):
    """
    A representation of a job in the LLMP system.

    The `JobRecord` class captures the core attributes of a job, its associated examples, and its history.

    Attributes:
        _idx (str): A unique identifier for the job.
        job_name (Optional[str]): The name of the job, if provided.
        version (int): The current version of the job, indicating updates or modifications.
        state (int): The current state of the job, indicating if it is active or inactive.
        is_explicit (bool): A flag indicating if the job is explicitly defined.
        input_model (InputModel): The input schema model.
        output_model (OutputModel): The output schema model.
        example_records (List[ExampleRecord]): A list of example records associated with the job.
        instruction (Optional[str]): An optional instruction or description for the job.
        metrics (Optional[Dict[str, float]]): Metrics associated with the job, if available.
        version_history (Dict[int, Any]): A dictionary capturing the history of versions for the job.
        event_log (list[str]): A log of actions performed on the job.
        generation_log (list[dict]): A history of generations associated with the job.

    Methods:
        convert_keys_to_int(cls, item) -> Dict[int, Any]:
            Convert string keys to integers for version history dictionary.

        parse_examples() -> List[Example]:
            Retrieve the parsed examples from the job's example records.

        add_version(instruction: str, examples: List[ExampleRecord], metrics: Dict[str, float]):
            Update the job to a new version with new instruction, examples, and metrics.

        add_action(action: str, version: int = None):
            Log an action in the job's action history.

        add_generation_log(generation_log: dict):
            Log a generation in the job's generation history.

        rollback(version: int):
            Rollback the job to a specific previous version.

        to_template() -> str:
            Convert the job into a template for LLM generation.
    """

    idx: str = Field(default_factory=lambda: uuid4().hex)
    job_name: Optional[str] = None
    version: int = 0
    is_explicit: bool = False
    config: dict = Field(default_factory=dict)

    input_model: InputModel
    output_model: OutputModel

    example_records: List[ExampleRecord] = Field(default_factory=list)
    instruction: Optional[str] = None

    version_history: list[dict] = Field(default_factory=list)
    generation_log: list[dict] = Field(default_factory=list)
    event_log: list[Event] = Field(default_factory=list)

    @property
    def io_hash(self) -> str:
        """Create a hash from the input and output models."""
        return hash_from_io_models(self.input_model, self.output_model, self.instruction)

    def log_event(self, event: Event):
        """Add an event to the job."""
        self.event_log.append(event)

    def log_generation(
            self, input_object: dict, output_object: dict, event_metric: dict, job_settings: dict = None
    ) -> Event:
        """Add a generation to the job."""
        example_id = get_record_by_input(self, input_object).idx if input_in_records(self, input_object) else None
        event = Event.from_generation_job(event_metric, job_settings, example_id=example_id, job_version=self.version)
        self.log_event(event)

        self.generation_log.append(dict(
            event_id=event.event_id,
            input=input_object,
            output=output_object,
        ))
        return event

    def get_examples(self, example_ids: list = None):
        """Parse the examples to the correct version."""
        if example_ids:
            assert all(isinstance(example_id, str) for example_id in example_ids)
            return [record.example for record in self.example_records if str(record.idx) in example_ids]
        return [record.example for record in self.example_records]

    # === unused methods ===

    def add_version(self, instruction: str, examples: List[ExampleRecord], metrics: Dict[str, float] = None) -> None:
        """Add a new version to the job."""
        self.version += 1
        self.instruction = instruction
        self.example_records = examples

        self.version_history.append(self.dict())

    def add_example(self, example_record: ExampleRecord, **kwargs) -> None:
        """Add an example to the job."""
        if input_in_records(self, example_record.input):
            return
        self.example_records.append(example_record)
        self.log_event(Event(
            event_type=EventType.ADD_EXAMPLES,
            example_id=example_record.idx,
            example_version=example_record.version,
            ref_event_id=example_record.gen_event_id,
            **kwargs
        ))

    def _add_example(self, input_example: Union[BaseModel, dict], output_example: Union[BaseModel, dict], **kwargs) -> ExampleRecord:
        """Add an example to the job."""
        input_example = input_example if isinstance(input_example, dict) else input_example.dict()
        output_example = output_example if isinstance(output_example, dict) else output_example.dict()

        if input_in_records(self, input_example):
            raise ValueError(f"Example {input_example} already exists in job {self.idx}!")

        record = ExampleRecord(
            example=Example(input=input_example, output=output_example),
            version=self.version,
            **kwargs
        )

        self.example_records.append(record)
        return record



    # --- version history methods ---

    # TODO: add a flag to rollback method for "hard" or "soft" rollback
    def rollback(self, version: int) -> None:
        """Rollback the job to a previous version."""
        # if version not in self.version_history:
        #     raise ValueError(f"Version {version} not found in version history!")
        #
        # self.version = version
        # self.instruction = self.version_history[version]["instruction"]
        return NotImplemented


# === utils functions === -------------------------------------------------------------------------


def input_in_records(job, input_example: dict) -> bool:
    """Check if an input example is already in the example records."""
    return any(record.input == input_example for record in job.example_records)


def get_record_by_input(job, input_example: dict):
    """Find an example record by its input."""
    return next((record for record in job.example_records if record.input == input_example), None)


def get_template_from_job(job, job_settings: dict = None) -> str:
    """Get a template from a job."""

    job_settings = job_settings or {}

    builder = PromptBuilder(
        instruction=job_settings.get("instruction", job.instruction),
        input_model=job.input_model,
        output_model=job.output_model,
        examples=ExampleSelector.load_examples(job.get_examples(job_settings)),
    )
    return builder.build_template()


def load_engine_from_job(
        job: JobRecord,
        job_settings: dict = None,
        engine_cls: Type[Engine] = None,
        return_metrics: bool = True,
        **kwargs) -> Engine:
    """Load a Engine engine from a job.

    Args:
        job: The job to load the engine from.
        job_settings: The job settings to use for the engine e.g. list of example_ids or different instruction.
        engine_cls (optional): The engine class to use for the engine e.g. AsyncEngine.
    """
    if not engine_cls:
        engine_cls = Engine

    job_settings = job_settings or {}

    return engine_cls.load_engine(
        instruction=job_settings.get("instruction", job.instruction),
        input_model=job.input_model,
        output_model=job.output_model,
        examples=ExampleSelector.load_examples(job.get_examples(job_settings)),
        return_metrics=return_metrics,
        **kwargs
    )
