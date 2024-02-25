import pytest
from llmp.data_model import JobRecord, ExampleRecord
from llmp.data_model.events import Event
from llmp.integration.structgenie import InputModel, OutputModel, Example
from llmp.types import EventType


def test_job_record_creation():
    input_model = InputModel()
    output_model = OutputModel()
    example_record = ExampleRecord(
        example=Example(input={}, output={}),
        version=0
    )
    job_record = JobRecord(
        job_name="Test Job",
        version=0,
        is_explicit=False,
        config={},
        input_model=input_model,
        output_model=output_model,
        example_records=[example_record],
        instruction="Test instruction",
        version_history=[{0: {}}],
        generation_log=[],
        event_log=[]
    )

    assert job_record.job_name == "Test Job"
    assert job_record.version == 0
    assert job_record.is_explicit == False
    assert job_record.config == {}
    assert job_record.input_model == input_model
    assert job_record.output_model == output_model
    assert job_record.example_records == [example_record]
    assert job_record.instruction == "Test instruction"
    assert job_record.version_history == [{0: {}}]
    assert job_record.generation_log == []
    assert job_record.event_log == []

def test_job_record_methods():
    input_model = InputModel()
    output_model = OutputModel()
    example_record = ExampleRecord(
        example=Example(input={}, output={}),
        version=0
    )
    job_record = JobRecord(
        job_name="Test Job",
        version=0,
        is_explicit=False,
        config={},
        input_model=input_model,
        output_model=output_model,
        example_records=[example_record],
        instruction="Test instruction",
        version_history=[{0: {}}],
        generation_log=[],
        event_log=[]
    )

    event = Event(event_type=EventType.JOB_CREATION, event_metric={}, job_settings={})
    job_record.log_event(event)
    assert job_record.event_log == [event]

    event = job_record.log_generation({}, {}, {}, {})
    generation_log = {"event_id": event.event_id, "input": {}, "output": {}}
    assert job_record.generation_log == [generation_log]

    examples = job_record.get_examples()
    assert examples == [example_record.example]


if __name__ == "__main__":
    pytest.main()