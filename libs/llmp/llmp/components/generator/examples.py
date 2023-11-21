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
            **kwargs
    ):
        """Initialize the generator with a job and job settings.

        Args:
            job (JobRecord): the job to be executed
            job_settings (dict): the job settings to be used
            num_votes (int): number of votes to be collected
            mode (VerificationType): the verification type to be used (majority vote, majority grade, human verified)
            **kwargs: any -  passed to MajorVoteGenerator
        """

        super().__init__(job, job_settings)
        self.generator = MajorVoteGenerator(job, job_settings, num_votes, mode, return_event_log=True, **kwargs)

    def generate(self, num_items, **kwargs) -> list[Union[ExampleRecord, dict]]:
        """Generate examples for a given job.

        1. Generate inputs with a template
        2. Generate outputs with a MajorVoteGenerator

        Args:
            num_items (int): number of examples to be generated
            **kwargs: any -  passed to MajorVoteGenerator.generate() method

        Returns:
            list[Union[ExampleRecord, dict]]: list of generated examples
        """
        input_list = self._generate_inputs(num_items)
        return self._generate_outputs(input_list)

    def _generate_outputs(self, input_list: list[dict]) -> list[ExampleRecord]:
        examples = []
        for input_object in input_list:
            output, event = self.generator.generate(input_object)
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

    def _generate_inputs(self, num_items: int = 20) -> list[dict]:
        input_model = OutputModel(**self.job.input_model.dict())
        engine = Engine.from_template(
            self.TEMPLATE, partial_output_model={"outputs": input_model}, debug=self._debug
        )  # type: ignore

        input_dict = {
            "instruction": self._job_settings.get("instruction", None) or self.job.instruction,
            "num_examples": num_items,
            "input_example": [example.example.input for example in self.job.example_records],
        }
        output = engine.run(input_dict)
        return output["outputs"]

    @property
    def verification_type(self):
        return None
