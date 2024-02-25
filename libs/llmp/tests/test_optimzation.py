import pytest

from llmp.data_model import JobRecord
from structgenie.components.input_output import OutputModel, InputModel


@pytest.fixture
def test_job():
    return JobRecord(
        id="test_job",
        input_model=InputModel(
            template_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "label": {"type": "string"}
                }
            }
        ),
        output_model=OutputModel(
            template_schema={
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "label": {"type": "string"}
                }
            }
        )
    )


# def test_instruction_optimization(test_job):
#     # instruction optimization
#     assert test_job.instruction == "return input_object"
