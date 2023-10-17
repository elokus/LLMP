from llmp.tests.resources.fixtures import job_manager, create_job_input
from llmp.data_model.events import Event
from llmp.types import EventType


def test_job_event_log_loading(job_manager, create_job_input):
    job = job_manager.create_job(**create_job_input)
    event_log = job_manager.load_event_log(job)
    assert len(event_log) >= 1, "Event log was not loaded correctly"
    assert all([isinstance(event, Event) for event in event_log]), "Event log was not loaded correctly"


def test_event_log_adding(job_manager, create_job_input):
    job = job_manager.create_job(**create_job_input)
    event_log = job_manager.load_event_log(job)
    job.log_event(Event(event_type=EventType.EVAL_RUN))
    job_manager.update_job(job)
    new_event_log = job_manager.load_event_log(job)
    assert len(new_event_log) == len(event_log) + 1, "Event log was not updated correctly"
