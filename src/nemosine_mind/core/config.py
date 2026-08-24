from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from typing import Any, Dict

from .._version import __version__

DEFAULT_SYSTEM_TEMPLATE = (
    "You are operating through MiND, an auditable LLM interaction middleware.\n"
    "Rules for this interaction:\n"
    "1) Follow the externally supplied configuration.\n"
    "2) Answer the user request directly.\n"
    "3) Do not invent capabilities or unavailable context.\n"
)


@dataclass(frozen=True)
class MindConfig:
    version: str = __version__
    mode: str = "mind"
    provider: str = "mock"
    model: str = "mind-mock-1"
    temperature: float = 0.2
    max_output_tokens: int = 700
    system_template: str = DEFAULT_SYSTEM_TEMPLATE

    def to_public_dict(self) -> Dict[str, Any]:
        return asdict(self)


def load_config() -> MindConfig:
    provider = os.getenv("MIND_PROVIDER", "mock").strip().lower()
    provider_model_env = {
        "openai": "OPENAI_MODEL",
        "anthropic": "ANTHROPIC_MODEL",
    }.get(provider)
    model = os.getenv("MIND_MODEL")
    if not model and provider_model_env:
        model = os.getenv(provider_model_env)
    if not model:
        model = "mind-mock-1" if provider == "mock" else ""
    return MindConfig(
        provider=provider,
        model=model,
        temperature=float(
            os.getenv("MIND_TEMPERATURE", os.getenv("OPENAI_TEMPERATURE", "0.2"))
        ),
        max_output_tokens=int(
            os.getenv(
                "MIND_MAX_OUTPUT_TOKENS",
                os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700"),
            )
        ),
        system_template=os.getenv("MIND_SYSTEM_TEMPLATE", DEFAULT_SYSTEM_TEMPLATE),
    )
