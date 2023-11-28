import json
import jsonlines
from pathlib import Path
from typing import Dict, List
from llmp.utils.encoder import JSONEncoder, dumps_encoder


class FileOperations:

    def _read_json_file(self, file_path: Path) -> Dict:
        with file_path.open('r') as f:
            return json.load(f)

    def _write_json_file(self, file_path: Path, data: Dict) -> None:
        with file_path.open('w') as f:
            json.dump(data, f, cls=JSONEncoder)

    def _read_jsonl_file(self, file_path: Path) -> List[Dict]:
        with jsonlines.open(file_path, mode='r') as reader:
            return [entry for entry in reader]

    def _write_jsonl_file(self, file_path: Path, data: List[Dict]) -> None:
        with jsonlines.open(file_path, mode='w', dumps=dumps_encoder) as writer:
            for entry in data:
                writer.write(entry)

    def _append_jsonl_file(self, file_path: Path, data: List[Dict]) -> None:
        mode = 'a' if file_path.exists() else 'w'
        with jsonlines.open(file_path, mode=mode, dumps=dumps_encoder) as writer:
            for entry in data:
                writer.write(entry)
