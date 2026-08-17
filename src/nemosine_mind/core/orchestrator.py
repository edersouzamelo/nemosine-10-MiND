from __future__ import annotations

import time
import uuid
from typing import Dict, List

from .config import MindConfig
from .input_handler import InputHandler
from .models import CycleRecord, MindOutput, RunResult
from .registry import JsonlRegistry
from nemosine_mind.providers.base import Provider

TextGenerator = Provider


class Orchestrator:
    """Execute one controlled interaction and persist its audit record."""

    def __init__(
        self,
        config: MindConfig,
        provider: Provider,
        registry: JsonlRegistry,
    ):
        self.config = config
        self.provider = provider
        self.registry = registry

    def _build_messages(self, user_text: str) -> List[Dict[str, str]]:
        return [
            {"role": "system", "content": self.config.system_template},
            {"role": "user", "content": user_text},
        ]

    def run(self, user_text: str) -> RunResult:
        start = time.time()
        inp = InputHandler.parse(user_text)
        if not inp.text:
            raise ValueError("Empty input after normalization")

        cycle_id = uuid.uuid4().hex[:12]
        messages = self._build_messages(inp.text)

        try:
            reply_text = self.provider.generate(
                messages=messages,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_output_tokens,
            )
        except Exception as exc:
            self.registry.append(CycleRecord(
                cycle_id=cycle_id,
                input={"text": inp.text},
                config=self.config.to_public_dict(),
                output={},
                meta={
                    "ts": int(time.time()),
                    "latency_ms": int((time.time() - start) * 1000),
                },
                status="failed",
                error={"type": type(exc).__name__, "message": str(exc)},
            ))
            raise

        out = MindOutput(text=reply_text)
        self.registry.append(CycleRecord(
            cycle_id=cycle_id,
            input={"text": inp.text},
            config=self.config.to_public_dict(),
            output={"text": out.text},
            meta={
                "ts": int(time.time()),
                "latency_ms": int((time.time() - start) * 1000),
            },
        ))
        return RunResult(cycle_id=cycle_id, reply=out.text)
