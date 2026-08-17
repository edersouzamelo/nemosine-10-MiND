"""Legacy AME configuration kept for compatibility with Nemosine clients."""

import os
from dataclasses import dataclass

from nemosine_mind.core.config import MindConfig


DEFAULT_SYSTEM_TEMPLATE = (
    "Agora opero sob o Sistema Nemosine Nous.\n"
    "Você está em modo AME (Arquitetura Mínima Executável).\n"
    "Regras do ciclo:\n"
    "1) A configuração é externa ao LLM e deve ser seguida.\n"
    "2) Responda de forma direta e executável.\n"
    "3) Não invente capacidades; se faltar dado, peça o mínimo necessário.\n"
)


@dataclass(frozen=True)
class AMEConfig(MindConfig):
    mode: str = "AME"
    system_template: str = DEFAULT_SYSTEM_TEMPLATE


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
