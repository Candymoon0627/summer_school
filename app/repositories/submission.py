from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models.submission import Submission, SubmissionReview


class SubmissionRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, **kwargs) -> Submission:
        submission = Submission(**kwargs)
        self.db.add(submission)
        self.db.flush()
        return submission

    def get(self, submission_id: UUID) -> Submission | None:
        return self.db.get(Submission, submission_id)

    def list(self, *, limit: int = 100, status: str | None = None) -> list[Submission]:
        statement = select(Submission).order_by(Submission.created_at.desc()).limit(limit)
        if status:
            statement = statement.where(Submission.status == status)
        return list(self.db.scalars(statement))

    def status_counts(self) -> dict[str, int]:
        rows = self.db.execute(
            select(Submission.status, func.count()).group_by(Submission.status)
        ).all()
        return {status: count for status, count in rows}

    def create_review(
        self,
        *,
        submission_id: UUID,
        stage: int,
        action: str,
        before_status: str | None,
        after_status: str | None,
        reviewer_username: str | None = None,
        reviewer_role: str | None = None,
        note: str | None = None,
    ) -> SubmissionReview:
        from datetime import UTC, datetime

        review = SubmissionReview(
            submission_id=submission_id,
            stage=stage,
            action=action,
            reviewer_username=reviewer_username,
            reviewer_role=reviewer_role,
            note=note,
            before_status=before_status,
            after_status=after_status,
            created_at=datetime.now(UTC),
        )
        self.db.add(review)
        self.db.flush()
        return review

    def reviews_for_submission(self, submission_id: UUID) -> list[SubmissionReview]:
        return list(
            self.db.scalars(
                select(SubmissionReview)
                .where(SubmissionReview.submission_id == submission_id)
                .order_by(SubmissionReview.created_at.asc())
            )
        )
