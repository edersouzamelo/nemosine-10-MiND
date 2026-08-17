from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import __version__
from .ame.config import load_config
from .ame.orchestrator import Orchestrator
from .ame.motor_openai import OpenAIMotor
from .ame.registry import JsonlRegistry

class Message(BaseModel):
    text: str


def default_registry_path() -> str:
    configured = os.getenv("MIND_DATA_DIR")
    if configured:
        data_dir = Path(configured).expanduser()
    elif os.name == "nt" and os.getenv("LOCALAPPDATA"):
        data_dir = Path(os.environ["LOCALAPPDATA"]) / "MiND"
    else:
        data_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "mind"
    return str(data_dir / "cycles.jsonl")


def create_app(
    *,
    config=None,
    motor: Optional[OpenAIMotor] = None,
    registry: Optional[JsonlRegistry] = None,
) -> FastAPI:
    """Build the HTTP adapter with explicitly replaceable runtime dependencies."""
    active_config = config or load_config()
    active_registry = registry or JsonlRegistry(default_registry_path())
    active_motor = motor or OpenAIMotor(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        model=os.getenv("OPENAI_MODEL", active_config.model),
    )
    orchestrator = Orchestrator(
        config=active_config,
        motor=active_motor,
        registry=active_registry,
    )

    application = FastAPI(
        title="MiND — Minimal Deterministic Middleware",
        version=__version__,
    )
    application.state.config = active_config
    application.state.registry = active_registry
    application.state.motor = active_motor
    application.state.orchestrator = orchestrator

    @application.get("/health")
    def health():
        return {"ok": True, "version": application.version}

    @application.get("/ame/config")
    def get_config():
        return active_config.to_public_dict()

    @application.get("/ame/last")
    def last_cycle():
        return {"last": active_registry.read_last()}

    @application.post("/chat")
    def chat(message: Message):
        if not message.text or not message.text.strip():
            raise HTTPException(status_code=400, detail="Empty message")
        if not active_motor.is_configured():
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        result = orchestrator.run(user_text=message.text)
        return {"reply": result.reply, "cycle_id": result.cycle_id}

    return application


app = create_app()
