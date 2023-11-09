"""
Job Storage Service
==========================
Data Access Layer for Jobs
==========================

This service is responsible for storing and retrieving jobs and their associated data.
"""

import json
import jsonlines
import shutil
from pathlib import Path

from llmp.data_model import JobRecord, ExampleRecord
from llmp.data_model.events import Event
from llmp.utils.encoder import JSONEncoder, dumps_encoder
from llmp.utils.signature import is_valid_uuid, safe_job_name


class JobStorage:

    def __init__(self, base_path: str = None):
        self.base_path = base_path or "./data/jobs"

    def store_job(self, job: JobRecord) -> None:
        self._save_job(job)

    def get_job(self, signature: str) -> JobRecord:
        """Load a job by signature name or id.

        Args:
            signature (str): The signature name, id or hash of the job.
        Returns:
            JobRecord: The loaded job.
        """
        if is_valid_uuid(signature):
            return self._load_job(signature)
        else:
            return self._load_job_from_register(signature)

    def update_job(self, job: JobRecord) -> None:
        self._save_job(job)

    def delete_job(self, idx: str) -> None:
        job_dir = Path(self.base_path) / idx
        if job_dir.exists():
            shutil.rmtree(job_dir)

    def store_generation_log(self, job: JobRecord, generation: list[dict]) -> None:
        job_dir = self._get_job_directory(job)

        with jsonlines.open(job_dir / "generation_log.jsonl", mode='a', dumps=dumps_encoder) as writer:
            for entry in generation:
                writer.write(entry)

    def load_generation_log(self, job: JobRecord) -> list[dict]:
        job_dir = self._get_job_directory(job)

        with jsonlines.open(job_dir / "generation_log.jsonl", mode='r') as reader:
            return [entry for entry in reader]

    def load_event_log(self, job: JobRecord) -> list[Event]:
        job_dir = self._get_job_directory(job)

        with jsonlines.open(job_dir / "event_log.jsonl", mode='r') as reader:
            return [Event.parse_obj(entry) for entry in reader]

    def store_event_log(self, job: JobRecord, events: list[Event]) -> None:
        job_dir = self._get_job_directory(job)

        with jsonlines.open(job_dir / "event_log.jsonl", mode='a', dumps=dumps_encoder) as writer:
            for event in events:
                writer.write(event.dict())

    def store_logs(self, job: JobRecord):
        if len(job.event_log) > 0 or len(job.generation_log) > 0:
            self._save_logs(job)

    # ==== Private Methods ====

    def _save_job(self, job: JobRecord) -> None:
        """Save the Job object components to separate files."""
        job_dir = self._get_job_directory(job)
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save Metadata
        exclude_metadata = {"example_records", "version_history", "action_history", "generation_history"}
        with (job_dir / "metadata.json").open('w') as f:
            json.dump(job.dict(exclude=exclude_metadata), f, cls=JSONEncoder)

        # Save Examples
        with jsonlines.open(job_dir / "examples.jsonl", mode='w', dumps=dumps_encoder) as writer:
            for example in job.example_records:
                writer.write(example.dict())

        # Save Version History
        with jsonlines.open(job_dir / "version_history.jsonl", mode='w', dumps=dumps_encoder) as writer:
            for version, version_data in job.version_history.items():
                writer.write(dict(version=version, **version_data))

        # Save/append logs
        self._save_logs(job)

    def _save_logs(self, job: JobRecord) -> None:
        """Save the Job object components to separate files."""
        job_dir = self._get_job_directory(job)
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save/Append Event History
        mode = 'a' if (job_dir / "event_log.jsonl").exists() else 'w'
        with jsonlines.open(job_dir / "event_log.jsonl", mode=mode, dumps=dumps_encoder) as writer:
            while job.event_log:
                event = job.event_log.pop(0)
                writer.write(event.dict())

        # Save/Append Generation History
        mode = 'a' if (job_dir / "generation_log.jsonl").exists() else 'w'
        with jsonlines.open(job_dir / "generation_log.jsonl", mode=mode, dumps=dumps_encoder) as writer:
            while job.generation_log:
                generation = job.generation_log.pop(0)
                writer.write(generation)

    def _load_job(self, job_idx: str) -> "JobRecord":
        job_dir = Path(self.base_path) / job_idx

        # Load Metadata
        with (job_dir / "metadata.json").open('r') as f:
            metadata = json.load(f)

        # Load Examples
        with jsonlines.open(job_dir / "examples.jsonl", mode='r') as reader:
            metadata["example_records"] = [ExampleRecord.parse_obj(example) for example in reader]

        # Load Version History
        with jsonlines.open(job_dir / "version_history.jsonl", mode='r') as reader:
            metadata["version_history"] = {entry["version"]: entry for entry in reader}

        return JobRecord(**metadata)

    def _load_job_from_register(self, key: str) -> "JobRecord":
        with (Path(self.base_path) / "job_register.json").open('r') as f:
            job_names = json.load(f)
        job_idx = job_names[key]
        return self._load_job(job_idx)

    def register_job(self, job_name: str, job_idx: str, io_hash: str) -> str:
        """Register a job name to a job id.

        If the job name already exists, append a versioning to the end of the name.

        Args:
            job_name (str): The job name to register.
            job_idx (str): The job id to register.
            io_hash (str): The io_hash of the input and output model to register.
        Returns:
            str: The registered job name.
        """
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        registry_file = Path(self.base_path) / "job_register.json"

        if registry_file.exists():
            with (Path(self.base_path) / "job_register.json").open('r') as f:
                job_names = json.load(f)
        else:
            # create file
            job_names = {}

        safe_name = safe_job_name(job_name, job_names.keys())
        job_names[safe_name] = job_idx
        job_names[io_hash] = job_idx

        with open(str(registry_file), mode='w') as f:
            json.dump(job_names, f)

        return safe_name

    def _get_job_directory(self, job: JobRecord) -> Path:
        return Path(self.base_path) / job.idx
