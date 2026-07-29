from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.media import MediaAsset


class MediaRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_lesson_docx_asset(
        self,
        *,
        lesson_request_id: UUID,
        object_key: str,
        original_filename: str,
        storage_provider: str,
        file_size: int | None,
        purpose: str = "lesson_docx",
    ) -> MediaAsset:
        asset = MediaAsset(
            owner_type="lesson_request",
            owner_id=str(lesson_request_id),
            media_type="docx",
            purpose=purpose,
            object_key=object_key,
            original_filename=original_filename,
            mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            file_size=file_size,
            storage_provider=storage_provider,
            retention_policy="90_days",
            expires_at=datetime.now(UTC) + timedelta(days=90),
            created_at=datetime.now(UTC),
        )
        self.db.add(asset)
        self.db.flush()
        return asset

    def lesson_docx_assets(self, lesson_request_id: UUID) -> list[MediaAsset]:
        return list(
            self.db.scalars(
                select(MediaAsset)
                .where(
                    MediaAsset.owner_type == "lesson_request",
                    MediaAsset.owner_id == str(lesson_request_id),
                    MediaAsset.media_type == "docx",
                    MediaAsset.deleted_at.is_(None),
                )
                .order_by(MediaAsset.created_at.asc())
            )
        )
