import json

from fastapi.testclient import TestClient

from nemosine_mind import Mind, MindConfig
from nemosine_mind.cli import main
from nemosine_mind.core.registry import JsonlRegistry
from nemosine_mind.core.sqlite_registry import SQLiteRegistry
from nemosine_mind.main import create_app
from nemosine_mind.providers.mock import MockProvider


def test_public_python_api_runs_and_inspects_cycle(tmp_path):
    store = SQLiteRegistry(str(tmp_path / "cycles.sqlite3"))
    mind = Mind.create(config=MindConfig(), provider=MockProvider(), store=store)

    result = mind.run("hello from python api")

    assert result.reply == "[mock:mind-mock-1] hello from python api"
    assert mind.get_cycle(result.cycle_id)["cycle_id"] == result.cycle_id
    assert mind.list_cycles(limit=1)[0]["cycle_id"] == result.cycle_id


def test_cli_demo_is_offline_and_emits_cycle_id(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    exit_code = main(["demo", "offline hello"])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "[mock:mind-mock-1] offline hello" in output
    assert "cycle_id:" in output
    assert (
        JsonlRegistry(str(tmp_path / "cycles.jsonl")).read_last()["status"]
        == "succeeded"
    )


def test_cli_run_json_returns_artifact(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_PROVIDER", "mock")

    exit_code = main(["run", "json hello", "--json"])

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["reply"] == "[mock:mind-mock-1] json hello"
    assert payload["artifact"]["cycle_id"] == payload["cycle_id"]


def test_cli_cycles_lists_and_reads_cycle(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_PROVIDER", "mock")
    main(["demo", "history"])
    cycle_id = JsonlRegistry(str(tmp_path / "cycles.jsonl")).read_last()["cycle_id"]
    capsys.readouterr()

    assert main(["cycles", "--json"]) == 0
    history = json.loads(capsys.readouterr().out)
    assert history["cycles"][0]["cycle_id"] == cycle_id

    assert main(["cycles", cycle_id]) == 0
    detail = json.loads(capsys.readouterr().out)
    assert detail["cycle_id"] == cycle_id


def test_cli_doctor_reports_healthy_offline_setup(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_PROVIDER", "mock")

    exit_code = main(["doctor", "--storage", "sqlite", "--json"])

    report = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert report["ok"] is True
    assert report["provider"] == "mock"
    assert report["checks"]["storage"]["value"] == "sqlite"


def test_cli_accepts_data_directory_without_environment_setup(tmp_path, monkeypatch):
    monkeypatch.delenv("MIND_DATA_DIR", raising=False)
    monkeypatch.setenv("MIND_PROVIDER", "mock")

    exit_code = main(["demo", "portable", "--data-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "cycles.jsonl").exists()


def test_cli_migrates_jsonl_to_sqlite(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("MIND_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("MIND_PROVIDER", "mock")
    main(["demo", "migrate me"])
    capsys.readouterr()
    source = tmp_path / "cycles.jsonl"
    target = tmp_path / "migrated.sqlite3"

    exit_code = main(
        [
            "migrate",
            "--from-jsonl",
            str(source),
            "--to-sqlite",
            str(target),
            "--json",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["migrated"] == 1
    assert SQLiteRegistry(str(target)).read_last()["input"]["text"] == "migrate me"


def test_versioned_http_api_and_legacy_aliases_share_runtime(tmp_path):
    store = SQLiteRegistry(str(tmp_path / "cycles.sqlite3"))
    client = TestClient(
        create_app(config=MindConfig(), provider=MockProvider(), registry=store)
    )

    created = client.post("/v1/interactions", json={"text": "hello"})

    assert created.status_code == 200
    payload = created.json()
    assert payload["artifact"]["cycle_id"] == payload["cycle_id"]
    assert client.get("/v1/health").status_code == 200
    assert client.get("/v1/config").json()["provider"] == "mock"
    assert (
        client.get("/v1/cycles").json()["cycles"][0]["cycle_id"] == payload["cycle_id"]
    )
    assert client.get(f"/v1/cycles/{payload['cycle_id']}").status_code == 200
    assert client.post("/chat", json={"text": "legacy"}).status_code == 200


def test_openapi_exposes_only_stable_v1_routes(tmp_path):
    client = TestClient(
        create_app(
            config=MindConfig(),
            provider=MockProvider(),
            registry=JsonlRegistry(str(tmp_path / "cycles.jsonl")),
        )
    )

    paths = client.get("/openapi.json").json()["paths"]

    assert "/v1/interactions" in paths
    assert "/v1/cycles" in paths
    assert "/chat" not in paths
    assert "/ame/config" not in paths
