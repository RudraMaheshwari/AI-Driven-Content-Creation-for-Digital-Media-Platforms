"""LangChain-backed Gemini client used by content-generation agents."""
from __future__ import annotations

from functools import lru_cache

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config.settings import settings
from src.utils.exceptions import AppError
from src.utils.logger import get_logger

logger = get_logger("gemini")


@lru_cache(maxsize=1)
def get_gemini_llm() -> BaseChatModel:
    """Singleton Gemini chat model used across agents."""
    if not settings.google_api_key:
        raise AppError(
            "GOOGLE_API_KEY is not set. Configure it in the backend .env.",
            code="missing_api_key",
            status_code=503,
        )
    logger.info(f"initializing Gemini model={settings.gemini_model}")
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        temperature=settings.gemini_temperature,
        max_output_tokens=settings.gemini_max_output_tokens,
        google_api_key=settings.google_api_key,
        convert_system_message_to_human=True,
    )
