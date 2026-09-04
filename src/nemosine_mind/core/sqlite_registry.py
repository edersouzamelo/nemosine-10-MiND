from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CycleArtifact


class SQLiteRegistry:
    """Small local SQLite store for addressable Cycle Artifacts."""

    def __init__(self, path: str):
        self.path = str(Path(path).expanduser())
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA busy_timeout=10000")
        return connection

    def _initialize(self) -> None:
        with closing(self._connect()) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS cycles ("
                "cycle_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, "
                "status TEXT NOT NULL, artifact_json TEXT NOT NULL)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_cycles_created_at "
                "ON cycles(created_at DESC, cycle_id DESC)"
            )

    def append(self, artifact: CycleArtifact) -> None:
        payload = json.dumps(
            artifact.to_dict(), ensure_ascii=False, separators=(",", ":")
        )
        try:
            with closing(self._connect()) as connection, connection:
                connection.execute(
                    "INSERT INTO cycles(cycle_id, created_at, status, artifact_json) "
                    "VALUES (?, ?, ?, ?)",
                    (artifact.cycle_id, artifact.created_at, artifact.status, payload),
                )
        except sqlite3.IntegrityError as exc:
            raise RuntimeError(f"Cycle already exists: {artifact.cycle_id}") from exc

    @staticmethod
    def _decode(payload: str) -> Dict[str, Any]:
        return CycleArtifact.from_dict(json.loads(payload)).to_dict()

    def get(self, cycle_id: str) -> Optional[Dict[str, Any]]:
        with closing(self._connect()) as connection:
            row = connection.execute(
                "SELECT artifact_json FROM cycles WHERE cycle_id = ?", (cycle_id,)
            ).fetchone()
        return self._decode(row[0]) if row else None

    def list(self, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        if limit < 1 or limit > 200 or offset < 0:
            raise ValueError("limit must be 1..200 and offset must be non-negative")
        with closing(self._connect()) as connection:
            rows = connection.execute(
                "SELECT artifact_json FROM cycles "
                "ORDER BY created_at DESC, cycle_id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        return [self._decode(row[0]) for row in rows]

    def read_last(self) -> Optional[Dict[str, Any]]:
        records = self.list(limit=1)
        return records[0] if records else None
