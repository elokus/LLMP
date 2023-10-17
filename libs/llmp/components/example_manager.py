"""
Manage and store examples for a given job.
===============================
Decisions:
    - How to store examples and their metrics in the database?
    - How to match examples with their metrics and their generation event?

Options:
1. inhibit generation log event in major vote generator and move to example generator
    - pro: easier to match examples with their metrics and their generation event
    - con: generation event is not logged for major vote generator
2. manually change generation log event after example generation
    - pro: generation event is logged for major vote generator
    - con: more complex to match examples with their metrics and their generation event
3. inhibit log event in every sub generator and move it to the outer generator
4. Add reference in ADD_EXAMPLES event to the generation event
    - pro: generation event is logged for major vote generator
    - con: more complex to match examples with their metrics and their generation event
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


class ExampleManager(BaseExampleManager):

    def __init__(self, job: JobRecord, debug: bool = False):
        self.job = job
        self.debug = debug

    @property
    def records(self) -> list[ExampleRecord]:
        return self.job.example_records

    def fill_examples(self, total_count: int = 20, **kwargs) -> None:
        delta = total_count - len(self.records)
        while delta > 0:
            if self.debug:
                print(f"Creating {delta} examples.")
            self.create_examples(delta, **kwargs)
            delta = total_count - len(self.records)

    def create_examples(self, num_examples: int = 20, **kwargs) -> None:
        generator = ExampleGenerator(self.job, **kwargs)
        examples = generator.generate(num_examples)
        for example in examples:
            self.job.add_example(example)

    def add_example(self, record: ExampleRecord, **kwargs) -> None:
        self.job.add_example(record)


    def get_examples(self, job_id: UUID4) -> list[dict]:
        pass

    def delete_example(self, job_id: UUID4, example_idx: int) -> None:
        pass

    def update_example(self, job_id: UUID4, example_idx: int, example: dict) -> None:
        pass

    def to_engine(self, job_id: UUID4) -> list[dict]:
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

    def get_possible_sets(self, set_size: int, exclude_ids: list[str] = None):
        if exclude_ids:
            records = [r for r in self.records if r.idx not in exclude_ids]
        else:
            records = self.records

        # get all possible combinations sets of size set_size
        return itertools.combinations(records, set_size)
