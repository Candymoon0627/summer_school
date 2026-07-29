from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Submission(Base, TimestampMixin):
    __tablename__ = "submissions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    teacher_id: Mapped[UUID | None] = mapped_column(ForeignKey("teachers.id"), index=True)
    school_id: Mapped[UUID | None] = mapped_column(ForeignKey("schools.id"), index=True)
    region_id: Mapped[UUID | None] = mapped_column(ForeignKey("regions.id"), index=True)
    knowledge_item_id: Mapped[UUID | None] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    status: Mapped[str] = mapped_column(String(64), default="draft", index=True)
    current_review_stage: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[str] = mapped_column(String(64), default="admin_manual", index=True)
    source_message_id: Mapped[str | None] = mapped_column(String(255), index=True)
    raw_input: Mapped[str | None] = mapped_column(Text)
    visibility_scope: Mapped[str] = mapped_column(String(64), default="shared_region", index=True)
    knowledge_type: Mapped[str] = mapped_column(String(64), default="local_example", index=True)
    subject: Mapped[str] = mapped_column(String(64), default="general", index=True)
    topic: Mapped[str] = mapped_column(String(255), default="teacher contribution", index=True)
    title: Mapped[str] = mapped_column(String(255))
    target_grade: Mapped[int | None] = mapped_column(Integer, index=True)
    grade_min: Mapped[int] = mapped_column(Integer, default=1, index=True)
    grade_max: Mapped[int] = mapped_column(Integer, default=12, index=True)
    content_th: Mapped[str | None] = mapped_column(Text)
    content_ms: Mapped[str | None] = mapped_column(Text)
    content_en: Mapped[str | None] = mapped_column(Text)
    local_context: Mapped[str | None] = mapped_column(Text)
    classroom_use: Mapped[str | None] = mapped_column(Text)
    safety_notes: Mapped[str | None] = mapped_column(Text)
    source_note: Mapped[str | None] = mapped_column(Text)
    sensitive_status: Mapped[str] = mapped_column(String(64), default="unchecked", index=True)
    copyright_status: Mapped[str] = mapped_column(String(64), default="unchecked", index=True)
    duplicate_status: Mapped[str] = mapped_column(String(64), default="unchecked", index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    first_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    second_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubmissionReview(Base):
    __tablename__ = "submission_reviews"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    submission_id: Mapped[UUID] = mapped_column(ForeignKey("submissions.id"), index=True)
    stage: Mapped[int] = mapped_column(Integer, default=0)
    action: Mapped[str] = mapped_column(String(64), index=True)
    reviewer_username: Mapped[str | None] = mapped_column(String(255))
    reviewer_role: Mapped[str | None] = mapped_column(String(64))
    note: Mapped[str | None] = mapped_column(Text)
    before_status: Mapped[str | None] = mapped_column(String(64))
    after_status: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
