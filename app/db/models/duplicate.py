from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DuplicateCandidate(Base):
    __tablename__ = "duplicate_candidates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    knowledge_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    candidate_item_id: Mapped[UUID] = mapped_column(ForeignKey("knowledge_items.id"), index=True)
    similarity_score: Mapped[float] = mapped_column(Float)
    resolved_action: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

