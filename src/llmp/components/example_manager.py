"""
Manage and store examples for a given job.
"""
import itertools
import random
from pydantic import UUID4

from llmp.integration.example_selector import ExampleManagerSelector
from llmp.components.base import BaseExampleManager
from llmp.components.generator import ExampleGenerator
from llmp.data_model import ExampleRecord, JobRecord
from llmp.data_model.events import Event
from llmp.types import TestSetMode, EventType


# ===============================
# Decisions:
#     - How to store examples and their metrics in the database?
#     - How to match examples with their metrics and their generation event?
#
# Options:
# 1. inhibit generation log event in major vote generator and move to example generator
#     - pro: easier to match examples with their metrics and their generation event
#     - con: generation event is not logged for major vote generator
# 2. manually change generation log event after example generation
#     - pro: generation event is logged for major vote generator
#     - con: more complex to match examples with their metrics and their generation event
# 3. inhibit log event in every sub generator and move it to the outer generator
# 4. Add reference in ADD_EXAMPLES event to the generation event
#     - pro: generation event is logged for major vote generator
#     - con: more complex to match examples with their metrics and their generation event


class ExampleManager(BaseExampleManager):

    def __init__(self, job: JobRecord, debug: bool = False):
        """Initialize the ExampleManager with a job.

        Args:
            job (JobRecord): The job to manage the examples for.
            debug (bool, optional): Enable debug mode. Defaults to False.
        """

        self.job = job
        self.debug = debug

    @property
    def records(self) -> list[ExampleRecord]:
        return self.job.example_records

    def fill_examples(self, total_count: int = 20, **kwargs) -> None:
        """Fill the example records for a given job.

        Args:
            total_count (int, optional): The total number of examples to create. Defaults to 20.
            **kwargs: Additional keyword arguments passed to self.create_examples().
        """
        delta = total_count - len(self.records)
        while delta > 0:
            if self.debug:
                print(f"Creating {delta} examples.")
            self.create_examples(delta, **kwargs)
            delta = total_count - len(self.records)

    def create_examples(self, num_examples: int = 20, **kwargs) -> None:
        """Create a given number of examples for a given job.

        Created examples are added to the job.

        Args:
            num_examples (int, optional): The number of examples to create. Defaults to 20.
            **kwargs: Additional keyword arguments passed to ExampleGenerator.generate().

        Example:
            >>> manager = ExampleManager(job)
            >>> manager.create_examples(20)
        """
        generator = ExampleGenerator(self.job, **kwargs)
        examples = generator.generate(num_examples)
        for example in examples:
            self.job.add_example(example)

    def add_example(self, record: ExampleRecord, **kwargs) -> None:
        """Add an example to the job.

        Args:
            record (ExampleRecord): The example to add.
            **kwargs: Additional keyword arguments passed to self.job.add_example().
        """
        self.job.add_example(record)


    def get_examples(self, job_id: UUID4) -> list[dict]:
        """Return all examples for a given job.

        Args:
            job_id (UUID4): The job id.
        Returns:
            list[dict]: A list of example records.
        """
        pass

    def delete_example(self, job_id: UUID4, example_idx: int) -> None:
        """Delete an example from a given job.

        Args:
            job_id (UUID4): The job id.
            example_idx (int): The example index.
        """
        pass

    def update_example(self, job_id: UUID4, example_idx: int, example: dict) -> None:
        """Update an example for a given job.

        Args:
            job_id (UUID4): The job id.
            example_idx (int): The example index.
            example (dict): The example to update.
        """

        pass

    def to_engine(self, job_id: UUID4) -> list[dict]:
        """Return a list of examples for a given job.

        Args:
            job_id (UUID4): The job id.
        Returns:
            list[dict]: A list of example records.
        """

        return ExampleManagerSelector(examples=self.records)

    def get_test_set(self, test_size: int, mode: str = TestSetMode.RANDOM, exclude_ids: list[str] = None) -> list[ExampleRecord]:
        """Return a test set of examples."""
        if exclude_ids:
            records = [r for r in self.records if r.idx not in exclude_ids]
        else:
            records = self.records


        if mode == TestSetMode.RANDOM:
            return random.sample(records, test_size)

        # get the examples with the lowest accuracy
        elif mode == TestSetMode.ACCURACY:
            return sorted(records, key=lambda x: x.reliability_score)[0:test_size]

    def get_possible_sets(self, set_size: int, exclude_ids: list[str] = None) -> list[tuple[ExampleRecord]]:
        """Return all possible sets of examples.

        Is used in ExampleOptimizer to test all possible combinations of existing examples for a given set_size.

        Args:
            set_size (int): The size of the sets.
            exclude_ids (list[str], optional): A list of example ids to exclude. Defaults to None.

        Returns:
            list[tuple[ExampleRecord]]: A list of example records.

        """
        if exclude_ids:
            records = [r for r in self.records if r.idx not in exclude_ids]
        else:
            records = self.records

        # get all possible combinations sets of size set_size
        return itertools.combinations(records, set_size)
