from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RenderJob(Base):
    __tablename__ = 'render_jobs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    celery_task_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    prompt: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='queued', index=True)
    output_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
