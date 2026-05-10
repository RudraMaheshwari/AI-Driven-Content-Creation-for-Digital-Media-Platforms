"""Step 2: produce the actual content from the structured brief."""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import GENERATE_PROMPT
from src.agents.tools.output_sanitizer import sanitize_content
from src.services.gemini_service import get_gemini_llm
from src.utils.logger import get_logger

logger = get_logger("tool.generator")


def generate_content(
    *,
    refined_prompt: str,
    key_points: list[str],
    must_avoid: list[str],
    content_type: str,
    platform: str,
    tone: str,
    length: str,
    audience: str | None,
) -> str:
    chain = GENERATE_PROMPT | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "refined_prompt": refined_prompt,
            "key_points": ", ".join(key_points) or "(none specified)",
            "must_avoid": ", ".join(must_avoid) or "(none specified)",
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
            "length": length,
            "audience": audience or "general digital media audience",
        }
    )
    return sanitize_content(raw)
