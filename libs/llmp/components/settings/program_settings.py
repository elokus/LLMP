from enum import Enum

from pydantic import BaseModel


class PromptType(str, Enum):
    ZERO_SHOT = "zero_shot"
    ONE_SHOT = "one_shot"
    FEW_SHOT = "few_shot"
    ZERO_SHOT_COT = "zero_shot_cot"
    FEW_SHOT_COT = "few_shot_cot"
    ONE_SHOT_COT = "one_shot_cot"


class ProgramSettings(BaseModel):

    log_action: bool = True
    auto_optimize: bool = True
    generator_type: str = "default"
    program_type: str = PromptType.ZERO_SHOT

    total_sample_size: int = 20
    max_few_shot_size: int = 5

    # First run settings
    fr_optimization: bool = True
    fr_human_verification: bool = True

    # Optimization settings
    test_size: int = 5
    test_set_selection: str = "random"
    runs_per_input: int = 5
    metric: str = "accuracy"
    early_stopping: bool = True
    early_stopping_patience: int = 2

    # Model settings
    model_name: str = "gpt-3.5-turbo"
    max_token: int = 3000
    temperature: float = 0.9
    top_p: float = 1
    best_of: int = 1
    frequency_penalty: float = 0
    presence_penalty: float = 0
    max_retry: int = 3

    @staticmethod
    def model_to_context_size(model_name: str = "gpt-3.5-turbo") -> int:
        """Calculate the maximum number of tokens possible to generate for a model.

        Args:
            modelname: The modelname we want to know the context size for.

        Returns:
            The maximum context size

        Example:
            .. code-block:: python

                max_tokens = openai.modelname_to_contextsize("text-davinci-003")
        """
        model_token_mapping = {
            "gpt-4": 8192,
            "gpt-4-0314": 8192,
            "gpt-4-0613": 8192,
            "gpt-4-32k": 32768,
            "gpt-4-32k-0314": 32768,
            "gpt-4-32k-0613": 32768,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-0301": 4096,
            "gpt-3.5-turbo-0613": 4096,
            "gpt-3.5-turbo-16k": 16385,
            "gpt-3.5-turbo-16k-0613": 16385,
            "gpt-3.5-turbo-instruct": 4096,
            "text-ada-001": 2049,
            "ada": 2049,
            "text-babbage-001": 2040,
            "babbage": 2049,
            "text-curie-001": 2049,
            "curie": 2049,
            "davinci": 2049,
            "text-davinci-003": 4097,
            "text-davinci-002": 4097,
            "code-davinci-002": 8001,
            "code-davinci-001": 8001,
            "code-cushman-002": 2048,
            "code-cushman-001": 2048,
        }
        return model_token_mapping.get(model_name, 2049)
