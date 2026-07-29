from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.admin import AuditLog


class AuditRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        *,
        action: str,
        target_type: str,
        target_id: str,
        actor_admin_id: UUID | None = None,
        before_snapshot: dict | None = None,
        after_snapshot: dict | None = None,
    ) -> AuditLog:
        log = AuditLog(
            actor_admin_id=actor_admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            before_snapshot=before_snapshot,
            after_snapshot=after_snapshot,
            created_at=datetime.now(UTC),
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list_recent(self, limit: int = 100) -> list[AuditLog]:
        return list(
            self.db.scalars(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit))
        )
