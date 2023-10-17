"""Optimization Process:
    1. Create 20 Examples per MajorVoteGenerator
    2. Create an Instruction Test set
    3. Test different Example sets

============================

Example Selection OPTIONS:
    1. Select Examples with the highest failing rate
    2. Select Examples with the highest failing rate and lowest accuracy
    3. Select random Examples
    4. Step by step selection of Examples

Preferred Option: 4 first test best two examples, then add one example at a time and test again.
When testing from 15 Examples all combinations of 2 we will get a total of 105 combinations.
Instead of testing from 15 Examples all combinations of 3 we will get a total of 455 combinations.
After defining best two examples we can test with additional 13 test runs to get a total of 118 test runs for three examples.

Alternatively we can try to find the best One Shot Example. This would end up in the smallest number of test runs,
but we would miss eventually better example combinations.

"""
import tqdm


from concurrent.futures import ThreadPoolExecutor, as_completed

from llmp.components.base import BaseOptimizer
from llmp.components.evaluation.engine import EvaluationEngine
from llmp.components.example_manager import ExampleManager
from llmp.data_model import JobRecord, ExampleRecord
from llmp.types import TestSetMode
import llmp.components.optimizer._prompts as prompts
from llmp.integration.structgenie import Engine


class InstructionOptimizer(BaseOptimizer):

    MIN_EXAMPLES: int = 20
    TEST_SIZE: int = 5
    PROMPT_SAMPLE_SIZE: int = 3
    SELECT_MODE: str = TestSetMode.ACCURACY
    INSTRUCTION_TEST_SIZE: int = 5
    RUN_PER_SAMPLE: int = 5

    def __init__(
            self,
            job: JobRecord,
            test_set: list[ExampleRecord] = None,
            display_progress: bool = True,
            debug: bool = False, **kwargs):
        super().__init__(job, debug, display_progress)
        self.example_manager = ExampleManager(self.job, debug=self.debug)
        self.test_set = test_set

    def prepare_job(self):
        # create 20 examples per MajorVoteGenerator
        if len(self.job.example_records) <= self.PROMPT_SAMPLE_SIZE:
            print(f">>> Filling examples to {self.PROMPT_SAMPLE_SIZE} examples.")
            self.example_manager.fill_examples(self.PROMPT_SAMPLE_SIZE)

        if len(self.job.example_records) <= self.MIN_EXAMPLES:
            print(f">>> Filling examples to {self.MIN_EXAMPLES} examples.")
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
        print(">>> Generating Instructions")
        instructions = Engine.from_template(prompts.INSTRUCTION_TEMPLATE).run(
            {"example_set": self.examples_to_prompt(example_set), "num_instructions": self.INSTRUCTION_TEST_SIZE})["instructions"]

        if self.debug:
            print("Instructions:")
            for i, instruction in enumerate(instructions):
                print(i, instruction)
                print("\n")


        test_settings = [
            {"instruction": instruction, "example_ids": [e.idx for e in example_set]}
            for instruction in instructions
        ]

        result = self.evaluate(test_settings)
        best_index = result.index(max(result, key=lambda x: x[metric]))
        best_setting = test_settings[best_index]
        return best_setting, result

    def evaluate(self, job_settings: list[dict], num_workers: int = 5, **kwargs):

        pbar = tqdm.tqdm(total=len(job_settings), dynamic_ncols=True, disable=not self.display_progress)
        pbar.set_description("Evaluating Instructions")

        results = []
        for idx, job_setting in enumerate(job_settings):
            evaluator = EvaluationEngine(self.job, self.RUN_PER_SAMPLE)
            result = evaluator.evaluate(self.test_set, job_setting)
            results.append(result)
            pbar.update(1)
        pbar.close()
        return results

    def examples_to_prompt(self, examples: list[ExampleRecord]):
        return [{"input": example.input, "output": example.output} for example in examples]

    @property
    def test_set_ids(self):
        return [r.idx for r in self.test_set]
