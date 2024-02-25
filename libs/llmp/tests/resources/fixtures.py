from typing import Literal

import pytest
from structgenie.pydantic_v1 import BaseModel
import llmp.services.job_manager as jm
import llmp.services.job_storage as js


@pytest.fixture
def create_job_input():
    class Input(BaseModel):
        description: str
        sources: list[Literal["internal", "external"]]

    class Output(BaseModel):
        external_types: list[Literal['numeric', 'textual', 'multimedia', 'code', None]]
        internal_types: list[Literal['numeric', 'textual', 'multimedia', 'code', None]]

    return {
        "job_name": "test_job",
        "instruction": (
            "Define the data types needed to create a output product."
            "Using the output description and provided data sources, decide on the types of data to be used."),
        "input_examples": [
            Input(
                description="A research paper on the effects of climate change on agriculture to be written",
                sources=["external"]
            ),
            Input(
                description="An internal report on the effects of climate change on agriculture to be written",
                sources=["internal", "external"]
            )
        ],
        "output_examples": [
            Output(external_types=["textual", "numeric"], internal_types=[]),
            Output(external_types=["textual", "numeric"], internal_types=["textual", "numeric"])
        ]
    }


@pytest.fixture
def job_manager():
    return jm.JobManager()

@pytest.fixture
def job_storage():
    return js.JobStorage()

@pytest.fixture
def job_id():
    return test_job.idx


@pytest.fixture
def temp_job_id():
    return "ef99861f501942888a73783a6d8202ab"


@pytest.fixture
def test_job():

    class Input(BaseModel):
        description: str
        sources: list[Literal["internal", "external"]]

    class Output(BaseModel):
        external_types: list[Literal['numeric', 'textual', 'multimedia', 'code', None]]
        internal_types: list[Literal['numeric', 'textual', 'multimedia', 'code', None]]

    job_input = {
        "job_name": "test_job",
        "instruction": (
            "Define the data types needed to create a output product."
            "Using the output description and provided data sources, decide on the types of data to be used."),
        "input_examples": [
            Input(
                description="A research paper on the effects of climate change on agriculture to be written",
                sources=["external"]
            ),
            Input(
                description="An internal report on the effects of climate change on agriculture to be written",
                sources=["internal", "external"]
            )
        ],
        "output_examples": [
            Output(external_types=["textual", "numeric"], internal_types=[]),
            Output(external_types=["textual", "numeric"], internal_types=["textual", "numeric"])
        ]
    }
    job = jm.JobManager().create_job(input_model=Input, output_model=Output, **job_input)
    return job

@pytest.fixture
def test_output_concensus_generator():
    return [({'external_types': ['textual'], 'internal_types': ['textual', 'multimedia']},
               {'execution_time': 0.8263273239135742,
                'token_usage': 307,
                'model_name': 'gpt-3.5-turbo',
                'model_config': {},
                'failure_rate': 1,
                'errors': []}),
              ({'external_types': [], 'internal_types': ['textual', 'multimedia']},
               {'execution_time': 1.0414953231811523,
                'token_usage': 304,
                'model_name': 'gpt-3.5-turbo',
                'model_config': {},
                'failure_rate': 1,
                'errors': []}),
              ({'external_types': ['textual'], 'internal_types': ['textual', 'multimedia']},
               {'execution_time': 1.0877337455749512,
                'token_usage': 307,
                'model_name': 'gpt-3.5-turbo',
                'model_config': {},
                'failure_rate': 1,
                'errors': []}),
              ({'external_types': ['textual', 'multimedia'],
                'internal_types': ['textual', 'multimedia']},
               {'execution_time': 1.1719236373901367,
                'token_usage': 310,
                'model_name': 'gpt-3.5-turbo',
                'model_config': {},
                'failure_rate': 1,
                'errors': []}),
              ({'external_types': ['textual'], 'internal_types': ['textual', 'multimedia']},
               {'execution_time': 1.1568892002105713,
                'token_usage': 307,
                'model_name': 'gpt-3.5-turbo',
                'model_config': {},
                'failure_rate': 1,
                'errors': []})]
