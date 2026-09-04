"""Legacy import path for the neutral MiND orchestrator."""

from nemosine_mind.core.orchestrator import Orchestrator as CoreOrchestrator
from nemosine_mind.core.orchestrator import TextGenerator


class Orchestrator(CoreOrchestrator):
    def __init__(self, config, motor, registry):
        super().__init__(config=config, provider=motor, registry=registry)


__all__ = ["Orchestrator", "TextGenerator"]
