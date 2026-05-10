"""SQLAlchemy ORM models for content generation history."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class ContentRecord(Base):
    __tablename__ = "content_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    original_prompt: Mapped[str] = mapped_column(Text)
    refined_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    content_type: Mapped[str] = mapped_column(String(64), index=True)
    platform: Mapped[str] = mapped_column(String(64), index=True)
    tone: Mapped[str] = mapped_column(String(64))
    length: Mapped[str] = mapped_column(String(32))
    audience: Mapped[str | None] = mapped_column(String(255), nullable=True)

    initial_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    final_output: Mapped[str | None] = mapped_column(Text, nullable=True)

    image_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    image_model_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    quality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    refinement_iterations: Mapped[int] = mapped_column(Integer, default=0)

    model_id: Mapped[str] = mapped_column(String(255))

    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent_trace: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class ContentRefinementLog(Base):
    __tablename__ = "content_refinement_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    record_id: Mapped[str] = mapped_column(String(64), index=True)
    iteration: Mapped[int] = mapped_column(Integer)
    input_text: Mapped[str] = mapped_column(Text)
    output_text: Mapped[str] = mapped_column(Text)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
