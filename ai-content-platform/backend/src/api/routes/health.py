from __future__ import annotations

from fastapi import APIRouter

from src.api.schemas import HealthResponse
from src.config.settings import settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        mock_mode=settings.content_mock,
        refinement_loop=settings.content_refinement_loop,
        personalization=settings.content_personalization,
        safety_filter=settings.content_safety_filter,
        image_generation=settings.content_generate_image,
        gemini_configured=bool(settings.google_api_key),
        model_id=settings.gemini_model,
        image_model_id=settings.image_model_id,
    )
