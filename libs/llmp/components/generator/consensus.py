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
        super().__init__(job, job_settings, **kwargs)
        self.generator = AsyncGenerator(self.job, self._job_settings, num_votes, **kwargs)
        self._mode = mode
        self._return_event_log = return_event_log

    def generate(self, inputs: dict, **kwargs) -> Union[dict, Tuple[dict, Event]]:

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
