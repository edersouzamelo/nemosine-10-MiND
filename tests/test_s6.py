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
    assert "--accent: #00a88f" in stylesheet.text
    assert script.status_code == 200
    assert 'request("/v1/interactions"' in script.text
    assert 'panelName === "llm"' in script.text
    assert 'panelName === "export"' in script.text
    assert 'panelName === "cleanup"' in script.text
    assert 'panelName === "backup"' in script.text
    assert logo.status_code == 200
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
