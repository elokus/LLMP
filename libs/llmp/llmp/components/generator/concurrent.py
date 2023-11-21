"""
Concurrent Generators
=====================
- Generators that run one job/prompt multiple times asynchronous.
- Generators that run multiple jobs/prompts in multi threading.

Used in evaluation of prompt variants and optimization of prompts.
Basically, we want to create multiple variants of a prompt and run them in multiple threads, where each thread will run
the same prompt multiple times.
"""
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

import nest_asyncio
from typing import Tuple, Union

from llmp.components.base import BaseGenerator
from llmp.data_model import JobRecord
from llmp.data_model.job_record import load_engine_from_job
from llmp.utils.helper import flatten
from llmp.integration.structgenie import AsyncEngine
from llmp.types import GenOutput


# We need to decide how to handle prompt variants. Should we create a new job for each prompt variant?
# The preferred logic will be to pass a single job and a list of settings for the prompt variants.
# This settings should include an instruction and a list of example ids that will be used for the generation.


class AsyncGenerator(BaseGenerator):
    """Generates a job multiple times asynchronous.

    Methods:
        generate: generate an output based on the job + job_setting and input data.
        run_engines (async): run the engines in parallel with identical job setup. This is an async method so it can be used with asyncio.gather()
    """

    def __init__(self, job: JobRecord, job_settings: dict = None, num_runs: int = 5, **kwargs):
        """Initialize the generator with a job and job settings.

        Args:
            job: JobRecord
            job_settings: dict
            num_runs: int
        """
        super().__init__(job, job_settings, **kwargs)
        self._num_runs = num_runs

    def generate(self, input_data: Union[dict, list[dict]], **kwargs) -> list[GenOutput]:
        """Generate an output based on the job + job_setting and input data."""
        nest_asyncio.apply()
        results = asyncio.run(self.run_engines(input_data, **kwargs))
        return results

    async def run_engines(self, input_data: Union[dict, list[dict]], **kwargs) -> list[GenOutput]:
        """Run the engines in parallel with identical job setup.

        Return a list of Tuple[output, run_metrics] for each run.
        """

        num_runs = self._num_runs if isinstance(input_data, dict) else len(input_data)

        engines = [
            load_engine_from_job(self.job, self._job_settings, engine_cls=AsyncEngine, **self._engine_kwargs)
            for _ in range(num_runs)
        ]

        # single input
        if isinstance(input_data, dict):
            results = await asyncio.gather(*[engine.run(input_data, **kwargs) for engine in engines])

        # multiple inputs
        elif isinstance(input_data, list):
            results = await asyncio.gather(
                *[engine.run(input_data_, **kwargs) for engine, input_data_ in zip(engines, input_data)]
            )

        else:
            raise ValueError(f"Input data type {type(input_data)} not supported!")

        return [result for result in results if result is not None]

    @property
    def verification_type(self):
        return None


class SequentialAsyncGenerator(BaseGenerator):
    """Execute a generation job within one thread multiple times for multiple Inputs in Sequence."""
    def __init__(self, job: JobRecord, job_settings: dict = None, num_runs: int = 5):
        super().__init__(job)
        self.generator = AsyncGenerator(job, job_settings, num_runs)

    def generate(self, input_data: list[dict], **kwargs) -> list[list[GenOutput]]:
        output_metrics = []
        for input_ in input_data:
            output_metrics.append(self.generator.generate(input_, **kwargs))

        return output_metrics

    @property
    def verification_type(self):
        return None


# TODO: Add RateLimitHandler
class SequentialAsyncGenerator2(BaseGenerator):
    """A faster version of SequentialAsyncGenerator.

    Runs all inputs in parallel but is prone to RateLimitingErrors.
    """
    def __init__(self, job: JobRecord, job_settings: dict = None, num_runs: int = 5):
        super().__init__(job)
        self.generator = AsyncGenerator(job, job_settings, num_runs)

    def generate(self, input_data: list[dict], **kwargs) -> list[list[GenOutput]]:
        nest_asyncio.apply()
        return asyncio.run(self._generate(input_data, **kwargs))

    async def _generate(self, input_data: list[dict], **kwargs) -> list[list[GenOutput]]:
        output_metrics = await asyncio.gather(*[self.generator.run_engines(input_, **kwargs) for input_ in input_data])
        return [m for m in output_metrics if m is not None]

    @property
    def verification_type(self):
        return None


class MultiThreadingAsyncGenerator(BaseGenerator):
    """Run SequentialAsyncGenerator in multiple threads.

    For each thread, a SequentialAsyncGenerator is created with different job settings and runs
    for each sample from input_data for "num_runs" times.
    """
    def __init__(self, job: JobRecord, job_settings: list[dict], num_runs: int = 5):
        super().__init__(job)
        self._job_settings = job_settings
        self._num_runs = num_runs
        self.num_threads = len(job_settings)

    def generate(self, input_data: list[dict], **kwargs) -> list[list[GenOutput]]:

        unordered_results = []

        with ThreadPoolExecutor(max_workers=self.num_threads) as executor:
            futures = {
                executor.submit(self._generate, idx, job_setting, input_data, **kwargs)
                for idx, job_setting in enumerate(self._job_settings)
            }

            for future in as_completed(futures):
                idx, results = future.result()
                unordered_results.append((idx, results))

        return [results for _, results in sorted(unordered_results, key=lambda x: x[0])]

    def _generate(self, idx: int, job_setting: dict, input_data: list[dict], **kwargs):
        generator = SequentialAsyncGenerator(self.job, job_setting, self._num_runs)
        return idx, generator.generate(input_data, **kwargs)

    @property
    def verification_type(self):
        return None
