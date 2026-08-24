import sqlite3
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from nemosine_mind import MindConfig
from nemosine_mind.cli import main
from nemosine_mind.core import sqlite_registry
from nemosine_mind.core.models import CycleArtifact
from nemosine_mind.core.registry import JsonlRegistry
from nemosine_mind.core.sqlite_registry import SQLiteRegistry
from nemosine_mind.main import create_app
from nemosine_mind.providers.mock import MockProvider
from nemosine_mind.runtime import build_runtime


@pytest.fixture
def valid_artifact():
    return CycleArtifact(
        cycle_id="cycle-test",
        status="succeeded",
        created_at="2026-08-23T00:00:00.000Z",
        completed_at="2026-08-23T00:00:00.001Z",
        duration_ms=1,
        input={"text": "hello"},
        config={},
        provider={"name": "mock", "model": "mind-mock-1"},
        output={"text": "reply"},
    )


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"cycle_id": ""}, "cycle_id is required"),
        ({"status": "pending"}, "status must be"),
        ({"duration_ms": -1}, "duration_ms must be non-negative"),
        ({"created_at": "2026-08-23"}, "timestamps must be UTC"),
    ],
)
def test_cycle_artifact_rejects_invalid_audit_data(valid_artifact, changes, message):
    with pytest.raises(ValueError, match=message):
        replace(valid_artifact, **changes)


def test_cli_reports_empty_history_and_missing_cycle(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_PROVIDER", "mock")

    assert main(["cycles"]) == 0
    assert "No cycles found." in capsys.readouterr().out

    assert main(["cycles", "missing-cycle"]) == 1
    assert "Cycle not found" in capsys.readouterr().err


def test_cli_rejects_invalid_storage_configuration(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_STORAGE", "unknown")

    assert main(["cycles"]) == 1
    assert "MIND_STORAGE must be" in capsys.readouterr().err


def test_http_api_validates_requests_and_missing_cycles(tmp_path):
    client = TestClient(
        create_app(
            config=MindConfig(),
            provider=MockProvider(),
            registry=JsonlRegistry(str(tmp_path / "cycles.jsonl")),
        )
    )

    assert client.post("/v1/interactions", json={"text": "   "}).status_code == 400
    assert client.get("/v1/cycles/missing-cycle").status_code == 404
    invalid_page = client.get("/v1/cycles", params={"limit": 0})
    assert invalid_page.status_code == 400
    assert "limit must be" in invalid_page.json()["detail"]


def test_dependency_injection_rejects_ambiguous_runtime(tmp_path):
    provider = MockProvider()
    store = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    runtime = build_runtime(provider=provider, registry=store)

    with pytest.raises(ValueError, match="runtime or individual dependencies"):
        create_app(runtime=runtime, provider=provider)

    with pytest.raises(ValueError, match="provider or legacy motor"):
        build_runtime(provider=provider, motor=provider, registry=store)


def test_sqlite_store_closes_every_connection(tmp_path, monkeypatch, valid_artifact):
    opened_connections = []
    original_connect = sqlite_registry.sqlite3.connect

    def tracked_connect(*args, **kwargs):
        connection = original_connect(*args, **kwargs)
        opened_connections.append(connection)
        return connection

    monkeypatch.setattr(sqlite_registry.sqlite3, "connect", tracked_connect)
    store = SQLiteRegistry(str(tmp_path / "cycles.sqlite3"))

    store.append(valid_artifact)
    assert store.get(valid_artifact.cycle_id) is not None
    assert store.list(limit=1)[0]["cycle_id"] == valid_artifact.cycle_id

    assert opened_connections
    for connection in opened_connections:
        with pytest.raises(sqlite3.ProgrammingError, match="closed database"):
            connection.execute("SELECT 1")
