from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .ame.motor_openai import OpenAIMotor
from .core.config import MindConfig, load_config
from .core.orchestrator import Orchestrator, TextGenerator
from .core.registry import JsonlRegistry


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


@dataclass(frozen=True)
class MindRuntime:
    """Runtime dependencies shared by the Python core and transport adapters."""

    config: MindConfig
    motor: TextGenerator
    registry: JsonlRegistry
    orchestrator: Orchestrator


def build_runtime(
    *,
    config: Optional[MindConfig] = None,
    motor: Optional[TextGenerator] = None,
    registry: Optional[JsonlRegistry] = None,
) -> MindRuntime:
    active_config = config or load_config()
    active_registry = registry or JsonlRegistry(default_registry_path())
    active_motor = motor or OpenAIMotor(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", active_config.model),
    )
    return MindRuntime(
        config=active_config,
        motor=active_motor,
        registry=active_registry,
        orchestrator=Orchestrator(
            config=active_config,
            motor=active_motor,
            registry=active_registry,
        ),
    )
