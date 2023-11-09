from enum import Enum
from typing import Tuple, Type, Union

from pydantic import BaseModel
from structgenie.components.input_output import InputModel, OutputModel

GenOutput = Tuple[dict, dict]


UnionIOModel = Union[InputModel, OutputModel]
IOModelDefinition = Union[UnionIOModel, str, dict, Type[BaseModel]]


class VerificationType(Enum):
    """Validation rank for ExampleRecords

    SINGLE_VOTE: Example output is created by a single generation execution.
    MAJORITY_VOTE: Example output is created by a majority vote of generation executions.
    MAJORITY_GRADE: Example output is created by a majority grade of generation executions.
    USAGE_VERIFIED: Example output is used/generated multiple times without claims.
    HUMAN_VERIFIED: Example output is verified by human interaction.
    """
    SINGLE_VOTE = 1
    MAJORITY_VOTE = 2
    MAJORITY_GRADE = 3
    USAGE_VERIFIED = 4
    HUMAN_VERIFIED = 5


class EventType(str, Enum):
    GENERATION: str = "generation"
    SAMPLE_EVAL: str = "sample_evaluation"
    EVAL_RUN: str = "evaluation_run"
    ADD_EXAMPLES: str = "example_add"
    REMOVE_EXAMPLES: str = "example_remove"
    UPDATE_EXAMPLES: str = "example_update"
    UPDATE_JOB: str = "job_update"
    JOB_CREATION: str = "job_creation"

class MajorVoteType(str, Enum):
    CONSENSUS = "consensus"
    GRADE = "grade"


class TestSetMode(str, Enum):
    RANDOM: str = "random"
    ACCURACY: str = "accuracy"


