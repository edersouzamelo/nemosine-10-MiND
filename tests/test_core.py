import json

import pytest
from fastapi.testclient import TestClient

from nemosine_mind import __version__
from nemosine_mind.ame.config import AMEConfig
from nemosine_mind.ame.orchestrator import Orchestrator
from nemosine_mind.ame.registry import JsonlRegistry
from nemosine_mind.main import create_app
from nemosine_mind.runtime import build_runtime, default_registry_path


class StubMotor:
    def __init__(self, reply="stub reply", error=None):
        self.reply = reply
        self.error = error

    def is_configured(self):
        return True

    def generate(self, **kwargs):
        if self.error:
            raise self.error
        return self.reply


def test_http_app_uses_injected_dependencies(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    app = create_app(
        config=AMEConfig(),
        motor=StubMotor(),
        registry=registry,
    )
    client = TestClient(app)

    response = client.post("/chat", json={"text": "  hello  "})

    assert response.status_code == 200
    assert response.json()["reply"] == "stub reply"
    assert client.get("/health").json()["version"] == __version__
    record = registry.read_last()
    assert record["input"] == {"text": "hello"}
    assert record["status"] == "succeeded"
    assert record["error"] is None


def test_failed_provider_call_is_auditable(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    orchestrator = Orchestrator(
        config=AMEConfig(),
        motor=StubMotor(error=RuntimeError("provider unavailable")),
        registry=registry,
    )

    with pytest.raises(RuntimeError, match="provider unavailable"):
        orchestrator.run("hello")

    record = registry.read_last()
    assert record["status"] == "failed"
    assert record["output"] == {}
    assert record["error"] == {
        "type": "RuntimeError",
        "message": "provider unavailable",
    }


def test_http_failure_is_auditable_without_exposing_provider_error(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    app = create_app(
        config=AMEConfig(),
        motor=StubMotor(error=RuntimeError("secret provider detail")),
        registry=registry,
    )

    response = TestClient(app).post("/chat", json={"text": "hello"})

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Provider execution failed; inspect the cycle registry"
    )
    assert "secret provider detail" not in response.text
    assert registry.read_last()["status"] == "failed"


def test_registry_writes_valid_jsonl(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "nested" / "cycles.jsonl"))
    orchestrator = Orchestrator(
        config=AMEConfig(),
        motor=StubMotor(),
        registry=registry,
    )

    orchestrator.run("one")
    orchestrator.run("two")

    lines = (tmp_path / "nested" / "cycles.jsonl").read_text().splitlines()
    assert len(lines) == 2
    assert [json.loads(line)["input"]["text"] for line in lines] == ["one", "two"]


def test_runtime_is_independent_from_http_adapter(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    runtime = build_runtime(
        config=AMEConfig(),
        motor=StubMotor(reply="core reply"),
        registry=registry,
    )

    result = runtime.orchestrator.run("hello from python")

    assert result.reply == "core reply"
    assert registry.read_last()["input"]["text"] == "hello from python"


def test_registry_path_respects_configured_data_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))

    assert default_registry_path() == str(tmp_path / "cycles.jsonl")
