import json

import pytest
from fastapi.testclient import TestClient

from nemosine_mind import __version__
from nemosine_mind.ame.config import AMEConfig
from nemosine_mind.ame.orchestrator import Orchestrator
from nemosine_mind.ame.registry import JsonlRegistry
from nemosine_mind.main import create_app


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
