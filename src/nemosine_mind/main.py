from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__
from .core.config import MindConfig
from .core.registry import CycleStore
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
    registry: Optional[CycleStore] = None,
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
    ui_directory = Path(__file__).resolve().parent / "ui"
    application.mount(
        "/ui/assets",
        StaticFiles(directory=str(ui_directory)),
        name="ui-assets",
    )

    @application.get("/", include_in_schema=False)
    @application.get("/ui", include_in_schema=False)
    def local_ui():
        return FileResponse(str(ui_directory / "index.html"))

    @application.get("/health", include_in_schema=False)
    @application.get("/v1/health")
    def health():
        return {"ok": True, "version": application.version}

    @application.get("/ame/config", include_in_schema=False)
    @application.get("/v1/config")
    def get_config():
        return active_runtime.config.to_public_dict()

    @application.get("/ame/last", include_in_schema=False)
    @application.get("/v1/cycles/last")
    def last_cycle():
        return {"last": active_runtime.registry.read_last()}

    @application.get("/cycles", include_in_schema=False)
    @application.get("/v1/cycles")
    def list_cycles(limit: int = 50, offset: int = 0):
        try:
            cycles = active_runtime.registry.list(limit=limit, offset=offset)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"cycles": cycles, "limit": limit, "offset": offset}

    @application.get("/cycles/{cycle_id}", include_in_schema=False)
    @application.get("/v1/cycles/{cycle_id}")
    def get_cycle(cycle_id: str):
        artifact = active_runtime.registry.get(cycle_id)
        if artifact is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return artifact

    @application.post("/chat", include_in_schema=False)
    @application.post("/v1/interactions")
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
        return {
            "reply": result.reply,
            "cycle_id": result.cycle_id,
            "artifact": active_runtime.registry.get(result.cycle_id),
        }

    return application


app = create_app()
