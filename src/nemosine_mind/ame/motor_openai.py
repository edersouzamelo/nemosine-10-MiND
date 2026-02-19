from __future__ import annotations

from typing import List, Dict, Any, Optional
from openai import OpenAI


class OpenAIMotor:
    """
    Componente 4 (TR-004): Motor Linguístico
    - Apenas geração textual.
    - Não controla estado global.
    """

    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None

    def is_configured(self) -> bool:
        return bool(self._client)

    def generate(self, *, messages: List[Dict[str, str]], temperature: float, max_output_tokens: int) -> str:
        if not self._client:
            raise RuntimeError("OPENAI_API_KEY not configured")

        completion = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            max_tokens=max_output_tokens,
            messages=messages,
        )
        return completion.choices[0].message.content or ""
