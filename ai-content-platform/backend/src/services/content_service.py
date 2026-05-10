"""Content-creation service.

In mock mode (CONTENT_MOCK=true) returns a deterministic placeholder so the
UI/API can be developed without burning Gemini quota. Otherwise delegates to
the LangChain content agent and the ImageService.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any, Callable

from src.agents.factories.content_agent import (
    ContentAgentResult,
    get_content_agent,
)
from src.agents.tools.image_prompt_builder import pick_aspect
from src.agents.tools.prompt_refiner import ContentBrief
from src.agents.tools.quality_evaluator import QualityReport
from src.config.settings import settings
from src.services.image_service import get_image_service
from src.utils.logger import get_logger

logger = get_logger("content")


@dataclass
class ContentRequest:
    prompt: str
    content_type: str
    platform: str
    tone: str
    length: str
    audience: str | None = None
    refine_loop: bool | None = None
    personalize: bool | None = None
    generate_image: bool | None = None
    record_id: str | None = None


@dataclass
class ContentResult:
    initial_output: str
    final_output: str
    brief: ContentBrief
    quality: QualityReport | None
    iterations: int
    image_prompt: str | None
    image_url: str | None
    image_model_id: str | None
    duration_ms: int
    trace: dict[str, Any]


class ContentService:
    """Top-level orchestrator. Picks mock vs real path based on settings."""

    def generate(
        self,
        req: ContentRequest,
        *,
        on_text_ready: Callable[["ContentResult"], None] | None = None,
    ) -> ContentResult:
        """Run the full pipeline.

        If ``on_text_ready`` is provided, it's invoked once the article body
        and image prompt are produced — *before* the image is rendered. The
        caller can persist the intermediate state so a polling client can
        display the article while the image is still being generated.
        """
        started = time.perf_counter()
        run_image = (
            settings.content_generate_image
            if req.generate_image is None
            else req.generate_image
        )

        if settings.content_mock:
            result = self._mock(req, run_image=run_image, on_text_ready=on_text_ready)
        else:
            agent_result: ContentAgentResult = get_content_agent().run(
                req.prompt,
                content_type=req.content_type,
                platform=req.platform,
                tone=req.tone,
                length=req.length,
                audience=req.audience,
                refine_loop=req.refine_loop,
                personalize=req.personalize,
                generate_image=run_image,
            )
            # Build the text-only result and notify the caller before
            # rendering the image (which can take 10–20s on Pollinations / Imagen).
            result = ContentResult(
                initial_output=agent_result.initial_output,
                final_output=agent_result.final_output,
                brief=agent_result.brief,
                quality=agent_result.quality,
                iterations=agent_result.iterations,
                image_prompt=agent_result.image_prompt,
                image_url=None,
                image_model_id=None,
                duration_ms=int((time.perf_counter() - started) * 1000),
                trace=agent_result.trace,
            )
            if on_text_ready is not None:
                on_text_ready(result)

            # Phase 2: image render
            if run_image and agent_result.image_prompt:
                width, height = pick_aspect(
                    platform=req.platform, content_type=req.content_type
                )
                try:
                    img = get_image_service().generate(
                        agent_result.image_prompt,
                        record_id=req.record_id,
                        width=width,
                        height=height,
                    )
                    result.image_url = img.url
                    if img.mock:
                        result.image_model_id = "mock"
                    elif img.provider == "gemini":
                        result.image_model_id = settings.image_model_id
                    elif img.provider == "pollinations":
                        result.image_model_id = (
                            f"pollinations/{settings.image_pollinations_model}"
                        )
                    else:
                        result.image_model_id = img.provider
                except Exception as exc:  # pragma: no cover - non-fatal
                    logger.warning(f"image render failed: {exc}")

        result.duration_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            f"content done platform={req.platform} type={req.content_type} "
            f"iters={result.iterations} image={'yes' if result.image_url else 'no'} "
            f"duration_ms={result.duration_ms}"
        )
        return result

    # ---------- mock path ----------

    @staticmethod
    def _mock(
        req: ContentRequest,
        *,
        run_image: bool,
        on_text_ready: Callable[["ContentResult"], None] | None = None,
    ) -> ContentResult:
        digest = hashlib.md5(req.prompt.encode()).hexdigest()[:8]
        body = (
            f"[MOCK · {req.platform.upper()} · {req.content_type}]\n\n"
            f"This is a placeholder response generated without calling Gemini. "
            f"It is deterministic for prompt hash {digest} so the UI has something "
            f"realistic to render.\n\n"
            f"Subject: {req.prompt}\n"
            f"Tone: {req.tone}. Length: {req.length}. "
            f"Audience: {req.audience or 'general audience'}.\n\n"
            f"Set CONTENT_MOCK=false in backend/.env and provide GOOGLE_API_KEY to "
            f"get real generated content."
        )
        brief = ContentBrief(
            refined_prompt=f"(mock) Produce a {req.tone} {req.content_type} for "
            f"{req.platform}: {req.prompt}",
            key_points=["mock key point 1", "mock key point 2", "mock key point 3"],
            must_avoid=["actual model inference"],
        )
        quality = QualityReport(
            score=0.85,
            clarity=0.9,
            relevance=0.85,
            tone_match=0.9,
            issues=[],
            feedback="mock response — quality not actually evaluated",
        )
        trace = {
            "events": [
                {"event": "mock", "note": "CONTENT_MOCK=true; skipping Gemini calls"}
            ]
        }
        image_prompt = None
        if run_image:
            image_prompt = (
                f"Editorial illustration accompanying a {req.tone} {req.content_type} "
                f"about: {req.prompt[:120]}"
            )
        result = ContentResult(
            initial_output=body,
            final_output=body,
            brief=brief,
            quality=quality,
            iterations=0,
            image_prompt=image_prompt,
            image_url=None,
            image_model_id=None,
            duration_ms=0,
            trace=trace,
        )
        if on_text_ready is not None:
            on_text_ready(result)

        if run_image and image_prompt is not None:
            try:
                width, height = pick_aspect(
                    platform=req.platform, content_type=req.content_type
                )
                img = get_image_service().generate(
                    image_prompt,
                    record_id=req.record_id,
                    width=width,
                    height=height,
                )
                result.image_url = img.url
                result.image_model_id = "mock"
            except Exception as exc:  # pragma: no cover
                logger.warning(f"mock image render failed: {exc}")
        return result


_service: ContentService | None = None


def get_content_service() -> ContentService:
    global _service
    if _service is None:
        _service = ContentService()
    return _service
