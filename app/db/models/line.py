from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LineEvent(Base):
    __tablename__ = "line_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    event_key: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    line_user_id: Mapped[str | None] = mapped_column(String(255), index=True)
    message_id: Mapped[str | None] = mapped_column(String(255), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    processed_status: Mapped[str] = mapped_column(String(64), default="received")
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class LineMessageDelivery(Base):
    __tablename__ = "line_message_deliveries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    teacher_id: Mapped[UUID | None] = mapped_column(ForeignKey("teachers.id"), index=True)
    lesson_request_id: Mapped[UUID | None] = mapped_column(ForeignKey("lesson_requests.id"))
    message_type: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(64), default="queued")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

