"""Database models. One row is stored for each finished analysis."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from .database import Base

# JSON works with PostgreSQL and is easy to inspect while learning.
JsonType = JSON().with_variant(JSONB, "postgresql")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    filename: Mapped[str] = mapped_column(String(255))
    ats_score: Mapped[float] = mapped_column(Float)
    resume_skills: Mapped[list[str]] = mapped_column(JsonType)
    job_skills: Mapped[list[str]] = mapped_column(JsonType)
    matched_skills: Mapped[list[str]] = mapped_column(JsonType)
    missing_skills: Mapped[list[str]] = mapped_column(JsonType)
    suggestions: Mapped[list[str]] = mapped_column(JsonType)
    resume_text: Mapped[str] = mapped_column(Text)
    job_description: Mapped[str] = mapped_column(Text)


class ResumeOptimization(Base):
    __tablename__ = "optimizations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(index=True, nullable=False, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    target_min: Mapped[int] = mapped_column(nullable=False)
    target_max: Mapped[int] = mapped_column(nullable=False)
    original_score: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    target_achieved: Mapped[bool] = mapped_column(nullable=False)
    iteration_count: Mapped[int] = mapped_column(nullable=False)
    original_resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    final_resume_text: Mapped[str] = mapped_column(Text, nullable=False)
    job_description: Mapped[str] = mapped_column(Text, nullable=False)
    unsupported_requirements: Mapped[list[str]] = mapped_column(JsonType, nullable=False)
    supported_requirements: Mapped[list[str]] = mapped_column(JsonType, nullable=False)
    changes: Mapped[list[dict]] = mapped_column(JsonType, nullable=False)
    iterations: Mapped[list[dict]] = mapped_column(JsonType, nullable=False)
    best_achievable_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
