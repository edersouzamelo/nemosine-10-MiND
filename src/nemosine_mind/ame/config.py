from __future__ import annotations

import os
from dataclasses import dataclass, asdict
from typing import Any, Dict


DEFAULT_SYSTEM_TEMPLATE = (
    "Agora opero sob o Sistema Nemosine Nous.\n"
    "Você está em modo AME (Arquitetura Mínima Executável).\n"
    "Regras do ciclo:\n"
    "1) A configuração é externa ao LLM e deve ser seguida.\n"
    "2) Responda de forma direta e executável.\n"
    "3) Não invente capacidades; se faltar dado, peça o mínimo necessário.\n"
)


@dataclass(frozen=True)
class AMEConfig:
    version: str = "0.2.0"
    mode: str = "AME"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2
    max_output_tokens: int = 700
    system_template: str = DEFAULT_SYSTEM_TEMPLATE

    def to_public_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Não expõe segredos.
        return d


def load_config() -> AMEConfig:
    """
    Configuração simbólico-modular EXTERNA ao motor linguístico (TR-004).
    Nesta versão mínima, é um dataclass inspecionável e versionado.
    """
    return AMEConfig(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
        max_output_tokens=int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "700")),
    )
