from __future__ import annotations

from .models import AMEInput


class InputHandler:
    """
    Componente 1 (TR-004): Manipulador de Entrada
    - Recebe texto e normaliza.
    - Sem inferência semântica profunda.
    """

    @staticmethod
    def parse(user_text: str) -> AMEInput:
        return AMEInput(text=(user_text or "").strip())
