from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from . import __version__
from .core.config import MindConfig
from .core.registry import JsonlRegistry
from .providers.base import Provider
from .runtime import MindRuntime, build_runtime

class Message(BaseModel):
    text: str


def create_app(
    *,
    runtime: Optional[MindRuntime] = None,
    config: Optional[MindConfig] = None,
    provider: Optional[Provider] = None,
    motor: Optional[Provider] = None,
    registry: Optional[JsonlRegistry] = None,
) -> FastAPI:
    """Build the HTTP adapter around an explicitly replaceable core runtime."""
    if runtime is not None and any(
        item is not None for item in (config, provider, motor, registry)
    ):
        raise ValueError("Pass runtime or individual dependencies, not both")
    active_runtime = runtime or build_runtime(
        config=config,
        provider=provider,
        motor=motor,
        registry=registry,
    )

    application = FastAPI(
        title="MiND — Minimal Deterministic Middleware",
        version=__version__,
    )
    application.state.runtime = active_runtime

    @application.get("/health")
    def health():
        return {"ok": True, "version": application.version}

    @application.get("/ame/config")
    def get_config():
        return active_runtime.config.to_public_dict()

    @application.get("/ame/last")
    def last_cycle():
        return {"last": active_runtime.registry.read_last()}

    @application.post("/chat")
    def chat(message: Message):
        if not message.text or not message.text.strip():
            raise HTTPException(status_code=400, detail="Empty message")
        try:
            result = active_runtime.orchestrator.run(user_text=message.text)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail="Provider execution failed; inspect the cycle registry",
            ) from exc
        return {"reply": result.reply, "cycle_id": result.cycle_id}

    return application


app = create_app()
