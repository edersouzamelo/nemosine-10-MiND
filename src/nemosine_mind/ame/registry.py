from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from .models import AMECycleRecord


class JsonlRegistry:
    """
    Componente 5 (TR-004): Registro Estrutural
    - Persistência mínima em JSONL.
    - Entrada, config e saída do ciclo para rastreabilidade.
    """

    def __init__(self, path: str):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def append(self, record: AMECycleRecord) -> None:
        line = json.dumps({
            "cycle_id": record.cycle_id,
            "input": record.input,
            "config": record.config,
            "output": record.output,
            "meta": record.meta,
        }, ensure_ascii=False)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def read_last(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.path):
            return None
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            if not lines:
                return None
            return json.loads(lines[-1])
        except Exception:
            return None
