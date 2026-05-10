"""Manual refinement endpoint — lets the UI's 'rewrite with this feedback'
button hit the rewriter directly, without going through the full pipeline."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.agents.tools.rewriter import rewrite_content
from src.api.schemas import RefineRequest, RefineResponse
from src.utils.exceptions import AppError

router = APIRouter(prefix="/content", tags=["content"])


@router.post("/refine", response_model=RefineResponse)
def refine(body: RefineRequest) -> RefineResponse:
    try:
        revised = rewrite_content(
            refined_prompt=body.refined_prompt or body.content[:200],
            content=body.content,
            feedback=body.feedback,
            issues=[],
        )
    except AppError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    return RefineResponse(revised_content=revised)
