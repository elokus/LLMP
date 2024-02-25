import pytest
from pathlib import Path

from tests.resources.fixtures import job_manager, test_job
from llmp.components.example_manager import ExampleManager



def test_fill_examples(test_job, job_manager):
    example_manager = ExampleManager(test_job, debug=True)
    example_manager.fill_examples(10, raise_errors=False)
    job_manager.update_job(test_job)
    assert len(test_job.example_records) == 10, "Examples were not filled correctly"
    job_manager.delete_job(test_job.idx)


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])