import json

import pytest
from fastapi.testclient import TestClient

from nemosine_mind import __version__
from nemosine_mind.core.config import MindConfig
from nemosine_mind.core.orchestrator import Orchestrator
from nemosine_mind.core.registry import JsonlRegistry
from nemosine_mind.main import create_app
from nemosine_mind.runtime import build_runtime, default_registry_path
from nemosine_mind.providers.anthropic import AnthropicProvider
from nemosine_mind.providers.factory import create_provider
from nemosine_mind.providers.mock import MockProvider
from nemosine_mind.providers.openai import OpenAIProvider


class StubProvider:
    name = "stub"
    model = "stub-1"

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
        config=MindConfig(),
        provider=StubProvider(),
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
        config=MindConfig(),
        provider=StubProvider(error=RuntimeError("provider unavailable")),
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
        config=MindConfig(),
        provider=StubProvider(error=RuntimeError("secret provider detail")),
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
        config=MindConfig(),
        provider=StubProvider(),
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
        config=MindConfig(),
        provider=StubProvider(reply="core reply"),
        registry=registry,
    )

    result = runtime.orchestrator.run("hello from python")

    assert result.reply == "core reply"
    assert registry.read_last()["input"]["text"] == "hello from python"


def test_registry_path_respects_configured_data_directory(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))

    assert default_registry_path() == str(tmp_path / "cycles.jsonl")


def test_default_core_configuration_is_nemosine_neutral():
    config = MindConfig()

    assert config.mode == "mind"
    assert "Nemosine" not in config.system_template
    assert "AME" not in config.system_template


def test_legacy_ame_imports_remain_compatible():
    from nemosine_mind.ame.config import AMEConfig
    from nemosine_mind.ame.orchestrator import Orchestrator as LegacyOrchestrator
    from nemosine_mind.ame.registry import JsonlRegistry as LegacyRegistry

    assert AMEConfig().mode == "AME"
    assert issubclass(LegacyOrchestrator, Orchestrator)
    assert LegacyRegistry is JsonlRegistry


def test_mock_provider_is_deterministic_and_offline():
    provider = MockProvider()
    arguments = {
        "messages": [{"role": "user", "content": "hello"}],
        "temperature": 0.9,
        "max_output_tokens": 1,
    }

    assert provider.generate(**arguments) == provider.generate(**arguments)
    assert provider.generate(**arguments) == "[mock:mind-mock-1] hello"


def test_runtime_defaults_to_mock_without_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MIND_PROVIDER", raising=False)

    runtime = build_runtime()
    result = runtime.orchestrator.run("offline demo")

    assert runtime.provider.name == "mock"
    assert result.reply == "[mock:mind-mock-1] offline demo"


def test_default_http_demo_works_without_api_key(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.delenv("MIND_PROVIDER", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    response = TestClient(create_app()).post("/chat", json={"text": "hello"})

    assert response.status_code == 200
    assert response.json()["reply"] == "[mock:mind-mock-1] hello"


def test_provider_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported provider"):
        create_provider(MindConfig(provider="unknown", model="model"))


def test_openai_adapter_maps_the_neutral_request():
    class Completions:
        def create(self, **kwargs):
            self.arguments = kwargs
            message = type("Message", (), {"content": "openai reply"})()
            choice = type("Choice", (), {"message": message})()
            return type("Completion", (), {"choices": [choice]})()

    completions = Completions()
    client = type(
        "Client",
        (),
        {"chat": type("Chat", (), {"completions": completions})()},
    )()
    provider = OpenAIProvider(api_key="", model="openai-test", client=client)

    reply = provider.generate(
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.2,
        max_output_tokens=100,
    )

    assert reply == "openai reply"
    assert completions.arguments["model"] == "openai-test"
    assert completions.arguments["max_tokens"] == 100


def test_anthropic_adapter_maps_system_and_conversation():
    class Messages:
        def create(self, **kwargs):
            self.arguments = kwargs
            block = type("Block", (), {"type": "text", "text": "anthropic reply"})()
            return type("Response", (), {"content": [block]})()

    messages_api = Messages()
    client = type("Client", (), {"messages": messages_api})()
    provider = AnthropicProvider(api_key="", model="anthropic-test", client=client)

    reply = provider.generate(
        messages=[
            {"role": "system", "content": "system rules"},
            {"role": "user", "content": "hello"},
        ],
        temperature=0.2,
        max_output_tokens=100,
    )

    assert reply == "anthropic reply"
    assert messages_api.arguments["system"] == "system rules"
    assert messages_api.arguments["messages"] == [
        {"role": "user", "content": "hello"}
    ]
