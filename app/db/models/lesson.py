from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class LessonRequest(Base, TimestampMixin):
    __tablename__ = "lesson_requests"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    teacher_id: Mapped[UUID] = mapped_column(ForeignKey("teachers.id"), index=True)
    school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id"), index=True)
    region_id: Mapped[UUID] = mapped_column(ForeignKey("regions.id"), index=True)
    raw_user_input: Mapped[str] = mapped_column(Text)
    subject: Mapped[str | None] = mapped_column(String(64), index=True)
    grade: Mapped[int | None] = mapped_column(Integer, index=True)
    topic: Mapped[str | None] = mapped_column(String(255), index=True)
    language_mode: Mapped[str] = mapped_column(String(128), default="th_ms_en")
    duration_minutes: Mapped[int] = mapped_column(Integer, default=45)
    resource_level: Mapped[str] = mapped_column(String(32), default="low")
    status: Mapped[str] = mapped_column(String(64), default="queued", index=True)
    structured_content: Mapped[dict | None] = mapped_column(JSON)
    rendered_markdown: Mapped[str | None] = mapped_column(Text)
    docx_media_asset_id: Mapped[UUID | None] = mapped_column(ForeignKey("media_assets.id"))
    model_provider: Mapped[str | None] = mapped_column(String(64))
    model_name: Mapped[str | None] = mapped_column(String(128))
    prompt_version: Mapped[str | None] = mapped_column(String(128))
    rag_strategy_version: Mapped[str | None] = mapped_column(String(128))
    rag_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    rag_confidence: Mapped[str | None] = mapped_column(String(32))
    token_input: Mapped[int | None] = mapped_column(Integer)
    token_output: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LessonKnowledgeRef(Base):
    __tablename__ = "lesson_knowledge_refs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lesson_request_id: Mapped[UUID] = mapped_column(ForeignKey("lesson_requests.id"), index=True)
    knowledge_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    knowledge_item_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("knowledge_item_versions.id")
    )
    chunk_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_chunks.id"))
    relevance_score: Mapped[float | None]
    rank: Mapped[int | None] = mapped_column(Integer)
    used_in_section: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

