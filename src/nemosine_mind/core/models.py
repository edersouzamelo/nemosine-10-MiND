from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


CYCLE_SCHEMA_VERSION = "mind.cycle/1"


def utc_now() -> str:
    """Return a stable, timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z"
    )


@dataclass(frozen=True)
class MindInput:
    text: str


@dataclass(frozen=True)
class MindOutput:
    text: str


@dataclass(frozen=True)
class CycleArtifact:
    """Versioned, provider-neutral audit artifact for one MiND interaction."""

    cycle_id: str
    status: str
    created_at: str
    completed_at: str
    duration_ms: int
    input: Dict[str, Any]
    config: Dict[str, Any]
    provider: Dict[str, Any]
    output: Dict[str, Any]
    error: Optional[Dict[str, Any]] = None
    schema_version: str = CYCLE_SCHEMA_VERSION
    extensions: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cycle_id:
            raise ValueError("cycle_id is required")
        if self.status not in {"succeeded", "failed"}:
            raise ValueError("status must be 'succeeded' or 'failed'")
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if not self.created_at.endswith("Z") or not self.completed_at.endswith("Z"):
            raise ValueError("Cycle Artifact timestamps must be UTC ISO 8601 values")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "cycle_id": self.cycle_id,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "input": self.input,
            "config": self.config,
            "provider": self.provider,
            "output": self.output,
            "error": self.error,
            "extensions": self.extensions,
        }

    @classmethod
    def from_dict(cls, value: Dict[str, Any]) -> "CycleArtifact":
        if value.get("schema_version") == CYCLE_SCHEMA_VERSION:
            return cls(
                cycle_id=value["cycle_id"],
                status=value["status"],
                created_at=value["created_at"],
                completed_at=value["completed_at"],
                duration_ms=int(value["duration_ms"]),
                input=value.get("input", {}),
                config=value.get("config", {}),
                provider=value.get("provider", {}),
                output=value.get("output", {}),
                error=value.get("error"),
                extensions=value.get("extensions", {}),
            )
        return cls.from_legacy_dict(value)

    @classmethod
    def from_legacy_dict(cls, value: Dict[str, Any]) -> "CycleArtifact":
        """Read the pre-S3 JSONL shape without pretending it was schema v1."""
        meta = value.get("meta", {})
        timestamp = datetime.fromtimestamp(
            int(meta.get("ts", 0)), tz=timezone.utc
        ).isoformat(timespec="seconds").replace("+00:00", "Z")
        return cls(
            cycle_id=value["cycle_id"],
            status=value.get("status", "succeeded"),
            created_at=timestamp,
            completed_at=timestamp,
            duration_ms=int(meta.get("latency_ms", 0)),
            input=value.get("input", {}),
            config=value.get("config", {}),
            provider=meta.get("provider", {}),
            output=value.get("output", {}),
            error=value.get("error"),
            schema_version="mind.cycle/legacy",
            extensions={"legacy_meta": meta},
        )


CycleRecord = CycleArtifact


@dataclass(frozen=True)
class RunResult:
    cycle_id: str
    reply: str
