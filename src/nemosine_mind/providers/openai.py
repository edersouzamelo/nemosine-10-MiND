from __future__ import annotations

from typing import Any, Dict, List, Optional


class OpenAIProvider:
    name = "openai"

    def __init__(
        self,
        api_key: str,
        model: str,
        client: Optional[Any] = None,
    ):
        if not model:
            raise ValueError("A model is required for the OpenAI provider")
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
    ) -> str:
        if self._client is None:
            raise RuntimeError("OPENAI_API_KEY not configured")
        completion = self._client.chat.completions.create(
            model=self.model,
            temperature=temperature,
            max_tokens=max_output_tokens,
            messages=messages,
        )
        return completion.choices[0].message.content or ""
