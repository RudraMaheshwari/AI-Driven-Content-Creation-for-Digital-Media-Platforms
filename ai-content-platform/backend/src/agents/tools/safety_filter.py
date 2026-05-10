"""Binary safety classifier for incoming content prompts.

Two layers:
1. Cheap keyword blocklist — rejects obvious cases without an LLM call.
2. Gemini-based classification for the rest.
"""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import SAFETY_PROMPT
from src.services.gemini_service import get_gemini_llm
from src.utils.logger import get_logger

logger = get_logger("tool.safety")

_HARD_BLOCKLIST = {
    "child sexual",
    "csam",
    "build a bomb",
    "make a bomb",
    "kill yourself",
}


def _keyword_unsafe(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(term in lowered for term in _HARD_BLOCKLIST)


def is_safe(prompt: str) -> tuple[bool, str]:
    prompt = (prompt or "").strip()
    if not prompt:
        return False, "empty prompt"
    if _keyword_unsafe(prompt):
        return False, "matched blocklist"

    try:
        chain = SAFETY_PROMPT | get_gemini_llm() | StrOutputParser()
        verdict = chain.invoke({"prompt": prompt}).strip().upper()
    except Exception as exc:
        # Fail open on the keyword-safe path — the blocklist already rejected hard cases.
        logger.warning(f"safety classifier unavailable ({exc}); allowing prompt")
        return True, "classifier unavailable"

    if "UNSAFE" in verdict:
        return False, "classifier flagged UNSAFE"
    return True, "classifier SAFE"
