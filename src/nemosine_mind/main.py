from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import __version__
from .core.config import MindConfig
from .core.registry import CycleStore
from .providers.base import Provider
from .runtime import MindRuntime, build_runtime
from .settings import (
    DEFAULT_MODELS,
    SUPPORTED_PROVIDERS,
    provider_key_is_configured,
    save_local_settings,
    store_api_key,
)


class Message(BaseModel):
    text: str


class ProviderSettings(BaseModel):
    provider: str
    model: str = ""
    api_key: Optional[str] = None


def bundled_ui_directory() -> Path:
    """Resolve UI assets in normal Python and frozen Windows applications."""
    frozen_root = getattr(sys, "_MEIPASS", None)
    if frozen_root:
        return Path(frozen_root) / "nemosine_mind" / "ui"
    return Path(__file__).resolve().parent / "ui"


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
    ui_directory = bundled_ui_directory()

    def current_runtime() -> MindRuntime:
        return application.state.runtime

    @application.middleware("http")
    async def prevent_stale_local_ui(request: Request, call_next):
        response = await call_next(request)
        if request.url.path in {"/", "/ui"} or request.url.path.startswith(
            "/ui/assets/"
        ):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, max-age=0"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            response.headers["X-MiND-Version"] = __version__
        return response

    application.mount(
        "/ui/assets",
        StaticFiles(directory=str(ui_directory)),
        name="ui-assets",
    )

    @application.get("/", include_in_schema=False)
    @application.get("/ui", include_in_schema=False)
    def local_ui():
        # Render the application version into the shell so every installed
        # release receives versioned asset URLs.  This prevents a browser
        # profile from combining an older HTML shell with a newer backend.
        page = (ui_directory / "index.html").read_text(encoding="utf-8")
        return HTMLResponse(page.replace("__MIND_VERSION__", __version__))

    @application.get("/health", include_in_schema=False)
    @application.get("/v1/health")
    def health():
        return {
            "ok": True,
            "version": application.version,
            "ui_revision": "control-center-8",
        }

    @application.get("/ame/config", include_in_schema=False)
    @application.get("/v1/config")
    def get_config():
        return current_runtime().config.to_public_dict()

    @application.get("/v1/providers")
    def list_providers():
        runtime_now = current_runtime()
        return {
            "active": runtime_now.config.provider,
            "providers": [
                {
                    "name": name,
                    "model": (
                        runtime_now.config.model
                        if runtime_now.config.provider == name
                        else DEFAULT_MODELS[name]
                    ),
                    "key_configured": (
                        True if name == "mock" else provider_key_is_configured(name)
                    ),
                }
                for name in ("mock", "openai", "anthropic")
            ],
        }

    @application.put("/v1/providers/active")
    def activate_provider(settings: ProviderSettings):
        provider_name = settings.provider.strip().lower()
        if provider_name not in SUPPORTED_PROVIDERS:
            raise HTTPException(status_code=400, detail="Provider não suportado")
        model = settings.model.strip() or DEFAULT_MODELS[provider_name]
        if provider_name != "mock" and not model:
            raise HTTPException(status_code=400, detail="Informe o modelo")
        if settings.api_key is not None and settings.api_key.strip():
            try:
                store_api_key(provider_name, settings.api_key)
            except (OSError, ValueError) as exc:
                raise HTTPException(
                    status_code=500,
                    detail="Não foi possível proteger a chave neste computador",
                ) from exc
        if provider_name != "mock" and not provider_key_is_configured(provider_name):
            raise HTTPException(
                status_code=400,
                detail="Informe uma chave de API para este provider",
            )

        runtime_now = current_runtime()
        new_config = replace(
            runtime_now.config,
            provider=provider_name,
            model=model,
        )
        try:
            new_runtime = build_runtime(
                config=new_config,
                registry=runtime_now.registry,
            )
            save_local_settings(provider_name, model)
        except (ImportError, OSError, ValueError) as exc:
            raise HTTPException(
                status_code=500,
                detail="Não foi possível ativar este provider",
            ) from exc
        application.state.runtime = new_runtime
        return {
            "ok": True,
            "provider": provider_name,
            "model": model,
            "key_configured": provider_name == "mock"
            or provider_key_is_configured(provider_name),
        }

    @application.get("/ame/last", include_in_schema=False)
    @application.get("/v1/cycles/last")
    def last_cycle():
        return {"last": current_runtime().registry.read_last()}

    @application.get("/cycles", include_in_schema=False)
    @application.get("/v1/cycles")
    def list_cycles(limit: int = 50, offset: int = 0):
        try:
            cycles = current_runtime().registry.list(limit=limit, offset=offset)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"cycles": cycles, "limit": limit, "offset": offset}

    @application.get("/cycles/{cycle_id}", include_in_schema=False)
    @application.get("/v1/cycles/{cycle_id}")
    def get_cycle(cycle_id: str):
        artifact = current_runtime().registry.get(cycle_id)
        if artifact is None:
            raise HTTPException(status_code=404, detail="Cycle not found")
        return artifact

    @application.post("/chat", include_in_schema=False)
    @application.post("/v1/interactions")
    def chat(message: Message):
        if not message.text or not message.text.strip():
            raise HTTPException(status_code=400, detail="Empty message")
        try:
            runtime_now = current_runtime()
            result = runtime_now.orchestrator.run(user_text=message.text)
        except RuntimeError as exc:
            raise HTTPException(
                status_code=503,
                detail="Provider execution failed; inspect the cycle registry",
            ) from exc
        return {
            "reply": result.reply,
            "cycle_id": result.cycle_id,
            "artifact": runtime_now.registry.get(result.cycle_id),
        }

    return application


app = create_app()
