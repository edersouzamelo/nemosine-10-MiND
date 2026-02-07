from __future__ import annotations

import time
import uuid
from typing import Dict, List

from .config import AMEConfig
from .input_handler import InputHandler
from .models import AMEOutput, AMECycleRecord, RunResult
from .registry import JsonlRegistry
from .motor_openai import OpenAIMotor


class Orchestrator:
    """
    Componente 3 (TR-004): Orquestrador do Loop
    - Coordena fluxo determinístico.
    - Aplica configuração externa.
    - Chama motor linguístico.
    - Registra ciclo.
    """

    def __init__(self, config: AMEConfig, motor: OpenAIMotor, registry: JsonlRegistry):
        self.config = config
        self.motor = motor
        self.registry = registry

    def _build_messages(self, user_text: str) -> List[Dict[str, str]]:
        # Configuração simbólico-modular explícita aplicada como SYSTEM message.
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

        reply_text = self.motor.generate(
            messages=messages,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_output_tokens,
        )
        out = AMEOutput(text=reply_text)

        record = AMECycleRecord(
            cycle_id=cycle_id,
            input={"text": inp.text},
            config=self.config.to_public_dict(),
            output={"text": out.text},
            meta={
                "ts": int(time.time()),
                "latency_ms": int((time.time() - start) * 1000),
            },
        )
        self.registry.append(record)

        return RunResult(cycle_id=cycle_id, reply=out.text)
