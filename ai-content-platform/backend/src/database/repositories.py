"""Thin repository layer over SQLAlchemy models."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.database.models import ContentRecord, ContentRefinementLog
from src.utils.ids import new_id


class ContentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **fields) -> ContentRecord:
        record = ContentRecord(id=new_id("ct"), **fields)
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get(self, record_id: str) -> ContentRecord | None:
        return self.db.get(ContentRecord, record_id)

    def list_recent(
        self,
        *,
        limit: int = 50,
        platform: str | None = None,
        content_type: str | None = None,
    ) -> Iterable[ContentRecord]:
        stmt = select(ContentRecord).order_by(desc(ContentRecord.created_at)).limit(limit)
        if platform:
            stmt = stmt.where(ContentRecord.platform == platform)
        if content_type:
            stmt = stmt.where(ContentRecord.content_type == content_type)
        return list(self.db.execute(stmt).scalars())

    def mark_completed(
        self,
        record: ContentRecord,
        *,
        initial_output: str,
        final_output: str,
        quality_score: float | None,
        quality_notes: str | None,
        refinement_iterations: int,
        duration_ms: int,
        agent_trace: dict | None = None,
    ) -> ContentRecord:
        record.status = "completed"
        record.initial_output = initial_output
        record.final_output = final_output
        record.quality_score = quality_score
        record.quality_notes = quality_notes
        record.refinement_iterations = refinement_iterations
        record.duration_ms = duration_ms
        record.completed_at = datetime.now(timezone.utc)
        if agent_trace is not None:
            record.agent_trace = agent_trace
        self.db.commit()
        self.db.refresh(record)
        return record

    def mark_failed(self, record: ContentRecord, *, error: str) -> ContentRecord:
        record.status = "failed"
        record.error = error
        record.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(record)
        return record


class RefinementLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(
        self,
        record_id: str,
        iteration: int,
        input_text: str,
        output_text: str,
        feedback: str | None = None,
    ) -> ContentRefinementLog:
        row = ContentRefinementLog(
            id=new_id("rf"),
            record_id=record_id,
            iteration=iteration,
            input_text=input_text,
            output_text=output_text,
            feedback=feedback,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row
