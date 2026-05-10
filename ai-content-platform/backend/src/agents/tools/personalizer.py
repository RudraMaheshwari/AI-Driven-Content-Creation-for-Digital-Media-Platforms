"""Step 5: tailor finished content to an audience profile. The 'Personalization
Layer' node from the paper's architecture diagram."""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import PERSONALIZE_PROMPT
from src.agents.tools.output_sanitizer import sanitize_content
from src.services.gemini_service import get_gemini_llm
from src.utils.logger import get_logger

logger = get_logger("tool.personalizer")


def personalize_content(
    *,
    content: str,
    audience: str,
    tone: str,
    platform: str,
) -> str:
    chain = PERSONALIZE_PROMPT | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "content": content,
            "audience": audience,
            "tone": tone,
            "platform": platform,
        }
    )
    return sanitize_content(raw)
