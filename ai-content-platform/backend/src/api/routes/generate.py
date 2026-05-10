"""/generate and /history endpoints — the core user-facing surface.

POST /generate enqueues a job and returns immediately with a `pending` record.
The Gemini orchestration runs in a FastAPI BackgroundTask. The frontend polls
GET /generate/{id} until status flips to `completed` or `failed`.
"""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from src.api.schemas import ContentResponse, GenerateRequest, HistoryResponse
from src.config.settings import settings
from src.database.models import ContentRecord
from src.database.repositories import ContentRepository
from src.database.session import get_db, session_scope
from src.services.content_service import ContentRequest as SvcRequest
from src.services.content_service import get_content_service
from src.utils.exceptions import AppError
from src.utils.logger import get_logger

router = APIRouter(tags=["generate"])
logger = get_logger("api.generate")


def _to_response(record: ContentRecord) -> ContentResponse:
    return ContentResponse(
        id=record.id,
        status=record.status,
        error=record.error,
        original_prompt=record.original_prompt,
        refined_prompt=record.refined_prompt,
        content_type=record.content_type,
        platform=record.platform,
        tone=record.tone,
        length=record.length,
        audience=record.audience,
        initial_output=record.initial_output,
        final_output=record.final_output,
        image_prompt=record.image_prompt,
        image_url=record.image_url,
        image_model_id=record.image_model_id,
        quality_score=record.quality_score,
        quality_notes=record.quality_notes,
        refinement_iterations=record.refinement_iterations,
        model_id=record.model_id,
        duration_ms=record.duration_ms,
        created_at=record.created_at,
        completed_at=record.completed_at,
    )


@router.post("/generate", response_model=ContentResponse, status_code=202)
def generate(
    body: GenerateRequest,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
) -> ContentResponse:
    repo = ContentRepository(db)

    record = repo.create(
        original_prompt=body.prompt,
        refined_prompt=None,
        content_type=body.content_type,
        platform=body.platform,
        tone=body.tone,
        length=body.length,
        audience=body.audience,
        model_id=settings.gemini_model,
        status="pending",
    )

    background.add_task(_run_content_job, record.id, body.model_dump())

    return _to_response(record)


@router.get("/generate/{record_id}", response_model=ContentResponse)
def get_generation(record_id: str, db: Session = Depends(get_db)) -> ContentResponse:
    record = ContentRepository(db).get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="not found")
    return _to_response(record)


@router.get("/history", response_model=HistoryResponse)
def list_history(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=200),
    platform: str | None = Query(default=None),
    content_type: str | None = Query(default=None),
) -> HistoryResponse:
    records = ContentRepository(db).list_recent(
        limit=limit, platform=platform, content_type=content_type
    )
    return HistoryResponse(items=[_to_response(r) for r in records])


# ---------- background worker ----------


def _run_content_job(record_id: str, body: dict) -> None:
    """Runs in FastAPI's threadpool after the POST response has been sent.

    Loads its own DB session (the request-scoped one is already closed by now).
    """
    with session_scope() as db:
        repo = ContentRepository(db)
        record = repo.get(record_id)
        if record is None:
            logger.error(f"job {record_id} vanished before worker picked it up")
            return

        record.status = "running"
        db.commit()
        db.refresh(record)

        def on_text_ready(text_result) -> None:
            """Commit the article body before image rendering starts so the
            polling client can render text immediately and show a loader for
            the image."""
            record.refined_prompt = text_result.brief.refined_prompt
            record.initial_output = text_result.initial_output
            record.final_output = text_result.final_output
            record.image_prompt = text_result.image_prompt
            record.quality_score = (
                text_result.quality.score if text_result.quality else None
            )
            record.quality_notes = (
                text_result.quality.feedback if text_result.quality else None
            )
            record.refinement_iterations = text_result.iterations
            record.status = "rendering_image" if text_result.image_prompt else "running"
            db.commit()
            db.refresh(record)

        try:
            result = get_content_service().generate(
                SvcRequest(
                    prompt=body["prompt"],
                    content_type=body["content_type"],
                    platform=body["platform"],
                    tone=body["tone"],
                    length=body["length"],
                    audience=body.get("audience"),
                    refine_loop=body.get("refine_loop"),
                    personalize=body.get("personalize"),
                    generate_image=body.get("generate_image"),
                    record_id=record.id,
                ),
                on_text_ready=on_text_ready,
            )
        except AppError as exc:
            logger.warning(f"job {record_id} failed: {exc.message}")
            repo.mark_failed(record, error=exc.message)
            return
        except Exception as exc:
            logger.exception(f"job {record_id} crashed")
            repo.mark_failed(record, error=str(exc))
            return

        record.refined_prompt = result.brief.refined_prompt
        record.image_prompt = result.image_prompt
        record.image_url = result.image_url
        record.image_model_id = result.image_model_id
        repo.mark_completed(
            record,
            initial_output=result.initial_output,
            final_output=result.final_output,
            quality_score=result.quality.score if result.quality else None,
            quality_notes=result.quality.feedback if result.quality else None,
            refinement_iterations=result.iterations,
            duration_ms=result.duration_ms,
            agent_trace=result.trace,
        )
