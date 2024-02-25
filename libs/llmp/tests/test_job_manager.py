import pytest
from llmp.services.job_manager import JobManager
from llmp.components.settings.program_settings import ProgramSettings
from llmp.types import IOModelDefinition
from structgenie.pydantic_v1 import BaseModel
from typing import Literal

class InputObject(BaseModel):
    book_title: str
    book_author: str
    release_year: int

class OutputObject(BaseModel):
    genre: Literal["fiction", "non-fiction", "fantasy", "sci-fi", "romance", "thriller", "horror", "other"]

@pytest.fixture
def job_manager():
    return JobManager()

@pytest.fixture
def input_model():
    return InputObject

@pytest.fixture
def output_model():
    return OutputObject

@pytest.fixture
def config():
    return ProgramSettings()


def test_create_job(job_manager, config):
    job = job_manager.create_job(
        "Book to Genre",
        input_model=InputObject,
        output_model=OutputObject,
        config=config.dict(),
        raise_errors=True
    )
    assert job is not None


def test_get_job(job_manager, config):
    job = job_manager.create_job(
        "Book to Genre",
        input_model=InputObject,
        output_model=OutputObject,
        config=config.dict(),
        raise_errors=True
    )
    old_idx = job.idx
    job = job_manager.get_job(job.idx)
    assert job is not None
    assert job.idx == old_idx
    job_manager.delete_job(job.idx)

def test_update_job(job_manager, config):
    job = job_manager.create_job(
        "Book to Genre v2",
        instruction="Another instruction",
        input_model=InputObject,
        output_model=OutputObject,
        config=config.dict()
    )
    job.instruction = "New instruction"
    job_manager.update_job(job)
    job = job_manager.get_job(name="Book to Genre v2")
    assert job.instruction == "New instruction"
    job_manager.delete_job(job.idx)

def test_delete_job(job_manager, input_model, output_model, config):
    job = job_manager.create_job(
        "Book to Genre",
        input_model=input_model,
        output_model=output_model,
        config=config.dict()
    )
    job_manager.delete_job(job.idx)
    with pytest.raises(Exception):
        job_manager.get_job(job.idx)

def test_get_job_by_input_output_model(job_manager, input_model, output_model, config):
    job = job_manager.create_job(
        "Book to Genre",
        input_model=input_model,
        output_model=output_model,
        config=config.dict()
    )
    retrieved_job = job_manager.get_job_by_input_output_model(input_model, output_model)
    assert retrieved_job.idx == job.idx
    job_manager.delete_job(job.idx)

if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
