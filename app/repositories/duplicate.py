from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.duplicate import DuplicateCandidate


class DuplicateRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_candidate(
        self,
        *,
        knowledge_item_id: UUID,
        candidate_item_id: UUID,
        similarity_score: float,
    ) -> DuplicateCandidate:
        candidate = DuplicateCandidate(
            knowledge_item_id=knowledge_item_id,
            candidate_item_id=candidate_item_id,
            similarity_score=similarity_score,
            created_at=datetime.now(UTC),
        )
        self.db.add(candidate)
        self.db.flush()
        return candidate

    def list_for_item(self, knowledge_item_id: UUID) -> list[DuplicateCandidate]:
        return list(
            self.db.scalars(
                select(DuplicateCandidate)
                .where(DuplicateCandidate.knowledge_item_id == knowledge_item_id)
                .order_by(DuplicateCandidate.similarity_score.desc())
            )
        )

