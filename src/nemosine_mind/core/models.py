from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class MindInput:
    text: str


@dataclass(frozen=True)
class MindOutput:
    text: str


@dataclass(frozen=True)
class CycleRecord:
    cycle_id: str
    input: Dict[str, Any]
    config: Dict[str, Any]
    output: Dict[str, Any]
    meta: Dict[str, Any]
    status: str = "succeeded"
    error: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class RunResult:
    cycle_id: str
    reply: str
