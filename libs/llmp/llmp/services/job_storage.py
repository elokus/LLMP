import shutil
from pathlib import Path
from typing import Union

from llmp.data_model import JobRecord, ExampleRecord
from llmp.data_model.events import Event
from llmp.utils.filesystem import FileOperations
from llmp.utils.io_model import hash_from_io_models
from llmp.utils.signature import is_valid_uuid, safe_job_name


class JobStorage(FileOperations):

    def __init__(self, base_path: str = None):
        self.base_path = base_path or "./data/jobs"

    def store_job(self, job: JobRecord) -> None:
        self._save_job(job)

    def get(self, idx: str = None, name: str = None, io_hash: str = None) -> JobRecord:
        """Load a job by idx, name, or io_hash.

        Only one of idx, name, or io_hash should be provided.
        """

        assert sum([idx is not None, name is not None,
                    io_hash is not None]) == 1, "Only one of idx, name, or io_hash must be provided."

        if idx is None:
            if name is not None:
                idx = self.get_idx_by_name(name)
            elif io_hash is not None:
                idx = self.get_idx_by_io_hash(io_hash)
            else:
                raise ValueError("One of idx, name, or io_hash must be provided.")

        if not idx:
            raise ValueError("No job found.")

        return self._load_job(idx)

    def update_job(self, job: JobRecord) -> None:
        new_io_hash = hash_from_io_models(job.input_model, job.output_model, job.instruction)
        new_name = job.job_name
        self._update_registry(job.idx, new_name, new_io_hash)
        self._save_job(job)

    def delete_job(self, idx: str) -> None:
        job_dir = Path(self.base_path) / idx
        if job_dir.exists():
            shutil.rmtree(job_dir)
        self._delete_from_registry(idx)

    # ==== IDX Registry Methods ====

    def get_registry_keys(self) -> list[str]:
        """Retrieve the keys of the registry."""
        return list(self._load_registry().keys())

    def key_in_registry(self, key: str) -> bool:
        """Check if key in registry."""
        if key in self._load_registry():
            return True
        return False

    def register_job(self, job: JobRecord):
        """Register a job in the registry."""
        registry = self._load_registry()
        assert job.io_hash not in registry.keys(), f"Job with io_hash '{job.io_hash}' already exists."
        assert job.job_name not in registry.keys(), f"Job with name '{job.job_name}' already exists."

        registry[job.job_name] = job.idx
        registry[job.io_hash] = job.idx

        registry_file = Path(self.base_path) / "job_register.json"
        self._write_json_file(registry_file, registry)

    def get_idx_by_name(self, name: str) -> Union[str, None]:
        """Retrieve the idx of a job by its name."""
        return self._get_idx_from_register(name)

    def get_idx_by_io_hash(self, io_hash: str) -> Union[str, None]:
        """Retrieve the idx of a job by its io_hash."""
        return self._get_idx_from_register(io_hash)

    # ==== Log Methods ====

    def store_generation_log(self, job: JobRecord, generation: list[dict]) -> None:
        job_dir = self._get_job_directory(job)
        self._write_jsonl_file(job_dir / "generation_log.jsonl", generation)

    def load_generation_log(self, job: JobRecord) -> list[dict]:
        job_dir = self._get_job_directory(job)
        return self._read_jsonl_file(job_dir / "generation_log.jsonl")

    def load_event_log(self, job: JobRecord) -> list[Event]:
        job_dir = self._get_job_directory(job)
        return [Event.parse_obj(entry) for entry in self._read_jsonl_file(job_dir / "event_log.jsonl")]

    def store_event_log(self, job: JobRecord, events: list[Event]) -> None:
        job_dir = self._get_job_directory(job)
        self._write_jsonl_file(job_dir / "event_log.jsonl", [event.dict() for event in events])

    def store_logs(self, job: JobRecord):
        if len(job.event_log) > 0 or len(job.generation_log) > 0:
            self._save_logs(job)

    # ==== Private Methods ====

    def _save_job(self, job: JobRecord) -> None:
        job_dir = self._get_job_directory(job)
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save Metadata
        exclude_metadata = {"example_records", "version_history", "event_log", "generation_log"}
        self._write_json_file(job_dir / "metadata.json", job.dict(exclude=exclude_metadata))

        # Save Examples
        self._write_jsonl_file(job_dir / "examples.jsonl", [example.dict() for example in job.example_records])

        # Save Version History
        self._write_jsonl_file(job_dir / "version_history.jsonl", [dict(version=version, **version_data) for version, version_data in job.version_history.items()])

        # Save/append logs
        self._save_logs(job)

    def _save_logs(self, job: JobRecord) -> None:
        job_dir = self._get_job_directory(job)
        job_dir.mkdir(parents=True, exist_ok=True)

        # Save/Append Event History
        event_log = self._read_jsonl_file(job_dir / "event_log.jsonl")
        event_ids = [event["event_id"] for event in event_log]
        new_events = [event.dict() for event in job.event_log if event.event_id not in event_ids]
        self._append_jsonl_file(job_dir / "event_log.jsonl", new_events)
        job.event_log = []

        # Save/Append Generation History
        generation_log = self._read_jsonl_file(job_dir / "generation_log.jsonl")
        event_ids = [event["event_id"] for event in generation_log]
        new_events = [event for event in job.generation_log if event["event_id"] not in event_ids]
        self._append_jsonl_file(job_dir / "generation_log.jsonl", new_events)
        job.generation_log = []

    def _load_job(self, job_idx: str) -> "JobRecord":
        job_dir = Path(self.base_path) / job_idx

        # Load Metadata
        metadata = self._read_json_file(job_dir / "metadata.json")

        # Load Examples
        metadata["example_records"] = [ExampleRecord.parse_obj(example) for example in self._read_jsonl_file(job_dir / "examples.jsonl")]

        # Load Version History
        metadata["version_history"] = {entry["version"]: entry for entry in self._read_jsonl_file(job_dir / "version_history.jsonl")}

        return JobRecord(**metadata)


    def io_hash_in_register(self, io_hash: str):
        registry_file = Path(self.base_path) / "job_register.json"
        job_names = self._read_json_file(registry_file) if registry_file.exists() else {}
        return io_hash in job_names

    def _get_job_directory(self, job: JobRecord) -> Path:
        return Path(self.base_path) / job.idx

    def _delete_from_registry(self, idx: str):
        registry_file = Path(self.base_path) / "job_register.json"
        registry = self._load_registry()

        del_keys = [key for key, value in registry.items() if value == idx]
        for key in del_keys:
            del registry[key]
        self._write_json_file(registry_file, registry)

    def _update_registry(self, idx: str, new_name: str, new_hash: str):
        registry_file = Path(self.base_path) / "job_register.json"
        job_names = self._read_json_file(registry_file) if registry_file.exists() else {}

        del_keys = [key for key, value in job_names.items() if value == idx]
        for key in del_keys:
            del job_names[key]
        job_names[new_name] = idx
        job_names[new_hash] = idx
        self._write_json_file(registry_file, job_names)

    def _load_registry(self) -> dict:
        """Retrieve the keys of the registry."""
        Path(self.base_path).mkdir(parents=True, exist_ok=True)
        registry_file = Path(self.base_path) / "job_register.json"

        registry = self._read_json_file(registry_file) if registry_file.exists() else {}
        return registry

    def _get_idx_from_register(self, key: str) -> str:
        """Retrieve the idx of a job from the register using a key."""
        registry = self._load_registry()
        return registry.get(key, None)
