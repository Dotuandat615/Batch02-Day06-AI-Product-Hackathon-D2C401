from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ClarifyInput(BaseModel):
    question: str = ""
    response_type: str = "text"
    options: list[str] = Field(default_factory=list)


def ask_user(**kwargs) -> dict[str, Any]:
    inp = ClarifyInput(**kwargs)
    return {
        "tool": "ask_user",
        "question": inp.question,
        "response_type": inp.response_type,
        "options": inp.options,
        "awaiting_user": True,
    }
