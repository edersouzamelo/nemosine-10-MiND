from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
import webbrowser
from dataclasses import replace
from pathlib import Path
from threading import Timer
from typing import Any, Dict, Optional, Sequence
from uuid import uuid4

from . import __version__
from .api import Mind
from .core.config import MindConfig, load_config
from .core.registry import JsonlRegistry, migrate_cycles
from .core.sqlite_registry import SQLiteRegistry
from .runtime import build_store, default_registry_path, default_sqlite_path


def _print(value: Any, *, as_json: bool = False) -> None:
    if as_json:
        print(json.dumps(value, ensure_ascii=False, indent=2))
    else:
        print(value)


def _nearest_existing_parent(path: Path) -> Path:
    candidate = path
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    return candidate


def _add_runtime_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--storage", choices=("jsonl", "sqlite"))
    parser.add_argument("--data-dir")


def _apply_runtime_options(args: argparse.Namespace) -> Dict[str, Optional[str]]:
    previous = {
        "MIND_STORAGE": os.environ.get("MIND_STORAGE"),
        "MIND_DATA_DIR": os.environ.get("MIND_DATA_DIR"),
    }
    if getattr(args, "storage", None):
        os.environ["MIND_STORAGE"] = args.storage
    if getattr(args, "data_dir", None):
        os.environ["MIND_DATA_DIR"] = args.data_dir
    return previous


def _restore_runtime_options(previous: Dict[str, Optional[str]]) -> None:
    for name, value in previous.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def _config_from_args(
    args: argparse.Namespace, *, force_mock: bool = False
) -> MindConfig:
    config = load_config()
    provider = "mock" if force_mock else (args.provider or config.provider)
    model = "mind-mock-1" if force_mock else (args.model or config.model)
    if provider != config.provider and args.model is None and provider != "mock":
        model = ""
    if provider == "mock" and not model:
        model = "mind-mock-1"
    return replace(config, provider=provider, model=model)


def _run(args: argparse.Namespace, *, demo: bool = False) -> int:
    config = _config_from_args(args, force_mock=demo)
    try:
        mind = Mind.create(config=config)
        result = mind.run(args.text)
    except (RuntimeError, ValueError) as exc:
        print(f"MiND error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        _print(
            {
                "cycle_id": result.cycle_id,
                "reply": result.reply,
                "artifact": mind.get_cycle(result.cycle_id),
            },
            as_json=True,
        )
    else:
        print(result.reply)
        print(f"cycle_id: {result.cycle_id}")
    return 0


def _cycles(args: argparse.Namespace) -> int:
    try:
        store = build_store()
        if args.cycle_id:
            cycle = store.get(args.cycle_id)
            if cycle is None:
                print(f"Cycle not found: {args.cycle_id}", file=sys.stderr)
                return 1
            _print(cycle, as_json=True)
            return 0
        cycles = store.list(limit=args.limit, offset=args.offset)
    except (RuntimeError, ValueError) as exc:
        print(f"MiND error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        _print(
            {"cycles": cycles, "limit": args.limit, "offset": args.offset}, as_json=True
        )
    elif not cycles:
        print("No cycles found.")
    else:
        for cycle in cycles:
            provider = cycle.get("provider", {})
            print(
                f"{cycle['cycle_id']}  {cycle['status']:<9}  "
                f"{provider.get('name', '-')}/{provider.get('model', '-')}  "
                f"{cycle['created_at']}"
            )
    return 0


def _migrate(args: argparse.Namespace) -> int:
    source = JsonlRegistry(args.from_jsonl)
    target = SQLiteRegistry(args.to_sqlite)
    try:
        count = migrate_cycles(source, target)
    except RuntimeError as exc:
        print(f"Migration failed: {exc}", file=sys.stderr)
        return 1
    result = {"migrated": count, "from": source.path, "to": target.path}
    _print(
        result if args.json else f"Migrated {count} cycle(s) to {target.path}",
        as_json=args.json,
    )
    return 0


