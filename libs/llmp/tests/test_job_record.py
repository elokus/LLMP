import pytest
from tests.resources.fixtures import test_job
from llmp.data_model.job_record import (input_in_records, get_record_by_input)


@pytest.fixture
def input_example():
    return {
        "description": "A research paper on the effects of climate change on agriculture to be written",
        "sources": ["external"]
    }


def test_example_in_job(test_job, input_example):
    assert input_in_records(test_job, input_example), "Input example was not found in job"


def test_record_by_input(test_job, input_example):
    record = get_record_by_input(test_job, input_example)
    assert record.input["description"] == input_example["description"], "Record was not found by input"
