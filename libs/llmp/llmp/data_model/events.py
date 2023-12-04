"""
Event model for logging events.
===============================
# TODO: Generalize the model for all events.
currently referencing example_id and example_version
We want to achieve a more generalized logic for all events. How should we log new instructions, changing example versions, etc.?
We want also to assure a rollback mechanism for all events. How should we achieve this?

We need to log the following event data:
    - event_id: unique id for each event
    - timestamp: timestamp of the event
    - event_type: type of the event

Event specific data:
    - example_id: id of the example
    - example_version: version of the example
    - ref_event_id: reference to another event like the generation event
    - event_metrics: metrics of the event
    - job_setting: job settings of the event

    - extra: extra data for the event

"""

from typing import Union, Optional
from uuid import uuid4, UUID

from pydantic import BaseModel, Field

from llmp.types import EventType
from llmp.utils.helper import get_timestamp


class Event(BaseModel):
    event_id: str = Field(default_factory=lambda: uuid4().hex)
    timestamp: str = Field(default_factory=get_timestamp)
    event_type: EventType
    event_metrics: Union[dict, None] = None

    # ---
    job_setting: Union[dict, None] = None
    job_version: Union[int, None] = None
    example_id: Union[str, list[str], None] = None
    example_version: Union[int, None] = None
    extra: Union[dict, None] = None
    ref_event_id: Union[str, None] = None

    @classmethod
    def from_sample_metric(cls, sample_metric: dict, job_setting: dict, example_id: Union[str, UUID] = None, **kwargs):
        return cls(
            event_type=EventType.SAMPLE_EVAL,
            example_id=example_id,
            event_metrics=sample_metric,
            job_setting=job_setting,
            **kwargs
        )

    @classmethod
    def from_evaluation_metric(cls, eval_metric: dict, job_setting: dict, example_ids: list[str] = None, **kwargs):
        return cls(
            event_type=EventType.EVAL_RUN,
            example_id=example_ids,
            event_metrics=eval_metric,
            job_setting=job_setting,
            **kwargs
        )

    @classmethod
    def from_generation_job(cls, event_metric: dict, job_setting: dict, example_id: Union[str, UUID] = None, **kwargs):
        return cls(
            event_type=EventType.GENERATION,
            example_id=example_id,
            event_metrics=event_metric,
            job_setting=job_setting,
            **kwargs
        )
