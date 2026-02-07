from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass(frozen=True)
class AMEInput:
    text: str


@dataclass(frozen=True)
class AMEOutput:
    text: str


@dataclass(frozen=True)
class AMECycleRecord:
    cycle_id: str
    input: Dict[str, Any]
    config: Dict[str, Any]
    output: Dict[str, Any]
    meta: Dict[str, Any]


@dataclass(frozen=True)
class RunResult:
    cycle_id: str
    reply: str
