from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from .models import CycleArtifact


class CycleStore(Protocol):
    def append(self, artifact: CycleArtifact) -> None: ...
    def get(self, cycle_id: str) -> Optional[Dict[str, Any]]: ...
    def list(self, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]: ...
    def read_last(self) -> Optional[Dict[str, Any]]: ...


class JsonlRegistry:
    """Append-only JSONL store with version-aware reads and partial-tail recovery."""

    def __init__(self, path: str):
        self.path = str(Path(path).expanduser())
        self._lock = threading.Lock()

    def append(self, artifact: CycleArtifact) -> None:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        line = json.dumps(artifact.to_dict(), ensure_ascii=False, separators=(",", ":"))
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as file:
                file.write(line + "\n")
                file.flush()
                os.fsync(file.fileno())

    def _read_all(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                raw_lines = file.readlines()
        except OSError as exc:
            raise RuntimeError(f"Could not read cycle registry: {self.path}") from exc
        records: List[Dict[str, Any]] = []
        for index, line in enumerate(raw_lines):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                is_partial_tail = index == len(raw_lines) - 1 and not line.endswith("\n")
                if is_partial_tail:
                    continue
                raise RuntimeError(
                    f"Corrupt cycle registry at line {index + 1}: {self.path}"
                ) from exc
            records.append(CycleArtifact.from_dict(raw).to_dict())
        return records

    def get(self, cycle_id: str) -> Optional[Dict[str, Any]]:
        for record in reversed(self._read_all()):
            if record["cycle_id"] == cycle_id:
                return record
        return None

    def list(self, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        if limit < 1 or limit > 200 or offset < 0:
            raise ValueError("limit must be 1..200 and offset must be non-negative")
        records = list(reversed(self._read_all()))
        return records[offset : offset + limit]

    def read_last(self) -> Optional[Dict[str, Any]]:
        records = self.list(limit=1)
        return records[0] if records else None
