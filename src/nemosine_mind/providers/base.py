from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Protocol


@dataclass(frozen=True)
class ProviderResult:
    """Provider-neutral result returned to the MiND core."""

    text: str
    request_id: Optional[str] = None
    finish_reason: Optional[str] = None
    usage: Dict[str, Any] = field(default_factory=dict)


class ProviderError(RuntimeError):
    """Safe, provider-neutral failure suitable for an audit artifact."""

    def __init__(
        self,
        provider: str,
        code: str,
        safe_message: str,
        *,
        retryable: bool = False,
    ):
        super().__init__(safe_message)
        self.provider = provider
        self.code = code
        self.safe_message = safe_message
        self.retryable = retryable


class ProviderConfigurationError(ProviderError):
    """Raised when a provider cannot run with the supplied configuration."""


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
    ) -> ProviderResult:
        ...
