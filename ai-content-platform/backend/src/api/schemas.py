"""Pydantic request/response schemas for the public API."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


ContentType = Literal[
    "article",
    "blog_post",
    "social_post",
    "caption",
    "marketing_copy",
    "ad_copy",
    "newsletter",
    "script",
    "summary",
    "headline",
]

Platform = Literal[
    "blog",
    "twitter",
    "linkedin",
    "instagram",
    "facebook",
    "youtube",
    "tiktok",
    "newsletter",
    "marketing",
    "news_portal",
]

Tone = Literal[
    "professional",
    "casual",
    "witty",
    "formal",
    "persuasive",
    "informative",
    "inspirational",
    "friendly",
]

Length = Literal["short", "medium", "long"]


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=4000)
    content_type: ContentType = "blog_post"
    platform: Platform = "blog"
    tone: Tone = "professional"
    length: Length = "medium"
    audience: str | None = Field(default=None, max_length=300)
    refine_loop: bool | None = None
    personalize: bool | None = None
    generate_image: bool | None = None


class QualityPayload(BaseModel):
    score: float
    clarity: float
    relevance: float
    tone_match: float
    issues: list[str] = []
    feedback: str = ""


class ContentResponse(BaseModel):
    id: str
    status: str
    error: str | None = None
    original_prompt: str
    refined_prompt: str | None
    content_type: str
    platform: str
    tone: str
    length: str
    audience: str | None
    initial_output: str | None
    final_output: str | None
    image_prompt: str | None = None
    image_url: str | None = None
    image_model_id: str | None = None
    quality_score: float | None
    quality_notes: str | None
    refinement_iterations: int
    model_id: str
    duration_ms: int | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class HistoryResponse(BaseModel):
    items: list[ContentResponse]


class RefineRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)
    feedback: str = Field(..., min_length=1, max_length=1000)
    refined_prompt: str | None = None


class RefineResponse(BaseModel):
    revised_content: str


class HealthResponse(BaseModel):
    status: str
    mock_mode: bool
    refinement_loop: bool
    personalization: bool
    safety_filter: bool
    image_generation: bool
    gemini_configured: bool
    model_id: str
    image_model_id: str
