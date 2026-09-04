"""Legacy AME model names mapped to the neutral MiND core."""

from nemosine_mind.core.models import (
    CycleRecord,
    MindInput,
    MindOutput,
    RunResult,
)

AMEInput = MindInput
AMEOutput = MindOutput
AMECycleRecord = CycleRecord

__all__ = ["AMECycleRecord", "AMEInput", "AMEOutput", "RunResult"]
