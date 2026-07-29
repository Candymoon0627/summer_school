from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db.models.knowledge import KnowledgeChunk, KnowledgeItem, KnowledgeItemVersion

APPROVED_RAG_STATUSES = {
    "approved_school_private",
    "approved_region_shared",
    "approved_global_shared",
}


class KnowledgeRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_item(self, **kwargs) -> KnowledgeItem:
        item = KnowledgeItem(**kwargs)
        self.db.add(item)
        self.db.flush()
        return item

    def get_item(self, item_id: UUID) -> KnowledgeItem | None:
        return self.db.get(KnowledgeItem, item_id)

    def list_items(self, limit: int = 100) -> list[KnowledgeItem]:
        return list(
            self.db.scalars(
                select(KnowledgeItem)
                .where(KnowledgeItem.is_deleted.is_(False))
                .order_by(KnowledgeItem.created_at.desc())
                .limit(limit)
            )
        )

    def review_status_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            select(KnowledgeItem.review_status, func.count())
            .where(KnowledgeItem.is_deleted.is_(False))
            .group_by(KnowledgeItem.review_status)
        ).all()
        return {status: count for status, count in rows}

    def vector_status_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            select(KnowledgeItem.vector_status, func.count())
            .where(KnowledgeItem.is_deleted.is_(False))
            .group_by(KnowledgeItem.vector_status)
        ).all()
        return {status: count for status, count in rows}

    def list_versions(self, item_id: UUID) -> list[KnowledgeItemVersion]:
        return list(
            self.db.scalars(
                select(KnowledgeItemVersion)
                .where(KnowledgeItemVersion.knowledge_item_id == item_id)
                .order_by(KnowledgeItemVersion.version_number.desc())
            )
        )

    def create_version(
        self,
        *,
        item: KnowledgeItem,
        snapshot: dict,
        change_type: str,
        change_summary: str | None = None,
        changed_by_admin_id: UUID | None = None,
    ) -> KnowledgeItemVersion:
        latest = self.latest_version(item.id)
        version_number = 1 if latest is None else latest.version_number + 1
        version = KnowledgeItemVersion(
            knowledge_item_id=item.id,
            version_number=version_number,
            snapshot=snapshot,
            change_type=change_type,
            change_summary=change_summary,
            changed_by_admin_id=changed_by_admin_id,
            created_at=datetime.now(UTC),
        )
        self.db.add(version)
        self.db.flush()
        return version

    def latest_version(self, item_id: UUID) -> KnowledgeItemVersion | None:
        return self.db.scalar(
            select(KnowledgeItemVersion)
            .where(KnowledgeItemVersion.knowledge_item_id == item_id)
            .order_by(KnowledgeItemVersion.version_number.desc())
            .limit(1)
        )

    def get_version(self, item_id: UUID, version_number: int) -> KnowledgeItemVersion | None:
        return self.db.scalar(
            select(KnowledgeItemVersion).where(
                KnowledgeItemVersion.knowledge_item_id == item_id,
                KnowledgeItemVersion.version_number == version_number,
            )
        )

    def chunks_for_item(self, item_id: UUID) -> list[KnowledgeChunk]:
        return list(
            self.db.scalars(select(KnowledgeChunk).where(KnowledgeChunk.knowledge_item_id == item_id))
        )

    def active_chunks(self, limit: int = 1000) -> list[KnowledgeChunk]:
        return list(
            self.db.scalars(
                select(KnowledgeChunk).where(KnowledgeChunk.active.is_(True)).limit(limit)
            )
        )

    def replace_chunks(self, item: KnowledgeItem, chunks: list[KnowledgeChunk]) -> None:
        existing = self.db.scalars(
            select(KnowledgeChunk).where(KnowledgeChunk.knowledge_item_id == item.id)
        )
        for chunk in existing:
            chunk.active = False
        for chunk in chunks:
            self.db.add(chunk)
        self.db.flush()

    def search_allowed_chunks(
        self,
        *,
        school_id: UUID,
        region_id: UUID,
        subject: str,
        grade: int,
        topic: str,
        limit: int = 30,
    ) -> list[KnowledgeChunk]:
        scope_filter = or_(
            and_(
                KnowledgeItem.visibility_scope == "private_school",
                KnowledgeItem.owner_school_id == school_id,
            ),
            and_(
                KnowledgeItem.visibility_scope == "shared_region",
                KnowledgeItem.owner_region_id == region_id,
            ),
            KnowledgeItem.visibility_scope == "shared_global",
        )
        del topic
        statement = (
            select(KnowledgeChunk)
            .join(KnowledgeItem, KnowledgeItem.id == KnowledgeChunk.knowledge_item_id)
            .where(
                KnowledgeChunk.active.is_(True),
                KnowledgeItem.is_deleted.is_(False),
                KnowledgeItem.review_status.in_(APPROVED_RAG_STATUSES),
                scope_filter,
                KnowledgeChunk.subject == subject,
                KnowledgeChunk.grade_min <= grade,
                KnowledgeChunk.grade_max >= grade,
            )
            .limit(limit)
        )
        return list(self.db.scalars(statement))
