from fastapi.testclient import TestClient

from nemosine_mind import MindConfig, cli
from nemosine_mind.core.registry import JsonlRegistry
from nemosine_mind.main import create_app
from nemosine_mind.providers.mock import MockProvider


def build_client(tmp_path):
    return TestClient(
        create_app(
            config=MindConfig(),
            provider=MockProvider(),
            registry=JsonlRegistry(str(tmp_path / "cycles.jsonl")),
        )
    )


def test_local_ui_and_assets_are_served_from_package(tmp_path):
    client = build_client(tmp_path)

    page = client.get("/")
    alias = client.get("/ui")
    stylesheet = client.get("/ui/assets/styles.css")
    script = client.get("/ui/assets/app.js")
    logo = client.get("/ui/assets/mind-logo.svg")

    assert page.status_code == 200
    assert alias.status_code == 200
    assert "Central de interação auditável" in page.text
    assert "Monitoramento ativo" in page.text
    assert "Cycle Artifact" in page.text
    assert "Seletor de LLM" in page.text
    assert "Plug and Play" in page.text
    assert "Verificar atualizações" in page.text
    assert "Exportar dados" in page.text
    assert "Limpar dados" in page.text
    assert "Fazer backup" in page.text
    assert stylesheet.status_code == 200
    assert stylesheet.headers["cache-control"] == "no-store, max-age=0"
    assert "--accent: #00a88f" in stylesheet.text
    assert script.status_code == 200
    assert 'request("/v1/interactions"' in script.text
    assert 'panelName === "llm"' in script.text
    assert 'panelName === "export"' in script.text
    assert 'panelName === "cleanup"' in script.text
    assert 'panelName === "backup"' in script.text
    assert logo.status_code == 200
    assert logo.headers["cache-control"] == "no-store, max-age=0"
    assert 'aria-label="MiND"' in logo.text


def test_visual_flow_uses_real_cycle_api(tmp_path):
    client = build_client(tmp_path)

    created = client.post("/v1/interactions", json={"text": "visible audit"})
    cycle_id = created.json()["cycle_id"]
    history = client.get("/v1/cycles").json()["cycles"]
    detail = client.get(f"/v1/cycles/{cycle_id}").json()

    assert history[0]["cycle_id"] == cycle_id
    assert detail["input"]["text"] == "visible audit"
    assert detail["output"]["text"] == "[mock:mind-mock-1] visible audit"


def test_provider_status_never_exposes_api_key(tmp_path, monkeypatch):
    client = build_client(tmp_path)
    monkeypatch.setattr(
        "nemosine_mind.main.provider_key_is_configured",
        lambda provider: provider == "openai",
    )

    response = client.get("/v1/providers")

    assert response.status_code == 200
    assert response.json()["providers"][1]["key_configured"] is True
    assert "api_key" not in response.text
    assert "sk-" not in response.text


def test_openai_can_be_configured_without_persisting_plaintext_key(
    tmp_path, monkeypatch
):
    stored = {}
    client = build_client(tmp_path)
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(
        "nemosine_mind.main.store_api_key",
        lambda provider, secret: stored.update({provider: secret}),
    )
    monkeypatch.setattr(
        "nemosine_mind.main.provider_key_is_configured",
        lambda provider: provider in stored,
    )
    monkeypatch.setattr(
        "nemosine_mind.providers.factory.resolve_api_key",
        lambda provider: stored.get(provider, ""),
    )
    monkeypatch.setattr(
        "nemosine_mind.runtime.create_provider",
        lambda config: MockProvider(model=config.model),
    )

    response = client.put(
        "/v1/providers/active",
        json={
            "provider": "openai",
            "model": "gpt-5.4-mini",
            "api_key": "test-secret-not-a-real-key",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "provider": "openai",
        "model": "gpt-5.4-mini",
        "key_configured": True,
    }
    settings_text = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert "test-secret" not in settings_text
    assert "api_key" not in settings_text
    assert client.get("/v1/config").json()["provider"] == "openai"


def test_no_argument_cli_opens_ui_by_default(monkeypatch):
    calls = []

    def fake_serve(args, *, open_browser=False):
        calls.append((args.host, args.port, args.no_browser, open_browser))
        return 0

    monkeypatch.setattr(cli, "_serve", fake_serve)

    assert cli.main([]) == 0
    assert calls == [("127.0.0.1", 8000, False, True)]


def test_ui_command_can_start_without_opening_browser(monkeypatch):
    calls = []

    def fake_serve(args, *, open_browser=False):
        calls.append((args.no_browser, open_browser))
        return 0

    monkeypatch.setattr(cli, "_serve", fake_serve)

    assert cli.main(["ui", "--no-browser"]) == 0
    assert calls == [(True, True)]