def doctor_report() -> Dict[str, Any]:
    config = load_config()
    storage = os.getenv("MIND_STORAGE", "jsonl").strip().lower()
    path = default_sqlite_path() if storage == "sqlite" else default_registry_path()
    data_parent = Path(path).parent
    writable_parent = _nearest_existing_parent(data_parent)
    checks = {
        "python": {
            "ok": sys.version_info >= (3, 9),
            "value": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        },
        "storage": {"ok": storage in {"jsonl", "sqlite"}, "value": storage},
        "data_directory": {
            "ok": writable_parent.exists() and os.access(writable_parent, os.W_OK),
            "value": str(data_parent),
        },
        "model": {"ok": bool(config.model), "value": config.model or "not configured"},
    }
    if config.provider == "mock":
        checks["provider"] = {"ok": True, "value": "mock (offline)"}
    else:
        key_name = f"{config.provider.upper()}_API_KEY"
        checks["provider_sdk"] = {
            "ok": importlib.util.find_spec(config.provider) is not None,
            "value": config.provider,
        }
        checks["provider_key"] = {
            "ok": bool(os.getenv(key_name)),
            "value": f"{key_name} configured"
            if os.getenv(key_name)
            else f"{key_name} missing",
        }
    return {
        "ok": all(check["ok"] for check in checks.values()),
        "version": __version__,
        "provider": config.provider,
        "checks": checks,
    }


def _doctor(args: argparse.Namespace) -> int:
    report = doctor_report()
    if args.json:
        _print(report, as_json=True)
    else:
        print(f"MiND {report['version']} — doctor")
        for name, check in report["checks"].items():
            marker = "OK" if check["ok"] else "FAIL"
            print(f"[{marker}] {name}: {check['value']}")
    return 0 if report["ok"] else 1


def _serve(args: argparse.Namespace, *, open_browser: bool = False) -> int:
    try:
        import uvicorn
    except ImportError:
        extra = "ui" if open_browser else "http"
        print(
            f"Install nemosine-mind[{extra}] to use this command.",
            file=sys.stderr,
        )
        return 1
    if open_browser and not args.no_browser:
        url = f"http://{args.host}:{args.port}/?launch={uuid4().hex}"
        opener = Timer(0.8, webbrowser.open, args=(url,))
        opener.daemon = True
        opener.start()
    uvicorn.run("nemosine_mind.main:app", host=args.host, port=args.port, reload=False)
    return 0


def _add_server_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--host", default=os.getenv("MIND_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MIND_PORT", "8000")))
    _add_runtime_options(parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mind", description="MiND — auditable middleware for LLM interactions"
    )
    parser.add_argument("--version", action="version", version=f"MiND {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run one interaction")
    run.add_argument("text")
    run.add_argument("--provider", choices=("mock", "openai", "anthropic"))
    run.add_argument("--model")
    run.add_argument("--json", action="store_true")
    _add_runtime_options(run)
    run.set_defaults(handler=_run)

    demo = subparsers.add_parser(
        "demo", help="Run an offline deterministic demonstration"
    )
    demo.add_argument("text", nargs="?", default="Hello from MiND")
    demo.add_argument("--provider", help=argparse.SUPPRESS)
    demo.add_argument("--model", help=argparse.SUPPRESS)
    demo.add_argument("--json", action="store_true")
    _add_runtime_options(demo)
    demo.set_defaults(handler=lambda args: _run(args, demo=True))

    cycles = subparsers.add_parser("cycles", help="List or inspect Cycle Artifacts")
    cycles.add_argument("cycle_id", nargs="?")
    cycles.add_argument("--limit", type=int, default=20)
    cycles.add_argument("--offset", type=int, default=0)
    cycles.add_argument("--json", action="store_true")
    _add_runtime_options(cycles)
    cycles.set_defaults(handler=_cycles)

    migrate = subparsers.add_parser("migrate", help="Migrate JSONL cycles to SQLite")
    migrate.add_argument("--from-jsonl", required=True)
    migrate.add_argument("--to-sqlite", required=True)
    migrate.add_argument("--json", action="store_true")
    migrate.set_defaults(handler=_migrate)

    doctor = subparsers.add_parser("doctor", help="Check local MiND configuration")
    doctor.add_argument("--json", action="store_true")
    _add_runtime_options(doctor)
    doctor.set_defaults(handler=_doctor)

    serve = subparsers.add_parser("serve", help="Start the local HTTP API")
    _add_server_options(serve)
    serve.set_defaults(no_browser=True)
    serve.set_defaults(handler=_serve)

    ui = subparsers.add_parser("ui", help="Open the local visual interface")
    _add_server_options(ui)
    ui.add_argument(
        "--no-browser", action="store_true", help="Start without opening a browser"
    )
    ui.set_defaults(handler=lambda args: _serve(args, open_browser=True))
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if not arguments:
        arguments = ["ui"]
    args = build_parser().parse_args(arguments)
    previous = _apply_runtime_options(args)
    try:
        return int(args.handler(args))
    finally:
        _restore_runtime_options(previous)
