from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .core.config import MindConfig, load_config
from .core.orchestrator import Orchestrator
from .core.registry import CycleStore, JsonlRegistry
from .core.sqlite_registry import SQLiteRegistry
from .providers.base import Provider
from .providers.factory import create_provider


def default_registry_path() -> str:
    """Return a writable user-data path, never a path inside the package."""
    configured = os.getenv("MIND_DATA_DIR")
    if configured:
        data_dir = Path(configured).expanduser()
    elif os.name == "nt" and os.getenv("LOCALAPPDATA"):
        data_dir = Path(os.environ["LOCALAPPDATA"]) / "MiND"
    else:
        xdg_data_home = os.getenv("XDG_DATA_HOME")
        data_dir = (
            Path(xdg_data_home).expanduser()
            if xdg_data_home
            else Path.home() / ".local" / "share"
        ) / "mind"
    return str(data_dir / "cycles.jsonl")


def default_sqlite_path() -> str:
    return str(Path(default_registry_path()).with_name("cycles.sqlite3"))


def build_store() -> CycleStore:
    backend = os.getenv("MIND_STORAGE", "jsonl").strip().lower()
    if backend == "jsonl":
        return JsonlRegistry(default_registry_path())
    if backend == "sqlite":
        return SQLiteRegistry(default_sqlite_path())
    raise ValueError("MIND_STORAGE must be 'jsonl' or 'sqlite'")


@dataclass(frozen=True)
class MindRuntime:
    """Runtime dependencies shared by the Python core and transport adapters."""

    config: MindConfig
    provider: Provider
    registry: CycleStore
    orchestrator: Orchestrator


def build_runtime(
    *,
    config: Optional[MindConfig] = None,
    provider: Optional[Provider] = None,
    motor: Optional[Provider] = None,
    registry: Optional[CycleStore] = None,
) -> MindRuntime:
    if provider is not None and motor is not None:
        raise ValueError("Pass provider or legacy motor, not both")
    active_config = config or load_config()
    active_registry = registry or build_store()
    active_provider = provider or motor or create_provider(active_config)
    return MindRuntime(
        config=active_config,
        provider=active_provider,
        registry=active_registry,
        orchestrator=Orchestrator(
            config=active_config,
            provider=active_provider,
            registry=active_registry,
        ),
    )
