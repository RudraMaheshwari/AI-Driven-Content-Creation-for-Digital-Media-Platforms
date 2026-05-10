"""Agent factory that wires the full content-creation pipeline together.

Mirrors the methodology diagram from the source paper:

    user prompt
        ↓
    safety filter
        ↓
    prompt preprocessing  ──► structured brief
        ↓
    initial content generation
        ↓
    quality & safety check ──► (refine? loop)
        ↓ approved
    personalization layer
        ↓
    platform-ready output

The agent runs a deterministic pipeline rather than a free-form ReAct loop —
content production needs reliable stages, not tool *selection*.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agents.monitoring.callbacks import TraceCollector
from src.agents.tools.content_generator import generate_content
from src.agents.tools.image_prompt_builder import build_image_prompt
from src.agents.tools.personalizer import personalize_content
from src.agents.tools.prompt_refiner import ContentBrief, refine_brief
from src.agents.tools.quality_evaluator import QualityReport, evaluate_quality
from src.agents.tools.rewriter import rewrite_content
from src.agents.tools.safety_filter import is_safe
from src.config.settings import settings
from src.utils.exceptions import ContentSafetyError
from src.utils.logger import get_logger

logger = get_logger("agent.content")


@dataclass
class ContentAgentResult:
    brief: ContentBrief
    initial_output: str
    final_output: str
    quality: QualityReport | None
    iterations: int
    image_prompt: str | None
    trace: dict[str, Any]


class ContentCreationAgent:
    """Orchestrates the safety → refine → generate → evaluate → rewrite → personalize chain."""

    def run(
        self,
        user_prompt: str,
        *,
        content_type: str,
        platform: str,
        tone: str,
        length: str,
        audience: str | None,
        refine_loop: bool | None = None,
        personalize: bool | None = None,
        generate_image: bool | None = None,
    ) -> ContentAgentResult:
        tracer = TraceCollector()
        run_refine = settings.content_refinement_loop if refine_loop is None else refine_loop
        run_personalize = (
            settings.content_personalization if personalize is None else personalize
        )
        run_image = (
            settings.content_generate_image if generate_image is None else generate_image
        )

        # 1. Safety check
        if settings.content_safety_filter:
            tracer.start("safety_check")
            safe, reason = is_safe(user_prompt)
            tracer.end("safety_check", safe=safe, reason=reason)
            if not safe:
                raise ContentSafetyError(f"Prompt rejected by safety filter: {reason}")

        # 2. Prompt preprocessing → structured brief
        tracer.start("refine_brief")
        brief = refine_brief(
            user_prompt,
            content_type=content_type,
            platform=platform,
            tone=tone,
            length=length,
            audience=audience,
        )
        tracer.end(
            "refine_brief",
            refined_preview=brief.refined_prompt[:200],
            key_points=brief.key_points,
        )

        # 3. Initial content generation
        tracer.start("generate")
        current_output = generate_content(
            refined_prompt=brief.refined_prompt,
            key_points=brief.key_points,
            must_avoid=brief.must_avoid,
            content_type=content_type,
            platform=platform,
            tone=tone,
            length=length,
            audience=audience,
        )
        tracer.end("generate", chars=len(current_output))
        initial_output = current_output

        # 4. Quality evaluation + rewrite loop
        quality: QualityReport | None = None
        iterations = 0
        if run_refine:
            for i in range(max(1, settings.content_refinement_max_iterations)):
                tracer.start("evaluate")
                quality = evaluate_quality(
                    refined_prompt=brief.refined_prompt,
                    content=current_output,
                    content_type=content_type,
                    platform=platform,
                    tone=tone,
                )
                tracer.end(
                    "evaluate",
                    score=quality.score,
                    issues=quality.issues,
                )
                if quality.score >= settings.content_quality_threshold:
                    logger.info(
                        f"quality {quality.score:.2f} >= threshold "
                        f"{settings.content_quality_threshold}; stopping refinement"
                    )
                    break

                tracer.start("rewrite", iteration=i + 1)
                current_output = rewrite_content(
                    refined_prompt=brief.refined_prompt,
                    content=current_output,
                    feedback=quality.feedback,
                    issues=quality.issues,
                )
                tracer.end("rewrite", iteration=i + 1, chars=len(current_output))
                iterations += 1

        # 5. Personalization layer
        if run_personalize and audience:
            tracer.start("personalize")
            current_output = personalize_content(
                content=current_output,
                audience=audience,
                tone=tone,
                platform=platform,
            )
            tracer.end("personalize", chars=len(current_output))

        # 6. Image-prompt synthesis (text-only here; the actual image is rendered
        #    by ImageService outside the LangChain pipeline).
        image_prompt: str | None = None
        if run_image:
            tracer.start("image_prompt")
            try:
                image_prompt = build_image_prompt(
                    content=current_output,
                    content_type=content_type,
                    platform=platform,
                    tone=tone,
                )
            except Exception as exc:  # pragma: no cover - non-fatal
                logger.warning(f"image-prompt synthesis failed: {exc}")
                tracer.note("image_prompt_error", error=str(exc))
            tracer.end(
                "image_prompt",
                chars=len(image_prompt) if image_prompt else 0,
            )

        return ContentAgentResult(
            brief=brief,
            initial_output=initial_output,
            final_output=current_output,
            quality=quality,
            iterations=iterations,
            image_prompt=image_prompt,
            trace=tracer.snapshot(),
        )


_agent: ContentCreationAgent | None = None


def get_content_agent() -> ContentCreationAgent:
    global _agent
    if _agent is None:
        _agent = ContentCreationAgent()
    return _agent
