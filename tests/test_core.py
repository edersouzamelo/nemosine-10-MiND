import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from nemosine_mind import __version__
from nemosine_mind.core.config import MindConfig
from nemosine_mind.core.models import CYCLE_SCHEMA_VERSION, CycleArtifact
from nemosine_mind.core.orchestrator import Orchestrator
from nemosine_mind.core.registry import JsonlRegistry, migrate_cycles
from nemosine_mind.core.sqlite_registry import SQLiteRegistry
from nemosine_mind.main import create_app
from nemosine_mind.providers.anthropic import AnthropicProvider
from nemosine_mind.providers.base import (
    ProviderConfigurationError,
    ProviderError,
    ProviderResult,
)
from nemosine_mind.providers.factory import create_provider
from nemosine_mind.providers.mock import MockProvider
from nemosine_mind.providers.openai import OpenAIProvider
from nemosine_mind.runtime import build_runtime, default_registry_path


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
        "message": "Unexpected provider failure",
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

    assert config.version == __version__
    assert config.mode == "mind"
    assert "Nemosine" not in config.system_template
    assert "AME" not in config.system_template


def test_provider_neutral_environment_controls_runtime(monkeypatch):
    monkeypatch.setenv("MIND_TEMPERATURE", "0.6")
    monkeypatch.setenv("MIND_MAX_OUTPUT_TOKENS", "321")
    monkeypatch.setenv("MIND_SYSTEM_TEMPLATE", "custom neutral template")

    from nemosine_mind.core.config import load_config

    config = load_config()

    assert config.temperature == 0.6
    assert config.max_output_tokens == 321
    assert config.system_template == "custom neutral template"


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
    assert provider.generate(**arguments).text == "[mock:mind-mock-1] hello"


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
            usage = type(
                "Usage",
                (),
                {"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
            )()
            choice.finish_reason = "stop"
            return type(
                "Completion",
                (),
                {"id": "openai-request", "choices": [choice], "usage": usage},
            )()

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

    assert reply == ProviderResult(
        text="openai reply",
        request_id="openai-request",
        finish_reason="stop",
        usage={"prompt_tokens": 2, "completion_tokens": 3, "total_tokens": 5},
    )
    assert completions.arguments["model"] == "openai-test"
    assert completions.arguments["max_tokens"] == 100


def test_anthropic_adapter_maps_system_and_conversation():
    class Messages:
        def create(self, **kwargs):
            self.arguments = kwargs
            block = type("Block", (), {"type": "text", "text": "anthropic reply"})()
            usage = type("Usage", (), {"input_tokens": 4, "output_tokens": 6})()
            return type(
                "Response",
                (),
                {
                    "id": "anthropic-request",
                    "content": [block],
                    "stop_reason": "end_turn",
                    "usage": usage,
                },
            )()

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

    assert reply == ProviderResult(
        text="anthropic reply",
        request_id="anthropic-request",
        finish_reason="end_turn",
        usage={"input_tokens": 4, "output_tokens": 6},
    )
    assert messages_api.arguments["system"] == "system rules"
    assert messages_api.arguments["messages"] == [{"role": "user", "content": "hello"}]


def test_provider_metadata_is_written_to_cycle(tmp_path):
    class MetadataProvider(StubProvider):
        def generate(self, **kwargs):
            return ProviderResult(
                text="reply",
                request_id="request-123",
                finish_reason="stop",
                usage={"input_tokens": 7, "output_tokens": 3},
            )

    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    orchestrator = Orchestrator(
        config=MindConfig(), provider=MetadataProvider(), registry=registry
    )

    orchestrator.run("hello")

    assert registry.read_last()["provider"] == {
        "name": "stub",
        "model": "stub-1",
        "request_id": "request-123",
        "finish_reason": "stop",
        "usage": {"input_tokens": 7, "output_tokens": 3},
    }


def test_provider_errors_are_safe_and_structured_in_audit(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    error = ProviderError(
        "openai", "request_failed", "OpenAI request failed", retryable=True
    )
    orchestrator = Orchestrator(
        config=MindConfig(),
        provider=StubProvider(error=error),
        registry=registry,
    )

    with pytest.raises(ProviderError):
        orchestrator.run("hello")

    assert registry.read_last()["error"] == {
        "type": "ProviderError",
        "provider": "openai",
        "code": "request_failed",
        "message": "OpenAI request failed",
        "retryable": True,
    }


@pytest.mark.parametrize(
    ("provider", "key_code"),
    [
        (OpenAIProvider(api_key="", model="openai-test"), "missing_api_key"),
        (AnthropicProvider(api_key="", model="anthropic-test"), "missing_api_key"),
    ],
)
def test_unconfigured_real_provider_has_normalized_error(provider, key_code):
    with pytest.raises(ProviderConfigurationError) as captured:
        provider.generate(
            messages=[{"role": "user", "content": "hello"}],
            temperature=0.2,
            max_output_tokens=100,
        )

    assert captured.value.code == key_code


def make_artifact(cycle_id, created_at="2026-08-17T12:00:00.000Z"):
    return CycleArtifact(
        cycle_id=cycle_id,
        status="succeeded",
        created_at=created_at,
        completed_at=created_at,
        duration_ms=1,
        input={"text": cycle_id},
        config={},
        provider={"name": "mock", "model": "mind-mock-1"},
        output={"text": "reply"},
    )


def test_cycle_artifact_v1_is_written_with_utc_timestamps(tmp_path):
    registry = JsonlRegistry(str(tmp_path / "cycles.jsonl"))
    result = Orchestrator(
        config=MindConfig(), provider=StubProvider(), registry=registry
    ).run("hello")

    artifact = registry.get(result.cycle_id)

    assert artifact["schema_version"] == CYCLE_SCHEMA_VERSION
    assert artifact["created_at"].endswith("Z")
    assert artifact["completed_at"].endswith("Z")
    assert artifact["duration_ms"] >= 0
    assert "meta" not in artifact


def test_jsonl_reads_legacy_records_and_marks_them_as_legacy(tmp_path):
    path = tmp_path / "cycles.jsonl"
    path.write_text(
        json.dumps(
            {
                "cycle_id": "legacy-1",
                "input": {"text": "old"},
                "config": {},
                "output": {"text": "reply"},
                "meta": {"ts": 1, "latency_ms": 12},
                "status": "succeeded",
                "error": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    artifact = JsonlRegistry(str(path)).get("legacy-1")

    assert artifact["schema_version"] == "mind.cycle/legacy"
    assert artifact["duration_ms"] == 12
    assert artifact["extensions"]["legacy_meta"]["ts"] == 1


def test_jsonl_ignores_only_an_incomplete_final_line(tmp_path):
    path = tmp_path / "cycles.jsonl"
    registry = JsonlRegistry(str(path))
    registry.append(make_artifact("complete"))
    with path.open("a", encoding="utf-8") as file:
        file.write('{"cycle_id":"partial"')

    assert [item["cycle_id"] for item in registry.list()] == ["complete"]


@pytest.mark.parametrize("store_type", [JsonlRegistry, SQLiteRegistry])
def test_cycle_stores_support_get_and_paginated_history(tmp_path, store_type):
    suffix = "jsonl" if store_type is JsonlRegistry else "sqlite3"
    store = store_type(str(tmp_path / f"cycles.{suffix}"))
    store.append(make_artifact("one", "2026-08-17T12:00:00.000Z"))
    store.append(make_artifact("two", "2026-08-17T12:00:01.000Z"))
    store.append(make_artifact("three", "2026-08-17T12:00:02.000Z"))

    assert store.get("two")["input"] == {"text": "two"}
    assert [item["cycle_id"] for item in store.list(limit=2)] == ["three", "two"]
    assert [item["cycle_id"] for item in store.list(limit=1, offset=2)] == ["one"]
    assert store.get("missing") is None


@pytest.mark.parametrize("store_type", [JsonlRegistry, SQLiteRegistry])
def test_cycle_stores_accept_concurrent_appends(tmp_path, store_type):
    suffix = "jsonl" if store_type is JsonlRegistry else "sqlite3"
    store = store_type(str(tmp_path / f"concurrent.{suffix}"))

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda number: store.append(make_artifact(str(number))), range(12)
            )
        )

    assert len(store.list(limit=50)) == 12


def test_http_exposes_cycle_history_and_cycle_by_id(tmp_path):
    registry = SQLiteRegistry(str(tmp_path / "cycles.sqlite3"))
    client = TestClient(
        create_app(config=MindConfig(), provider=StubProvider(), registry=registry)
    )
    created = client.post("/chat", json={"text": "hello"}).json()

    detail = client.get(f"/cycles/{created['cycle_id']}")
    history = client.get("/cycles?limit=1&offset=0")

    assert detail.status_code == 200
    assert detail.json()["schema_version"] == CYCLE_SCHEMA_VERSION
    assert history.status_code == 200
    assert history.json()["cycles"][0]["cycle_id"] == created["cycle_id"]
    assert client.get("/cycles/missing").status_code == 404


def test_runtime_selects_sqlite_storage(tmp_path, monkeypatch):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_STORAGE", "sqlite")

    runtime = build_runtime(config=MindConfig(), provider=StubProvider())

    assert isinstance(runtime.registry, SQLiteRegistry)
    assert runtime.registry.path == str(tmp_path / "cycles.sqlite3")


def test_legacy_jsonl_can_be_migrated_to_sqlite(tmp_path):
    jsonl_path = tmp_path / "legacy.jsonl"
    jsonl_path.write_text(
        json.dumps(
            {
                "cycle_id": "legacy-to-sqlite",
                "input": {"text": "old"},
                "config": {},
                "output": {"text": "reply"},
                "meta": {"ts": 1, "latency_ms": 12},
                "status": "succeeded",
                "error": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    source = JsonlRegistry(str(jsonl_path))
    target = SQLiteRegistry(str(tmp_path / "cycles.sqlite3"))

    copied = migrate_cycles(source, target)

    assert copied == 1
    assert target.get("legacy-to-sqlite")["schema_version"] == "mind.cycle/legacy"
