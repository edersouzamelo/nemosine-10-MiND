from __future__ import annotations

from nemosine_mind.core.config import MindConfig
from nemosine_mind.settings import resolve_api_key

from .anthropic import AnthropicProvider
from .base import Provider
from .mock import MockProvider
from .openai import OpenAIProvider


def create_provider(config: MindConfig) -> Provider:
    if config.provider == "mock":
        return MockProvider(model=config.model)
    if config.provider == "openai":
        return OpenAIProvider(
            api_key=resolve_api_key("openai"),
            model=config.model,
        )
    if config.provider == "anthropic":
        return AnthropicProvider(
            api_key=resolve_api_key("anthropic"),
            model=config.model,
        )
    raise ValueError(f"Unsupported provider: {config.provider}")
