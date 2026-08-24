from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .api import Mind
from .core.config import MindConfig
from .core.models import CycleArtifact, RunResult
from .core.registry import CycleStore, JsonlRegistry
from .core.sqlite_registry import SQLiteRegistry

__all__ = [
    "CycleArtifact",
    "CycleStore",
    "JsonlRegistry",
    "Mind",
    "MindConfig",
    "RunResult",
    "SQLiteRegistry",
    "__version__",
]

try:
    __version__ = version("nemosine-mind")
except PackageNotFoundError:
    __version__ = "0+unknown"
