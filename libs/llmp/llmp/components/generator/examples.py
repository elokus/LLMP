# Should update the job with every new example to increase validation accuracy?
#
# Option 1: Updating the job with every new example
#     Pros: Higher validation accuracy
#     Cons: More expensive to update the job with every new example in regard to token usage
# Option 2: Create new examples and return them without updating the job
#     Pros: Less expensive to create new examples. Single Responsibility Principle for the generator.
#     Cons: Lower validation accuracy
#
# Currently using option 2. We might create a second generator that uses option 1.
#
# TODO: add a decision module to decide if output generation should be performed with MajorVote or MajorVoteGrading.
#
# MajorVoteGradingGenerator is currently not used. When generating examples with definite outputs
# MajorVoteGenerator should be preferred. MajorVoteGradingGenerator should be used when generating examples with
# indefinite outputs. For example, when generating examples for a
# prompt like "Write a short story about a dog." the output is indefinite.
# In this case, MajorVoteGradingGenerator should be used.
# This implementation should be added in the future most likely on OutputModel level or on Job level.

from typing import Union
from llmp.integration.structgenie import Engine

from llmp.components.base import BaseGenerator
from llmp.components.generator._prompts import EXTEND_INPUTS_TEMPLATE
from llmp.types import VerificationType
from llmp.components.generator.consensus import MajorVoteGenerator
from llmp.data_model import ExampleRecord, JobRecord
from llmp.integration.structgenie import OutputModel
from structgenie.engine import StructEngine


class ExampleGenerator(BaseGenerator):
    """A Generator dedicated to generating examples for a given job.

    This generator is used to generate examples for a given job with a predefined Prompt template.
    Under the hood, it uses a MajorVoteGenerator to generate the examples.
    """

    TEMPLATE: str = EXTEND_INPUTS_TEMPLATE

    def __init__(
            self,
            job: JobRecord,
            job_settings: dict = None,
            num_votes: int = 5,
            mode: VerificationType = VerificationType.MAJORITY_VOTE,
            debug: bool = False,
            raise_errors: bool = False,
            **kwargs
    ):
        """
        Initialize the generator with a job and job settings.

        Args:
            job (JobRecord): The job to be executed.
            job_settings (dict): The job settings to be used.
            num_votes (int): Number of votes to be collected for the MajorVoteGenerator.
            mode (VerificationType): The verification type to be used (majority vote, majority grade, human verified).
            debug (bool): If True, debug information will be printed.
            raise_errors (bool): If True, errors will be raised.
            **kwargs: Additional keyword arguments passed to MajorVoteGenerator.
        """

        super().__init__(job, job_settings)
        self.output_generator = MajorVoteGenerator(
            job, job_settings, num_votes, mode, return_event_log=True, raise_errors=raise_errors, debug=debug, **kwargs
        )
        self.input_generator = self._load_engine(job, debug=debug, raise_errors=raise_errors, **kwargs)
        self.run_metrics = {}

    def generate(
            self,
            num_items, **kwargs) -> list[Union[ExampleRecord, dict]]:
        """
        Generate examples for a given job.

        This method generates inputs with a template and then generates outputs with a MajorVoteGenerator.

        Args:
            num_items (int): Number of examples to be generated.
            **kwargs: Additional keyword arguments passed to MajorVoteGenerator.generate() method.

        Returns:
            list[Union[ExampleRecord, dict]]: List of generated examples.
        """
        input_list = self._generate_inputs(num_items, **kwargs)
        return self._generate_outputs(input_list, **kwargs)

    def _generate_outputs(self, input_list: list[dict], **kwargs) -> list[ExampleRecord]:
        """
        Generate outputs for the given inputs.

        Args:
            input_list (list[dict]): List of input objects.
            **kwargs: Additional keyword arguments passed to MajorVoteGenerator.generate() method.

        Returns:
            list[ExampleRecord]: List of ExampleRecord objects.
        """
        examples = []
        for input_object in input_list:
            output, event = self.output_generator.generate(input_object, **kwargs)
            record = ExampleRecord.from_input_output(
                input_obj=input_object,
                output_obj=output,
                version=1,
                gen_event_id=event.event_id,
                verification_type=event.event_metrics.get("verification_type", None),
                reliability=event.event_metrics.get("reliability", 1.0),
            )
            examples.append(record)
        return examples

    def _generate_inputs(self, num_items: int = 20, **kwargs) -> list[dict]:
        """
        Generate inputs for the examples.

        Args:
            num_items (int): Number of inputs to be generated.
            **kwargs: Additional keyword arguments passed to the input generator.

        Returns:
            list[dict]: List of input objects.
        """
        input_dict = {
            "instruction": self._job_settings.get("instruction", None) or self.job.instruction,
            "num_examples": num_items,
            "input_example": [example.example.input for example in self.job.example_records],
        }
        output, _ = self.input_generator.run(input_dict, **kwargs)
        return output["outputs"]

    @property
    def verification_type(self):
        """
        Return the validation type for the generator.

        Returns:
            None: This method should be overridden in subclasses.
        """
        return None

    def _load_engine(self, job: JobRecord, **kwargs) -> "StructEngine":
        """
        Load the engine for the generator.

        Initializes the engine with the prompt template and parse the input model as partial_output_model.

        Args:
            job (JobRecord): The job to be executed.
            **kwargs: Additional keyword arguments passed to the engine.

        Returns:
            StructEngine: The engine for the generator.
        """
        input_model = OutputModel(**job.input_model.dict())
        return Engine.from_template(
            self.TEMPLATE, partial_output_model={"outputs": input_model}, **kwargs
        )
