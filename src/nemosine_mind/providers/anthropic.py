from __future__ import annotations

from typing import Any, Dict, List, Optional


class AnthropicProvider:
    name = "anthropic"

    def __init__(
        self,
        *,
        api_key: str,
        model: str,
        client: Optional[Any] = None,
    ):
        if not model:
            raise ValueError("A model is required for the Anthropic provider")
        self._model = model
        if client is not None:
            self._client = client
        elif api_key:
            try:
                from anthropic import Anthropic
            except ImportError as exc:
                raise RuntimeError(
                    "Install nemosine-mind[anthropic] to use Anthropic"
                ) from exc
            self._client = Anthropic(api_key=api_key)
        else:
            self._client = None

    @property
    def model(self) -> str:
        return self._model

    def generate(
        self,
        *,
        messages: List[Dict[str, str]],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        if self._client is None:
            raise RuntimeError("ANTHROPIC_API_KEY not configured")

        system_parts = [
            message["content"] for message in messages if message["role"] == "system"
        ]
        conversation = [
            message for message in messages if message["role"] in {"user", "assistant"}
        ]
        response = self._client.messages.create(
            model=self.model,
            system="\n\n".join(system_parts),
            messages=conversation,
            temperature=temperature,
            max_tokens=max_output_tokens,
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", "") == "text"
        )
