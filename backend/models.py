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

