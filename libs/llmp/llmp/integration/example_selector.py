from structgenie.base import BaseExampleSelector
from structgenie.components.examples.base import Example


class ExampleManagerSelector(BaseExampleSelector):

    def add_example(self, job_id: str, example: dict) -> None:
        pass

    def to_prompt(self, max_token: int = 2000, **kwargs) -> list[dict]:
        pass

    def input_keys(self):
        pass