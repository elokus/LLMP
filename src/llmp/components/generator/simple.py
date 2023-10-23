"""Simple Generator module that can be used to perform generation tasks for a given job and input object."""


# This module is used to perform generation tasks for a given job and input object. Next implementation should add
# tracing and logging to the generation process. Generation tasks should log new input objects and their corresponding
# outputs. This can be used to create a dataset of input objects and their corresponding outputs. This dataset can be used
# to extend the example library of a job.
#
# TODO: Add tracing and logging to the generation process.

from typing import Tuple

from llmp.components.base import BaseGenerator
from llmp.data_model.job_record import load_engine_from_job
from llmp.types import VerificationType


class Generator(BaseGenerator):
    """Basic generator that runs a job once.

    This generator is used to run a job once and return the parsed output according job's output_model.
    """

    def generate(self, input_data: dict, **kwargs) -> Tuple[dict, dict]:
        """Generate an output based on the job and input data.

        loads the engine from the job and runs it with the input data.

        Args:
            input_data (dict): Input data for the job. With prompt placeholder as keys
            **kwargs: any -  passed to engine.run() method
        """

        engine = load_engine_from_job(self.job, self._job_settings, **self._engine_kwargs)
        output, run_metrics = engine.run(input_data, **kwargs)
        return output, run_metrics

    @property
    def verification_type(self):
        """Return the validation type for the generator.

        Used in event log.
        """
        return VerificationType.SINGLE_VOTE
