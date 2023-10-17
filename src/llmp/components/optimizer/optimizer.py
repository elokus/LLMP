"""
Optimization Process:
    1. Create 20 Examples per MajorVoteGenerator
    2. Create an Instruction Test set
    3. Test Instructions

"""
from concurrent.futures import ThreadPoolExecutor, as_completed

from llmp.components.base import BaseOptimizer
from llmp.components.evaluation.engine import EvaluationEngine
from llmp.components.example_manager import ExampleManager
from llmp.data_model import JobRecord, ExampleRecord
from llmp.types import TestSetMode
import llmp.components.optimizer._prompts as prompts
from llmp.integration.structgenie import Engine


class Optimizer(BaseOptimizer):

    MIN_EXAMPLES: int = 20
    TEST_SIZE: int = 5
    PROMPT_SAMPLE_SIZE: int = 3
    SELECT_MODE: str = TestSetMode.ACCURACY
    INSTRUCTION_TEST_SIZE: int = 5
    RUN_PER_SAMPLE: int = 5

    def __init__(self, job: JobRecord, test_set: list[ExampleRecord] = None):
        super().__init__(job)
        self.example_manager = ExampleManager(self.job)
        self.test_set = test_set

    def prepare_job(self):
        # create 20 examples per MajorVoteGenerator
        if len(self.job.example_records) <= self.PROMPT_SAMPLE_SIZE:
            self.example_manager.fill_examples(self.PROMPT_SAMPLE_SIZE)

        if len(self.job.example_records) <= self.MIN_EXAMPLES:
            self.example_manager.fill_examples(self.MIN_EXAMPLES)

        if not self.test_set:
            self.test_set = self.example_manager.get_test_set(self.TEST_SIZE, mode=self.SELECT_MODE)

    def optimize(self, mode: str = "random", metric: str = "accuracy"):
        """Optimize the prompts and examples for a specific job."""
        self.prepare_job()

        # step 2: create an instruction test set
        example_set = self.example_manager.get_test_set(
            self.PROMPT_SAMPLE_SIZE, mode=self.SELECT_MODE, exclude_ids=self.test_set_ids
        )
        instructions = Engine.from_template(prompts.INSTRUCTION_TEMPLATE).run(
            {"example_set": example_set, "num_instructions": self.INSTRUCTION_TEST_SIZE})["instructions"]

        test_settings = [
            {"instruction": instruction, "example_ids": [e.idx for e in example_set]}
            for instruction in instructions
        ]

        result = self.evaluate(test_settings)
        best_index = result.index(max(result, key=lambda x: x[metric]))
        best_setting = test_settings[best_index]

        # step 3: select test cases with the highest failing rate

    def evaluate(self, job_settings: list[dict], num_workers: int = 5, **kwargs):

        unordered_results = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = {
                executor.submit(self._evaluate, idx, job_setting, **kwargs)
                for idx, job_setting in enumerate(job_settings)
            }

            for future in as_completed(futures):
                idx, results = future.result()
                unordered_results.append((idx, results))

        return [results for _, results in sorted(unordered_results, key=lambda x: x[0])]

    def _evaluate(self, idx: int, job_setting: dict, **kwargs):
        evaluator = EvaluationEngine(self.job, self.RUN_PER_SAMPLE)
        return idx, evaluator.evaluate(self.test_set, job_setting)

    @property
    def test_set_ids(self):
        return [r.idx.hex for r in self.test_set]
