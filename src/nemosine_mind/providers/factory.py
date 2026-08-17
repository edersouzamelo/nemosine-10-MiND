from __future__ import annotations

import os

from nemosine_mind.core.config import MindConfig

from .anthropic import AnthropicProvider
from .base import Provider
from .mock import MockProvider
from .openai import OpenAIProvider


def create_provider(config: MindConfig) -> Provider:
    if config.provider == "mock":
        return MockProvider(model=config.model)
    if config.provider == "openai":
        return OpenAIProvider(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=config.model,
        )
    if config.provider == "anthropic":
        return AnthropicProvider(
            api_key=os.getenv("ANTHROPIC_API_KEY", ""),
            model=config.model,
        )
    raise ValueError(f"Unsupported provider: {config.provider}")
