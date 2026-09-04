from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .core.config import MindConfig
from .core.models import RunResult
from .core.registry import CycleStore
from .providers.base import Provider
from .runtime import MindRuntime, build_runtime


@dataclass(frozen=True)
class Mind:
    """Small public Python API for running and inspecting MiND interactions."""

    runtime: MindRuntime

    @classmethod
    def create(
        cls,
        *,
        config: Optional[MindConfig] = None,
        provider: Optional[Provider] = None,
        store: Optional[CycleStore] = None,
    ) -> "Mind":
        return cls(build_runtime(config=config, provider=provider, registry=store))

    def run(self, text: str) -> RunResult:
        return self.runtime.orchestrator.run(text)

    def get_cycle(self, cycle_id: str) -> Optional[Dict[str, Any]]:
        return self.runtime.registry.get(cycle_id)

    def list_cycles(self, *, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return self.runtime.registry.list(limit=limit, offset=offset)
