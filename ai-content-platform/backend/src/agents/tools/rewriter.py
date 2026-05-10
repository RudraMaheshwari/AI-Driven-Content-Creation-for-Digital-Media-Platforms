"""Step 4: rewrite content given quality feedback. The 'Refinement & Rewriting Loop'
node from the paper's flow chart."""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import REWRITE_PROMPT
from src.agents.tools.output_sanitizer import sanitize_content
from src.services.gemini_service import get_gemini_llm
from src.utils.logger import get_logger

logger = get_logger("tool.rewriter")


def rewrite_content(
    *,
    refined_prompt: str,
    content: str,
    feedback: str,
    issues: list[str],
) -> str:
    chain = REWRITE_PROMPT | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "refined_prompt": refined_prompt,
            "content": content,
            "feedback": feedback or "(no specific feedback)",
            "issues": ", ".join(issues) or "(none)",
        }
    )
    return sanitize_content(raw)
