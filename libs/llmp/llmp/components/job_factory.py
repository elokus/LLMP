from abc import ABC, abstractmethod
from typing import Union, Type

from structgenie.pydantic_v1 import BaseModel

from llmp.data_model import JobRecord, ExampleRecord
from llmp.types import VerificationType
from llmp.integration.structgenie import (
    Example,
    OutputModel,
    InputModel,
    extract_sections,
)


class JobCreator(ABC):
    """
    Abstract class for creating jobs.
    """

    @abstractmethod
    def create_job(self, *args, **kwargs) -> JobRecord:
        """Create a new job."""
        pass
    
    def _create_job(
            self,
            job_name: str,
            instruction: str,
            input_model: InputModel,
            output_model: OutputModel,
            example_pairs: list[Example],
            config: dict = None,
            **kwargs) -> JobRecord:
        
        job = JobRecord(
            job_name=job_name,
            input_model=input_model,
            output_model=output_model,
            instruction=instruction,
            config=config,
            **kwargs
        )
        if example_pairs:
            job = self._add_examples(job, example_pairs)
        
        return job
    
    @staticmethod
    def _add_examples(job: JobRecord, example_pairs: list[Example]):
        """Add examples to a job."""
        for example in example_pairs:
            job.add_example(ExampleRecord(
                example=example,
                gen_event_id="genesis",
                verification_type=VerificationType.HUMAN_VERIFIED,
                data_type="real"
            ))

        return job
        

class ModelJobCreator(JobCreator):
    """
    Class for creating zero-shot jobs.
    """
    def create_job(
            self,
            job_name,
            instruction: str = None,
            input_model: Type[BaseModel] = None,
            output_model: Type[BaseModel] = None,
            example_pairs: list[Example] = None,
            config: dict = None,
            **kwargs) -> JobRecord:
        """Create a new zero-shot job."""
        input_model = InputModel.from_pydantic(input_model)
        output_model = OutputModel.from_pydantic(output_model)
        
        return self._create_job(
            job_name=job_name,
            input_model=input_model,
            output_model=output_model,
            instruction=instruction,
            config=config,
            example_pairs=example_pairs,
            **kwargs
        )


class ExampleJobCreator(JobCreator):
    """
    Class for creating example jobs.
    """

    def create_job(
            self,
            job_name,
            instruction: str = None,
            example_pairs: list[Example] = None,
            config: dict = None,
            **kwargs) -> JobRecord:
        """Create a new example job."""
        # load input and output model from examples
        input_model = InputModel.from_examples(example_pairs)
        output_model = OutputModel.from_examples(example_pairs)
        
        return self._create_job(
            job_name=job_name,
            input_model=input_model,
            output_model=output_model,
            instruction=instruction,
            config=config,
            example_pairs=example_pairs,
            **kwargs
        )


class TemplateJobCreator(JobCreator):
    """
    Class for creating template jobs.
    """

    def create_job(
            self,
            job_name,
            instruction: str = None,
            input_template: str = None,
            output_template: str = None,
            example_pairs: list[Example] = None,
            config: dict = None,
            **kwargs
    ) -> JobRecord:
        """Create a new job from string template.

        Example:
            '''
            # Instruction
            ...
            # Input
            Book: {book}
            # Output
            Genre: <str, options=['Fiction', 'Non-Fiction']>
            '''

        """
        input_model = InputModel.from_string(input_template)
        output_model = OutputModel.from_string(output_template)

        return self._create_job(
            job_name=job_name,
            input_model=input_model,
            output_model=output_model,
            instruction=instruction,
            config=config,
            example_pairs=example_pairs,
        )


def job_factory(
        job_name: str,
        instruction: str = None,
        input_model: Type[BaseModel] = None,
        output_model: Type[BaseModel] = None,
        input_examples: Union[dict, list[dict]] = None,
        output_examples:  Union[dict, list[dict]] = None,
        example_pairs: list[tuple[dict], Example, dict] = None,
        prompt_template: str = None,
        input_template: str = None,
        output_template: str = None,
        config: dict = None,
        **kwargs) -> JobRecord:
    """
    
    Args:
        job_name (str): The job_name name or id of the job.
        instruction (str): The instruction for the job.
        input_model (Type[BaseModel]): The input model for the job.
        output_model (Type[BaseModel]): The output model for the job.
        input_examples (Union[dict, list[dict]]): The input examples for the job.
        output_examples (Union[dict, list[dict]]): The output examples for the job.
        example_pairs (list[tuple[dict], Example, dict]): The example pairs for the job.
        prompt_template (str): The prompt template for the job.
        input_template (str): The input template for the job.
        output_template (str): The output template for the job.
        config (dict): The config for the job.
    """

    # prepare examples
    assert not ((input_examples or output_examples) and example_pairs), "Cannot use input_examples/output_examples and example_pairs at the same time."

    if input_examples and output_examples:
        input_examples = input_examples if isinstance(input_examples, list) else [input_examples]
        output_examples = output_examples if isinstance(output_examples, list) else [output_examples]
        example_pairs = list(zip(input_examples, output_examples))
        
    if example_pairs:
        if isinstance(example_pairs[0], tuple):
            example_pairs = [Example(input=inp, output=out) for inp, out in example_pairs]
        elif isinstance(example_pairs[0], dict):
            example_pairs = [Example.from_dict(**example) for example in example_pairs]

    # create from string template
    assert not (prompt_template and (input_template or output_template)), "Cannot use prompt_template and input_template/output_template at the same time."
    assert not (input_template and not output_template), "Cannot use input_template without output_template."
    assert not (output_template and not input_template), "Cannot use output_template without input_template."
    
    if prompt_template:
        sections = extract_sections(prompt_template)
        instruction = sections.get("instruction") or instruction
        input_template = sections.get("input_schema")
        output_template = sections.get("output_schema")
    
    if input_template and output_template:
        return TemplateJobCreator().create_job(
            job_name,
            instruction=instruction,
            input_template=input_template,
            output_template=output_template,
            example_pairs=example_pairs,
            config=config,
            **kwargs
        )
    
    # create from input/output model
    if input_model and output_model:
        return ModelJobCreator().create_job(
            job_name,
            instruction=instruction,
            input_model=input_model,
            output_model=output_model,
            example_pairs=example_pairs,
            config=config,
            **kwargs
        )
    
    if example_pairs:
        return ExampleJobCreator().create_job(
            job_name,
            instruction=instruction,
            example_pairs=example_pairs,
            config=config,
            **kwargs
        )
        
    raise ValueError("Invalid Arguments for job creation.")
