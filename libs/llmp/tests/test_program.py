import pytest
from llmp.services.program import Program
from structgenie.pydantic_v1 import BaseModel
from typing import Literal

class InputObject(BaseModel):
    book_title: str
    book_author: str
    release_year: int

class OutputObject(BaseModel):
    genre: Literal["fiction", "non-fiction", "fantasy", "sci-fi", "romance", "thriller", "horror", "other"]

@pytest.fixture
def input_model():
    return InputObject

@pytest.fixture
def output_model():
    return OutputObject

@pytest.fixture
def program(input_model, output_model):
    signature = "test_signature"
    program = Program(signature, input_model, output_model)
    return program

def test_init(program):
    assert program.job is not None
    assert program.config is not None

def test_call(program, input_model):
    input_dict = input_model(book_title="The Lord of the Rings", book_author="J.R.R. Tolkien", release_year=1954)
    output = program(input_dict.dict(), raise_errors=True)
    assert output is not None

def test_load_by_signature(program):
    signature = "test_signature"
    assert program._load_by_signature(signature) is True

def test_load_by_io_model(program, input_model, output_model):
    assert program._load_by_io_model(input_model, output_model) is True

def test_event_log(program):
    assert program.event_log() is not None

def test_generation_log(program):
    assert program.generation_log() is not None


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])