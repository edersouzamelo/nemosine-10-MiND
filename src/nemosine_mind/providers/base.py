from __future__ import annotations

from typing import Dict, List, Protocol


class Provider(Protocol):
    """Minimal contract required by the MiND execution core."""

    @property
    def name(self) -> str:
        ...

    @property
    def model(self) -> str:
        ...

    def generate(
        self,
        *,
        messages: List[Dict[str, str]],
        temperature: float,
        max_output_tokens: int,
    ) -> str:
        ...
