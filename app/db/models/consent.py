from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class ConsentVersion(Base, TimestampMixin):
    __tablename__ = "consent_versions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    version: Mapped[str] = mapped_column(String(64), unique=True)
    language: Mapped[str] = mapped_column(String(16), default="th")
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class TeacherConsent(Base):
    __tablename__ = "teacher_consents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    teacher_id: Mapped[UUID] = mapped_column(ForeignKey("teachers.id"), index=True)
    consent_version_id: Mapped[UUID] = mapped_column(ForeignKey("consent_versions.id"))
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ip_address: Mapped[str | None] = mapped_column(String(64))
    line_user_id_snapshot: Mapped[str] = mapped_column(String(255))

