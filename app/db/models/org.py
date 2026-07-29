from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class Region(Base, TimestampMixin):
    __tablename__ = "regions"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    country_code: Mapped[str] = mapped_column(String(2), default="th", index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    districts: Mapped[list["District"]] = relationship(back_populates="region")
    schools: Mapped[list["School"]] = relationship(back_populates="region")


class District(Base, TimestampMixin):
    __tablename__ = "districts"
    __table_args__ = (UniqueConstraint("region_id", "code", name="uq_district_region_code"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(ForeignKey("regions.id"), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    region: Mapped[Region] = relationship(back_populates="districts")


class School(Base, TimestampMixin):
    __tablename__ = "schools"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    region_id: Mapped[UUID] = mapped_column(ForeignKey("regions.id"), index=True)
    district_id: Mapped[UUID | None] = mapped_column(ForeignKey("districts.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255))
    school_code_hash: Mapped[str] = mapped_column(String(255), index=True)
    school_code_rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    school_type: Mapped[str | None] = mapped_column(String(64))
    resource_level: Mapped[str] = mapped_column(String(32), default="low")
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    region: Mapped[Region] = relationship(back_populates="schools")


class Teacher(Base, TimestampMixin):
    __tablename__ = "teachers"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    line_user_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(255))
    school_id: Mapped[UUID] = mapped_column(ForeignKey("schools.id"), index=True)
    region_id: Mapped[UUID] = mapped_column(ForeignKey("regions.id"), index=True)
    language_preference: Mapped[str] = mapped_column(String(16), default="th")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    consent_version_id: Mapped[UUID | None] = mapped_column(ForeignKey("consent_versions.id"))
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    note: Mapped[str | None] = mapped_column(Text)

