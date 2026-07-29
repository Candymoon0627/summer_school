from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.line import LineEvent


class LineEventRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def mark_received(
        self,
        *,
        event_key: str,
        line_user_id: str | None,
        message_id: str | None,
        event_type: str,
    ) -> bool:
        event = LineEvent(
            event_key=event_key,
            line_user_id=line_user_id,
            message_id=message_id,
            event_type=event_type,
            processed_status="received",
            created_at=datetime.now(UTC),
        )
        self.db.add(event)
        try:
            self.db.flush()
        except IntegrityError:
            self.db.rollback()
            return False
        return True

