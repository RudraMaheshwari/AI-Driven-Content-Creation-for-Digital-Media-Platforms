"""Step 1 of the pipeline: turn the user's raw prompt into a structured brief.

Mirrors the paper's "Prompt Preprocessing → Context & Requirement Extraction" stages.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import REFINE_PROMPT
from src.agents.tools.json_utils import extract_json
from src.services.gemini_service import get_gemini_llm
from src.utils.exceptions import ContentSafetyError
from src.utils.logger import get_logger

logger = get_logger("tool.refiner")


@dataclass
class ContentBrief:
    refined_prompt: str
    key_points: list[str]
    must_avoid: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def refine_brief(
    user_prompt: str,
    *,
    content_type: str,
    platform: str,
    tone: str,
    length: str,
    audience: str | None,
) -> ContentBrief:
    user_prompt = (user_prompt or "").strip()
    if not user_prompt:
        raise ValueError("prompt is empty")

    chain = REFINE_PROMPT | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "user_prompt": user_prompt,
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
            "length": length,
            "audience": audience or "general digital media audience",
        }
    )
    logger.debug(f"gemini refine raw: {raw[:200]}")

    try:
        parsed = extract_json(raw)
    except Exception as exc:
        logger.warning(f"failed to parse refine JSON: {exc}; falling back to raw prompt")
        return ContentBrief(refined_prompt=user_prompt, key_points=[], must_avoid=[])

    if parsed.get("unsafe"):
        raise ContentSafetyError(parsed.get("reason", "Prompt was flagged as unsafe."))

    return ContentBrief(
        refined_prompt=str(parsed.get("refined_prompt") or user_prompt),
        key_points=[str(p) for p in (parsed.get("key_points") or [])],
        must_avoid=[str(p) for p in (parsed.get("must_avoid") or [])],
    )
