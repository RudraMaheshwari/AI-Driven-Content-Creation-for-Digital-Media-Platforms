"""Step 6: turn finished content into a one-paragraph image-generation prompt.

The image prompt is biased toward a poster/marketing-graphic aesthetic for
social platforms (Instagram, Facebook, marketing, ad copy, news_portal,
TikTok) and toward a clean editorial illustration for long-form content
(blogs, articles, newsletters, scripts).
"""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser

from src.agents.prompts.templates import IMAGE_PROMPT
from src.services.gemini_service import get_gemini_llm
from src.utils.logger import get_logger

logger = get_logger("tool.image_prompt")


_POSTER_PLATFORMS = {
    "instagram",
    "facebook",
    "tiktok",
    "marketing",
    "ad_copy",
    "news_portal",
    "twitter",
}

_POSTER_TYPES = {
    "social_post",
    "caption",
    "marketing_copy",
    "ad_copy",
    "headline",
}


def pick_image_style(*, platform: str, content_type: str) -> str:
    """Decide whether the image should look like a poster or an editorial illustration."""
    if platform in _POSTER_PLATFORMS or content_type in _POSTER_TYPES:
        return "poster"
    return "editorial"


def pick_aspect(*, platform: str, content_type: str) -> tuple[int, int]:
    """Pick a width/height for Pollinations matching the chosen image style."""
    style = pick_image_style(platform=platform, content_type=content_type)
    if style == "poster":
        # Instagram-friendly 4:5 portrait
        return 1024, 1280
    if platform == "youtube":
        return 1280, 720
    # Default editorial hero — 16:9
    return 1024, 576


def build_image_prompt(
    *, content: str, content_type: str, platform: str, tone: str
) -> str:
    style = pick_image_style(platform=platform, content_type=content_type)
    chain = IMAGE_PROMPT | get_gemini_llm() | StrOutputParser()
    raw = chain.invoke(
        {
            "content": content,
            "content_type": content_type,
            "platform": platform,
            "tone": tone,
            "image_style": style,
        }
    )
    return raw.strip().strip('"').strip()
