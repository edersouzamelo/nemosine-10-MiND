from __future__ import annotations

from typing import Any, Dict, List, Optional

from .base import ProviderConfigurationError, ProviderError, ProviderResult


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        client: Optional[Any] = None,
    ):
        if not model:
            raise ProviderConfigurationError(
                "openai", "missing_model", "OpenAI model is not configured"
            )
        self._model = model
        if client is not None:
            self._client = client
        elif api_key:
            from openai import OpenAI

            self._client = OpenAI(api_key=api_key)
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
                "openai", "missing_api_key", "OpenAI API key is not configured"
            )
        try:
            completion = self._client.chat.completions.create(
                model=self.model,
                temperature=temperature,
                max_tokens=max_output_tokens,
                messages=messages,
            )
        except Exception as exc:
            raise ProviderError(
                "openai",
                "request_failed",
                "OpenAI request failed",
                retryable=True,
            ) from exc
        choice = completion.choices[0]
        usage = getattr(completion, "usage", None)
        return ProviderResult(
            text=choice.message.content or "",
            request_id=getattr(completion, "id", None),
            finish_reason=getattr(choice, "finish_reason", None),
            usage={
                key: value
                for key in ("prompt_tokens", "completion_tokens", "total_tokens")
                if (value := getattr(usage, key, None)) is not None
            },
        )
