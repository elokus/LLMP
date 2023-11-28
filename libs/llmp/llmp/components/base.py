from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Optional, Any, Union

from pydantic import UUID4
from tqdm import tqdm

from llmp.data_model.events import Event
from llmp.data_model import ExampleRecord, JobRecord


class BaseExampleManager(ABC):

    @abstractmethod
    def add_example(self, job_id: UUID4, example: dict) -> None:
        pass

    @abstractmethod
    def get_examples(self, job_id: UUID4) -> List[dict]:
        pass

    @abstractmethod
    def delete_example(self, job_id: UUID4, example_idx: int) -> None:
        pass

    @abstractmethod
    def update_example(self, job_id: UUID4, example_idx: int, example: dict) -> None:
        pass


class BaseOptimizer(ABC):
    def __init__(self, job: JobRecord, debug: bool = False, display_progress: bool = True):
        self.job = job
        self.debug = debug
        self.display_progress = display_progress
        self.progress_bar_config = {
            "dynamic_ncols": True
        }

    @abstractmethod
    def optimize(self, mode: str = "all"):
        """Optimize the prompts and examples for a specific job."""
        pass

    def get_progress_bar(
            self, length: int, description: str, sub: bool = False, desc_length: int = 40, leave: bool = True
    ):
        if sub:
            description = "  > " + description

        if (d := desc_length - len(description)) > 0:
            description += " " * d

        return tqdm(
            total=length,
            desc=description,
            disable=not self.display_progress,
            leave=leave,
            position=0 if not sub else 1,
            **self.progress_bar_config
        )


class BaseGenerator(ABC):
    """Base class for the Generator component.

    A Generator is a wrapper for executing job-specific completion with a job specific input object.
    """


    def __init__(self, job: JobRecord, job_settings: dict = None, **kwargs):
        """Initialize the generator with a job and job settings.

        Args:
            job (JobRecord): the job to be executed
            job_settings (dict): the job settings to be used
            **kwargs: any -  passed to load_engine_from_job

        """

        self.job = job
        self._debug = kwargs.get("debug", False)
        self._job_settings = job_settings or {}
        self._report_generation = kwargs.get("report_generation", True)
        self._engine_kwargs = kwargs

    def log_generation(
            self, input_object: dict, generated_object: dict, run_metrics: dict, **kwargs
    ) -> Union[Event, None]:
        """Log the generation result.

        Args:
            input_object (dict): the input object
            generated_object (dict): the generated object
            run_metrics (dict): the run metrics
            **kwargs: any -  passed to JobRecord.log_generation
        """
        if not self.verification_type or not self._report_generation:
            return None

        event_metric = {
            "verification_type": self.verification_type,
            **run_metrics,
            **kwargs
        }
        return self.job.log_generation(input_object, generated_object, event_metric)

    @abstractmethod
    def generate(self, input_object: dict, **kwargs):
        """Generate text based on the job and input object."""
        pass

    @property
    @abstractmethod
    def verification_type(self):
        """Return the validation type for the generator."""
        pass


class BaseInstructionHandler(ABC):
    def __init__(self, job: JobRecord, debug: bool = False, **kwargs):
        self.job = job
        self.debug = debug
        self.raise_errors = kwargs.get("raise_errors", False)

    def generate(self, *args, **kwargs):
        """Generate text based on the job and input object."""
        pass



class BaseEvaluationEngine(ABC):
    """
    Abstract base class for the EvaluationEngine.
    Provides an interface for evaluating generation results and computing metrics.
    """

    def __init__(self, job: JobRecord):
        self.job = job

    @abstractmethod
    def evaluate(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Evaluate the generation result against the desired output and compute metrics.

        Returns:
            Dict[str, Any]: A dictionary containing the computed metrics.
        """
        pass

    @abstractmethod
    def compute_metrics(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Compute and aggregate metrics based on the run metrics and the evaluation results.

        Returns:
            Dict[str, Any]: A dictionary containing the aggregated metrics.
        """
        pass


class BaseHumanVerification(ABC):

    @abstractmethod
    def verify(self, job_id, generated_example):
        """Manually verify a generated example for a specific job."""
        pass