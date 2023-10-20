from typing import Dict, Any

from llmp.components.job_factory import job_factory
from llmp.components.instruction.generation import InstructionGenerator
from llmp.data_model.events import Event
from llmp.services.job_storage import JobStorage
from llmp.components.generator import Generator
from llmp.data_model import JobRecord, ExampleRecord
from llmp.types import EventType


def load_generator_cls(generator_type: str):
    """Load a generator class by type."""
    if generator_type == "default":
        return Generator
    elif generator_type == "consensus":
        raise NotImplementedError
    elif generator_type == "async":
        raise NotImplementedError
    else:
        raise ValueError(f"Generator type '{generator_type}' not supported.")


class JobManager:
    def __init__(self, config: dict):
        self.job_storage = JobStorage(config.get("base_path"))

    def create_job(
            self,
            job_name: str,
            **kwargs) -> JobRecord:
        """Create a new job.

        Generate a new job with the provided signature and kwargs.
        If not provided, the instruction will be generated automatically.
        """
        job = job_factory(
            job_name=job_name,
            **kwargs)

        # register job_name
        _job_name = self.job_storage.register_job(job_name, job.idx)
        if job_name != _job_name:
            job.job_name = _job_name
            print(f"Job name '{job_name}' already exists. Using '{_job_name}' instead.")

        # log creation event
        job.log_event(Event(
            event_type=EventType.JOB_CREATION,
            job_setting=dict(instruction=job.instruction, example_id=[example.idx for example in job.example_records]),
            job_version=job.version,
        ))

        # generate instruction
        if not job.instruction:
            job.instruction = self.generate_instruction(job, **kwargs)
            self.job_storage.update_job(job)

        return job

    def get_job(self, signature: str) -> JobRecord:
        """Retrieve details for a specific job."""
        return self.job_storage.get_job(signature)

    def update_job(self, job: JobRecord):
        """Update details of a specific job."""
        return self.job_storage.update_job(job)

    def delete_job(self, signature: str):
        """Delete a specific job."""
        return self.job_storage.delete_job(signature)

    def optimize_job(self, *args, **kwargs):
        """Run the optimization process for a job, including generating examples and refining instructions."""
        pass

    # TODO: make self.job_storage.store_logs() multi-threaded
    def generate_output(self, job: JobRecord, input_data: dict, generator_type: str = "default", **kwargs):
        """Generate output for a specific input."""
        generator = load_generator_cls(generator_type=generator_type)(job, **kwargs)
        result, run_metrics = generator.generate(input_data, **kwargs)
        event_metric = {
            "verification_type": generator.verification_type,
            **run_metrics,
            **kwargs
        }
        job.log_generation(input_data, result, event_metric)
        self.job_storage.store_logs(job)
        return result


    def generate_instruction(self, job: JobRecord, **kwargs) -> str:
        """Generate an instruction for a specific job."""
        generator = InstructionGenerator(job, **kwargs)
        return generator.run()

    def generate_examples_for_job(self, job_id: str, target_count: int):
        """Generate additional examples for a specific job."""
        pass

    def evaluate_job_performance(self, job_id: str) -> Dict[str, float]:
        """Evaluate the performance metrics for a specific job."""
        pass

    def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """Retrieve metrics for a specific job."""
        pass

    def human_verify_example(self, example: ExampleRecord) -> bool:
        """Submit an example for human verification and get the result."""
        pass

    def log_action(self, action: str, job_id: str):
        """Log a specific action related to a job."""
        pass

    # # === Private methods ===
    #
    # def _create_job(
    #         self,
    #         signature: str,
    #         instruction: str,
    #         input_examples: Union[BaseModel, list[BaseModel]],
    #         output_examples: Union[BaseModel, list[BaseModel]],
    #         verification_type: int = VerificationType.HUMAN_VERIFIED,
    #         reliability: float = 1.0,
    #         **kwargs
    # ) -> JobRecord:
    #     input_examples = input_examples if isinstance(input_examples, list) else [input_examples]
    #     output_examples = output_examples if isinstance(output_examples, list) else [output_examples]
    #     input_model = InputModel.from_pydantic(type(input_examples[0]))
    #     output_model = OutputModel.from_pydantic(type(output_examples[0]))
    #     new_job = JobRecord(
    #         job_name=signature,
    #         input_model=input_model,
    #         output_model=output_model,
    #         instruction=instruction,
    #         **kwargs
    #     )
    #
    #     for input_example, output_example in zip(input_examples, output_examples):
    #         new_job.add_example(ExampleRecord.from_input_output(
    #             input_example, output_example, verification_type=verification_type, reliability=reliability
    #         ))
    #
    #     # log creation event
    #     new_job.log_event(Event(
    #         event_type=EventType.JOB_CREATION,
    #         job_setting=dict(instruction=instruction, example_id=[example.idx for example in new_job.example_records]),
    #         job_version=new_job.version,
    #     ))
    #     # register job_name
    #     _job_name = self._register_job_name(signature, new_job.idx)
    #     if signature != _job_name:
    #         new_job.job_name = _job_name
    #         print(f"Job name '{signature}' already exists. Using '{_job_name}' instead.")
    #
    #     # save job
    #     self._save_job(new_job)
    #     return new_job
