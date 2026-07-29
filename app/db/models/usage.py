from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.mixins import TimestampMixin


class ModelCallLog(Base):
    __tablename__ = "model_call_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    lesson_request_id: Mapped[UUID | None] = mapped_column(ForeignKey("lesson_requests.id"))
    provider: Mapped[str] = mapped_column(String(64), index=True)
    model_name: Mapped[str] = mapped_column(String(128), index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    prompt_version: Mapped[str | None] = mapped_column(String(128))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    cached_input_tokens: Mapped[int | None] = mapped_column(Integer)
    cost_estimated: Mapped[float | None] = mapped_column(Float)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(64), default="succeeded")
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UsageCounter(Base, TimestampMixin):
    __tablename__ = "usage_counters"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    scope_type: Mapped[str] = mapped_column(String(64), index=True)
    scope_id: Mapped[str] = mapped_column(String(128), index=True)
    metric: Mapped[str] = mapped_column(String(64), index=True)
    period: Mapped[str] = mapped_column(String(32), index=True)
    count: Mapped[int] = mapped_column(Integer, default=0)
    token_input: Mapped[int] = mapped_column(Integer, default=0)
    token_output: Mapped[int] = mapped_column(Integer, default=0)
    cost_estimated: Mapped[float] = mapped_column(Float, default=0)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    key: Mapped[str] = mapped_column(String(128), index=True)
    enabled: Mapped[bool]
    scope_type: Mapped[str] = mapped_column(String(64), default="global", index=True)
    scope_id: Mapped[str | None] = mapped_column(String(128), index=True)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_by: Mapped[str | None] = mapped_column(String(128))
