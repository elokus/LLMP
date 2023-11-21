"""Consensus generators.

Generators that execute a job multiple times and return the majority vote/majority grade output.
Is used in evaluation and verification tasks."""

from typing import Union, Tuple

from llmp.components.base import BaseGenerator
from llmp.components.generator import AsyncGenerator
import llmp.components.generator.verification as verify
from llmp.data_model import JobRecord
from llmp.data_model.events import Event
from llmp.types import VerificationType


class MajorVoteGenerator(BaseGenerator):
    """Execute a job with a specific input multiple times and return the majority vote output."""

    def __init__(
            self,
            job: JobRecord,
            job_settings: dict = None,
            num_votes: int = 10,
            mode: VerificationType = VerificationType.MAJORITY_VOTE,
            return_event_log: bool = False,
            **kwargs
    ):
        """Initialize the generator with a job and job settings.

        Args:
            job: JobRecord - the job to be executed
            job_settings: dict  - the job settings to be used
            num_votes: int  - number of votes to be collected
            mode: VerificationType  - the verification type to be used (majority vote, majority grade, human verified)
            return_event_log: bool  - whether to return the event log
            **kwargs: any -  passed to AsyncGenerator

        Examples:
            >>> from llmp.components.generator import MajorVoteGenerator
            >>> from llmp.data_model import JobRecord
            >>> from llmp.data_model.job_record import load_job_from_file

        """
        super().__init__(job, job_settings, **kwargs)
        self.generator = AsyncGenerator(self.job, self._job_settings, num_votes, **kwargs)
        self._mode = mode
        self._return_event_log = return_event_log

    def generate(self, inputs: dict, **kwargs) -> Union[dict, Tuple[dict, Event]]:
        """Generate an output from input data

        Runs an AsyncGenerator with a specific input multiple times and returns the majority vote output.

        Args:
            inputs (dict): Input data for the job. With prompt placeholder as keys
            **kwargs:

        Returns:
            Union[dict, Tuple[dict, Event]]

        """

        outputs = self.generator.generate(inputs, **kwargs)
        # select best output
        if self._mode == VerificationType.MAJORITY_VOTE:
            output, run_metric = verify.get_majority_vote(outputs, job=self.job)

        elif self._mode == VerificationType.MAJORITY_GRADE:
            output, run_metric = verify.get_majority_grade(outputs, job=self.job)

        elif self._mode == VerificationType.HUMAN_VERIFIED:
            output, run_metric = verify.get_human_vote(outputs)
            run_metric["reliability"] = 1.0

        else:
            raise ValueError(f"Validation type {self._mode} not supported.")

        event = self.log_generation(inputs, output, run_metric)

        if self._return_event_log:
            return output, event
        return output

    @property
    def verification_type(self):
        return self._mode
