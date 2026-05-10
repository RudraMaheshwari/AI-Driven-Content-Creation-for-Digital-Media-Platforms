"""Step 3: scoring + actionable feedback for the rewrite loop.

Mirrors the paper's "Content Quality Evaluation" / "Quality & Safety Check" node —
returns a normalised score plus structured issues the rewriter can act on.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import QUALITY_PROMPT
from src.agents.tools.json_utils import extract_json
from src.services.gemini_service import get_gemini_llm
from src.utils.logger import get_logger

logger = get_logger("tool.quality")


@dataclass
class QualityReport:
    score: float
    clarity: float
    relevance: float
    tone_match: float
    issues: list[str]
    feedback: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clip(value: Any, default: float = 0.5) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, v))


def evaluate_quality(
    *,
    refined_prompt: str,
    content: str,
    content_type: str,
    platform: str,
    tone: str,
) -> QualityReport:
    chain = QUALITY_PROMPT | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "refined_prompt": refined_prompt,
            "content": content,
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
        }
    )
    logger.debug(f"gemini quality raw: {raw[:200]}")

    try:
        parsed = extract_json(raw)
    except Exception as exc:
        logger.warning(f"failed to parse quality JSON: {exc}; assuming pass")
        return QualityReport(
            score=0.8,
            clarity=0.8,
            relevance=0.8,
            tone_match=0.8,
            issues=[],
            feedback="quality evaluator returned non-JSON; passing through",
        )

    return QualityReport(
        score=_clip(parsed.get("score")),
        clarity=_clip(parsed.get("clarity")),
        relevance=_clip(parsed.get("relevance")),
        tone_match=_clip(parsed.get("tone_match")),
        issues=[str(i) for i in (parsed.get("issues") or [])],
        feedback=str(parsed.get("feedback") or ""),
    )
