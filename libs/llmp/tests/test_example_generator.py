import pytest
from pathlib import Path

from llmp.tests.resources.fixtures import job_id, job_manager, temp_job_id
from llmp.components.example_manager import ExampleManager


@pytest.fixture
def test_job(job_manager, job_id, temp_job_id):
    check_path = Path(job_manager.base_path) / temp_job_id
    if not check_path.exists():
        old_job = job_manager.get_job(job_id)
        old_job.idx = temp_job_id
        job_manager.update_job(old_job)

    return job_manager.get_job(temp_job_id)


def test_fill_examples(test_job, job_manager):
    example_manager = ExampleManager(test_job)
    example_manager.fill_examples(10)
    job_manager.update_job(test_job)
    assert len(test_job.example_records) == 10, "Examples were not filled correctly"