"""
How to parse validation rank?

Using ValidationType enum from llmp/types.py
    1. ValidationType.SINGLE_VOTE
    2. ValidationType.MAJORITY_VOTE
    3. ValidationType.MAJORITY_GRADE
    4. ValidationType.USAGE_VERIFIED
    5. ValidationType.HUMAN_VERIFIED

Option 1: Calculating float value from enum by devision (e.g. 1/5, 2/5, 3/5, 4/5, 5/5)
Option 2: Using enum value as float or int value (e.g. 1.0, 2.0, 3.0, 4.0, 5.0)
Option 3: Storing validation_rank as dict with ValidationRank as key and a second calculated validation value as value

Next we need to store the failure rate of each example record. We can do this by stroring each execution in a history log
and then calculating the failure rate from the history log. We can also store the failure rate in the example record directly
but nethertheless we would need an execution history log. For calculating the usage count we would also need to keep
track of indirect usage (as an example) and we would need to keep track of the usage count for each version of the example.
While tracking the execution history we could do this on job level as well and not on example record level.
This would simplify the logging process but would make it harder to track the usage count for each version of the example.
"""

from typing import Optional
from uuid import uuid4
from structgenie.pydantic_v1 import BaseModel, validator, Field

from llmp.types import VerificationType
from llmp.integration.structgenie import Example


class ExampleRecord(BaseModel):
    idx: str = Field(default_factory=lambda: uuid4().hex)
    example: Example
    version: int = 0
    version_history: dict[int, Example] = Field(default_factory=dict)

    # --- Example Metrics ---
    gen_event_id: Optional[str] = None
    verification_type: Optional[VerificationType] = None
    reliability: Optional[float] = None
    data_type: Optional[str] = "synthetic"  # "semi-synthetic", "real"

    @property
    def reliability_score(self):
        return self.reliability * float(self.verification_type.value)

    @property
    def input(self):
        return self.example.input

    @property
    def input_keys(self):
        return self.example.input_keys

    @property
    def output_keys(self):
        return self.example.output_keys

    @property
    def output(self):
        return self.example.output

    @classmethod
    @validator('version_history', pre=True)
    def convert_keys_to_int(cls, item):
        return {int(k): v for k, v in item.items()}

    @classmethod
    @validator('verification_type', pre=True)
    def convert_verification_type(cls, item):
        if isinstance(item, int):
            return VerificationType(item)
        return item

    @classmethod
    def from_input_output(cls, input_obj, output_obj, **kwargs):
        return cls(example=Example(input=input_obj, output=output_obj), **kwargs)
