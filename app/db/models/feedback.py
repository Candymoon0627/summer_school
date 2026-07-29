from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LessonFeedback(Base):
    __tablename__ = "lesson_feedback"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lesson_request_id: Mapped[UUID] = mapped_column(ForeignKey("lesson_requests.id"), index=True)
    teacher_id: Mapped[UUID] = mapped_column(ForeignKey("teachers.id"), index=True)
    rating: Mapped[str] = mapped_column(String(64))
    reason_code: Mapped[str | None] = mapped_column(String(64))
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    teacher_id: Mapped[UUID | None] = mapped_column(ForeignKey("teachers.id"), index=True)
    school_id: Mapped[UUID | None] = mapped_column(ForeignKey("schools.id"), index=True)
    category: Mapped[str] = mapped_column(String(64), default="general")
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(64), default="open", index=True)
    assigned_admin_id: Mapped[UUID | None] = mapped_column(ForeignKey("admin_users.id"))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

