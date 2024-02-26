import pytest

from llmp.components.settings.program_settings import ProgramSettings
from llmp.pydantic_v1 import BaseModel
from llmp.services.job_manager import JobManager
from llmp.services.program import Program


@pytest.fixture
def job_manager():
    return JobManager()


@pytest.fixture
def conditional_job_idx(job_manager):
    class InputObject(BaseModel):
        text: str

    class OutputObject(BaseModel):
        name: str
        age: int
        country: str

    class OutputObjectConditional(BaseModel):
        missing_information: str


    job = job_manager.create_job(
        "Extract data from text input",
        input_model=InputObject,
        output_model=OutputObject,
        condition="If all data is present in the text",
        output_model_cond=OutputObjectConditional,
    )
    return job.idx


def test_conditional_job(conditional_job_idx, job_manager):
    job = job_manager.get_job(conditional_job_idx)
    input_data = {
        "text": "John Doe is 25 years old and lives in the United States."
    }
    output, _ = job_manager.generate_output(job, input_data)

    assert output["name"] == "John Doe"
    assert output["age"] == 25
    assert output["country"] == "United States"


def test_conditional_job_conditional_output(conditional_job_idx, job_manager):
    job = job_manager.get_job(conditional_job_idx)
    input_data = {
        "text": "John Doe is 25 years old."
    }
    output, _ = job_manager.generate_output(job, input_data)

    assert output["missing_information"] is not None
    print(output["missing_information"])


def test_conditional_program():
    class InputObject(BaseModel):
        text: str

    class OutputObject(BaseModel):
        name: str
        age: int
        country: str

    class OutputObjectConditional(BaseModel):
        missing_information: str

    program = Program(
        "Extract data conditional",
        InputObject,
        OutputObject,
        output_model_cond=OutputObjectConditional
    )
    input_data = {"text": "John Doe is 25 years old and lives in the United States."}
    output = program(input_data)
    assert output.name == "John Doe"

    input_data = {"text": "John Doe is 25 years old."}
    output = program(input_data)
    assert output.missing_information is not None
