from __future__ import annotations

from .models import MindInput


class InputHandler:
    """Normalize user input without semantic inference."""

    @staticmethod
    def parse(user_text: str) -> MindInput:
        return MindInput(text=(user_text or "").strip())
