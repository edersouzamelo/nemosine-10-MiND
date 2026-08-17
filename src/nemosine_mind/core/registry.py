from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from .models import CycleRecord


class JsonlRegistry:
    """Minimal append-only JSONL persistence for cycle records."""

    def __init__(self, path: str):
        self.path = str(Path(path).expanduser())

    def append(self, record: CycleRecord) -> None:
        parent = os.path.dirname(self.path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        line = json.dumps({
            "cycle_id": record.cycle_id,
            "input": record.input,
            "config": record.config,
            "output": record.output,
            "meta": record.meta,
            "status": record.status,
            "error": record.error,
        }, ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as file:
            file.write(line + "\n")

    def read_last(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as file:
                lines = file.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read cycle registry: {self.path}") from exc
