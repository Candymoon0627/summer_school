from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class KnowledgeItem(Base, TimestampMixin):
    __tablename__ = "knowledge_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_type: Mapped[str] = mapped_column(String(32), default="project")
    owner_school_id: Mapped[UUID | None] = mapped_column(ForeignKey("schools.id"), index=True)
    owner_region_id: Mapped[UUID | None] = mapped_column(ForeignKey("regions.id"), index=True)
    visibility_scope: Mapped[str] = mapped_column(String(64), index=True)
    review_status: Mapped[str] = mapped_column(String(64), default="pending_review", index=True)
    knowledge_type: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    topic: Mapped[str] = mapped_column(String(255), index=True)
    title: Mapped[str] = mapped_column(String(255))
    target_grade: Mapped[int | None] = mapped_column(Integer, index=True)
    grade_min: Mapped[int] = mapped_column(Integer, index=True)
    grade_max: Mapped[int] = mapped_column(Integer, index=True)
    grade_mode: Mapped[str] = mapped_column(String(32), default="exact")
    curriculum_codes: Mapped[list[str]] = mapped_column(JSON, default=list)
    curriculum_notes: Mapped[str | None] = mapped_column(Text)
    adaptation_notes: Mapped[dict | None] = mapped_column(JSON)
    content_th: Mapped[str | None] = mapped_column(Text)
    content_ms: Mapped[str | None] = mapped_column(Text)
    content_en: Mapped[str | None] = mapped_column(Text)
    type_specific: Mapped[dict] = mapped_column(JSON, default=dict)
    local_context: Mapped[str | None] = mapped_column(Text)
    classroom_use: Mapped[str | None] = mapped_column(Text)
    materials_needed: Mapped[str | None] = mapped_column(Text)
    safety_notes: Mapped[str | None] = mapped_column(Text)
    sensitive_tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    copyright_status: Mapped[str] = mapped_column(String(64), default="unchecked")
    quality_score: Mapped[int] = mapped_column(Integer, default=3)
    source_type: Mapped[str] = mapped_column(String(64), default="project_manual")
    source_confidence: Mapped[str] = mapped_column(String(32), default="medium")
    source_note: Mapped[str | None] = mapped_column(Text)
    vector_status: Mapped[str] = mapped_column(String(64), default="not_embedded", index=True)
    github_path: Mapped[str | None] = mapped_column(String(512))
    github_commit_sha: Mapped[str | None] = mapped_column(String(128))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KnowledgeItemVersion(Base):
    __tablename__ = "knowledge_item_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    knowledge_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    version_number: Mapped[int] = mapped_column(Integer)
    snapshot: Mapped[dict] = mapped_column(JSON)
    change_summary: Mapped[str | None] = mapped_column(Text)
    change_type: Mapped[str] = mapped_column(String(64))
    changed_by_admin_id: Mapped[UUID | None] = mapped_column(ForeignKey("admin_users.id"))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class KnowledgeChunk(Base, TimestampMixin):
    __tablename__ = "knowledge_chunks"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    knowledge_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    chunk_text: Mapped[str] = mapped_column(Text)
    language: Mapped[str | None] = mapped_column(String(16))
    region_id: Mapped[UUID | None] = mapped_column(ForeignKey("regions.id"), index=True)
    school_id: Mapped[UUID | None] = mapped_column(ForeignKey("schools.id"), index=True)
    subject: Mapped[str] = mapped_column(String(64), index=True)
    topic: Mapped[str | None] = mapped_column(String(255), index=True)
    grade_min: Mapped[int] = mapped_column(Integer, index=True)
    grade_max: Mapped[int] = mapped_column(Integer, index=True)
    embedding_provider: Mapped[str | None] = mapped_column(String(64))
    embedding_model: Mapped[str | None] = mapped_column(String(128))
    embedding_dimensions: Mapped[int | None] = mapped_column(Integer)
    # Vector column will be added once the concrete embedding dimension is selected in migration.
    embedding_json: Mapped[list[float] | None] = mapped_column(JSON)
    active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

