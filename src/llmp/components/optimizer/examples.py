"""
Example Optimizer

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
from llmp.components.base import BaseOptimizer
from llmp.components.evaluation.engine import EvaluationEngine
from llmp.components.example_manager import ExampleManager
from llmp.data_model import JobRecord, ExampleRecord
from llmp.types import TestSetMode


class ExampleOptimizer(BaseOptimizer):

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
            max_examples_per_prompt: int = 4,
            debug: bool = False, **kwargs):
        super().__init__(job, debug, display_progress)
        self.example_manager = ExampleManager(self.job, debug=self.debug)
        self.test_set = test_set
        self.max_examples_per_prompt = max_examples_per_prompt

    def prepare_job(self):
        # create 20 examples per MajorVoteGenerator

        pbar = self.get_progress_bar(3, f"Preparing Job - Filling Examples #{self.PROMPT_SAMPLE_SIZE}", leave=False)

        if len(self.job.example_records) <= self.PROMPT_SAMPLE_SIZE:
            self.example_manager.fill_examples(self.PROMPT_SAMPLE_SIZE)

        pbar.update(1)
        pbar.set_description(f"Preparing Job - Filling Examples #{self.MIN_EXAMPLES}", refresh=True)

        if len(self.job.example_records) <= self.MIN_EXAMPLES:
            self.example_manager.fill_examples(self.MIN_EXAMPLES)

        pbar.update(1)
        pbar.set_description(f"Preparing Job - Creating Test Set #{self.TEST_SIZE}", refresh=True)

        if not self.test_set:
            self.test_set = self.example_manager.get_test_set(self.TEST_SIZE, mode=self.SELECT_MODE)

        pbar.update(1)
        pbar.close()

    def optimize(self, mode: str = "random", metric: str = "accuracy"):
        """Optimize the prompts and examples for a specific job."""
        self.prepare_job()

        # step 2: create an instruction test set
        pbar = self.get_progress_bar(self.max_examples_per_prompt - 1, "Testing Example Sets")
        sub_pbar = self.get_progress_bar(self.max_examples_per_prompt - 1, "Testing Example", sub=True, leave=False)

        current_metric = 0
        current_set = []
        for set_size in range(1, self.max_examples_per_prompt):
            pbar.set_description(
                f"Testing Example Sets - Size {set_size + 1}/{self.max_examples_per_prompt}", refresh=True
            )
            exclude_set = self.test_set_ids + current_set
            example_sets = self.example_manager.get_possible_sets(1, exclude_ids=exclude_set)
            test_settings = [
                {"example_ids": [*current_set, *[e.idx for e in example_set]]}
                for example_set in example_sets
            ]
            result = self.evaluate(test_settings)
            best_index = result.index(max(result, key=lambda x: x[metric]))
            best_setting = test_settings[best_index]
            best_metric = result[best_index][metric]
            pbar.update(1)

            if best_metric >= current_metric:
                current_metric = best_metric
                current_set = best_setting["example_ids"]
                print(f">>> Best Example Set: {current_set}")
                print(f">>> Found better example set with metric:\n{result[best_index]}")

            else:
                print("No better example found. Stopping evaluation")
                break
        pbar.close()

        return current_set, current_metric

    def evaluate(self, job_settings: list[dict], pabr, **kwargs):

        pbar = self.get_progress_bar(len(job_settings), "Evaluating Examples", leave=False, sub=True)
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
