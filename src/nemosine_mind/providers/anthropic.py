from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import ProviderConfigurationError, ProviderError, ProviderResult


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
            raise ProviderConfigurationError(
                "anthropic", "missing_model", "Anthropic model is not configured"
            )
        self._model = model
        if client is not None:
            self._client = client
        elif api_key:
            try:
                from anthropic import Anthropic
            except ImportError as exc:
                raise ProviderConfigurationError(
                    "anthropic",
                    "missing_dependency",
                    "Install nemosine-mind[anthropic] to use Anthropic",
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
    ) -> ProviderResult:
        if self._client is None:
            raise ProviderConfigurationError(
                "anthropic", "missing_api_key", "Anthropic API key is not configured"
            )

        system_parts = [
            message["content"] for message in messages if message["role"] == "system"
        ]
        conversation = [
            message for message in messages if message["role"] in {"user", "assistant"}
        ]
        try:
            response = self._client.messages.create(
                model=self.model,
                system="\n\n".join(system_parts),
                messages=conversation,
                temperature=temperature,
                max_tokens=max_output_tokens,
            )
        except Exception as exc:
            raise ProviderError(
                "anthropic",
                "request_failed",
                "Anthropic request failed",
                retryable=True,
            ) from exc
        usage = getattr(response, "usage", None)
        return ProviderResult(
            text="".join(
                block.text
                for block in response.content
                if getattr(block, "type", "") == "text"
            ),
            request_id=getattr(response, "id", None),
            finish_reason=getattr(response, "stop_reason", None),
            usage={
                key: value
                for key in ("input_tokens", "output_tokens")
                if (value := getattr(usage, key, None)) is not None
            },
        )
