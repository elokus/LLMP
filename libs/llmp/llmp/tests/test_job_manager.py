from pathlib import Path
from llmp.tests.resources.fixtures import job_manager, create_job_input, job_id


def test_job_creation(job_manager, create_job_input):
    job_id = job_manager.create_job(**create_job_input).idx
    check_path = Path(job_manager.base_path) / job_id
    assert check_path.exists(), "Job directory was not created"

    job_manager.delete_job(job_id)
    assert not check_path.exists(), "Job directory was not deleted"


def test_job_loading(job_manager, job_id):
    job = job_manager.get_job(job_id)
    assert job.job_name == "test_job", "Job name was not loaded correctly"


def test_update_job(job_manager, job_id):
    job = job_manager.get_job(job_id)
    job.job_name = "updated_job_name"
    new_job_id = "ef99861f501942888a73783a6d8202ab"
    job.idx = new_job_id
    job_manager.update_job(job)
    job = job_manager.get_job(new_job_id)
    assert job.job_name == "updated_job_name", "Job name was not updated correctly"
    job_manager.delete_job(new_job_id)


def test_delete_job(job_manager, job_id):
    new_job_id = "ef99861f501942888a73783a6d8202ab"
    old_job = job_manager.get_job(job_id)
    old_job.idx = new_job_id
    job_manager.update_job(old_job)
    check_path = Path(job_manager.base_path) / new_job_id
    assert check_path.exists(), "Job was not updated with new id"
    job_manager.delete_job(new_job_id)
    assert not check_path.exists(), "Job directory was not deleted"