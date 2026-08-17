from __future__ import annotations

from typing import Dict, List

from .base import ProviderResult


class MockProvider:
    """Offline deterministic provider for tests and demonstrations."""

    name = "mock"

    def __init__(self, model: str = "mind-mock-1"):
        self._model = model

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        *,
        messages: List[Dict[str, str]],
        temperature: float,
        max_output_tokens: int,
    ) -> ProviderResult:
        del temperature, max_output_tokens
        user_messages = [
            message["content"] for message in messages if message["role"] == "user"
        ]
        text = user_messages[-1] if user_messages else ""
        return ProviderResult(
            text=f"[mock:{self.model}] {text}",
            finish_reason="deterministic",
            usage={"input_messages": len(messages)},
        )
