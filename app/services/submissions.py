from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.admin_auth import AdminPrincipal
from app.db.models.knowledge import KnowledgeItem
from app.db.models.submission import Submission
from app.repositories.audit import AuditRepository
from app.repositories.knowledge import KnowledgeRepository
from app.repositories.org import OrgRepository
from app.repositories.submission import SubmissionRepository
from app.schemas.submission import SubmissionCreate, SubmissionUpdate
from app.services.knowledge import KnowledgeService
from app.services.request_parser import LessonRequestParser

DRAFT_STATUSES = {"draft", "needs_revision"}
REVIEWABLE_STATUSES = {"pending_review", "first_approved"}
TOPIC_SUBJECTS = {
    "fractions": "math",
    "equivalent fractions": "math",
    "area": "math",
    "perimeter": "math",
    "water cycle": "science",
    "evaporation": "science",
    "plant parts": "science",
    "forces": "science",
}


@dataclass(frozen=True)
class SubmissionPrefixMatch:
    is_submission: bool
    body: str


class SubmissionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.submissions = SubmissionRepository(db)
        self.orgs = OrgRepository(db)
        self.knowledge = KnowledgeRepository(db)
        self.audit = AuditRepository(db)
        self.parser = LessonRequestParser()

    def create_admin_submission(
        self,
        request: SubmissionCreate,
        *,
        current_admin: AdminPrincipal | None = None,
    ) -> Submission:
        submission = self.submissions.create(
            teacher_id=UUID(request.teacher_id) if request.teacher_id else None,
            school_id=UUID(request.school_id) if request.school_id else None,
            region_id=UUID(request.region_id) if request.region_id else None,
            status="draft",
            current_review_stage=0,
            source_type="admin_manual",
            raw_input=None,
            visibility_scope=request.visibility_scope,
            knowledge_type=request.knowledge_type,
            subject=request.subject,
            topic=request.topic,
            title=request.title.strip(),
            target_grade=request.target_grade,
            grade_min=request.grade_min,
            grade_max=request.grade_max,
            content_th=request.content_th,
            content_ms=request.content_ms,
            content_en=request.content_en,
            local_context=request.local_context,
            classroom_use=request.classroom_use,
            safety_notes=request.safety_notes,
            source_note=request.source_note,
        )
        self._record(
            submission,
            action="created",
            before_status=None,
            after_status=submission.status,
            current_admin=current_admin,
            note="Created from admin UI.",
        )
        if request.submit:
            self.submit_for_review(submission.id, current_admin=current_admin, commit=False)
        self.db.commit()
        return submission

    def create_line_text_submission(
        self,
        *,
        line_user_id: str,
        text: str,
        source_message_id: str | None = None,
    ) -> Submission:
        teacher = self.orgs.get_teacher_by_line_user_id(line_user_id)
        if not teacher:
            raise ValueError("Teacher is not bound.")
        body = detect_submission_text(text).body
        title = self._title_from_text(body)
        classification = self._classification_from_text(body, title)
        submission = self.submissions.create(
            teacher_id=teacher.id,
            school_id=teacher.school_id,
            region_id=teacher.region_id,
            status="pending_review",
            current_review_stage=1,
            source_type="line_text",
            source_message_id=source_message_id,
            raw_input=text,
            visibility_scope="shared_region",
            knowledge_type="local_example",
            subject=classification["subject"],
            topic=classification["topic"],
            title=title,
            target_grade=classification["target_grade"],
            grade_min=classification["grade_min"],
            grade_max=classification["grade_max"],
            content_th=body,
            source_note="Submitted by teacher from LINE text.",
            submitted_at=datetime.now(UTC),
        )
        self._record(
            submission,
            action="submitted",
            before_status=None,
            after_status=submission.status,
            note="Submitted from LINE text.",
        )
        self.db.commit()
        return submission

    def update_submission(
        self,
        submission_id: UUID | str,
        request: SubmissionUpdate,
        *,
        current_admin: AdminPrincipal | None = None,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        before = self.snapshot(submission)
        for field, value in request.model_dump(exclude_unset=True).items():
            setattr(submission, field, value)
        if submission.grade_min > submission.grade_max:
            raise ValueError("grade_min must be less than or equal to grade_max.")
        self.audit.create(
            action="submission_updated",
            target_type="submission",
            target_id=str(submission.id),
            before_snapshot=before,
            after_snapshot=self.snapshot(submission),
        )
        self._record(
            submission,
            action="updated",
            before_status=submission.status,
            after_status=submission.status,
            current_admin=current_admin,
            note="Updated submission content.",
        )
        self.db.commit()
        return submission

    def submit_for_review(
        self,
        submission_id: UUID | str,
        *,
        current_admin: AdminPrincipal | None = None,
        note: str | None = None,
        commit: bool = True,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        self._require_status(submission, DRAFT_STATUSES)
        before = submission.status
        submission.status = "pending_review"
        submission.current_review_stage = 1
        submission.submitted_at = datetime.now(UTC)
        self._record(
            submission,
            action="submitted",
            before_status=before,
            after_status=submission.status,
            current_admin=current_admin,
            note=note,
        )
        if commit:
            self.db.commit()
        return submission

    def first_approve(
        self,
        submission_id: UUID | str,
        *,
        current_admin: AdminPrincipal | None = None,
        note: str | None = None,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        self._require_status(submission, {"pending_review"})
        before = submission.status
        submission.status = "first_approved"
        submission.current_review_stage = 2
        submission.first_reviewed_at = datetime.now(UTC)
        self._record(
            submission,
            action="first_approved",
            before_status=before,
            after_status=submission.status,
            current_admin=current_admin,
            note=note,
        )
        self.db.commit()
        return submission

    def second_approve(
        self,
        submission_id: UUID | str,
        *,
        current_admin: AdminPrincipal | None = None,
        note: str | None = None,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        self._require_status(submission, {"first_approved"})
        before = submission.status
        submission.status = "second_approved"
        submission.current_review_stage = 2
        submission.second_reviewed_at = datetime.now(UTC)
        self._record(
            submission,
            action="second_approved",
            before_status=before,
            after_status=submission.status,
            current_admin=current_admin,
            note=note,
        )
        self.db.commit()
        return submission

    def request_revision(
        self,
        submission_id: UUID | str,
        *,
        current_admin: AdminPrincipal | None = None,
        note: str | None = None,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        self._require_status(submission, REVIEWABLE_STATUSES)
        before = submission.status
        submission.status = "needs_revision"
        submission.current_review_stage = 0
        self._record(
            submission,
            action="needs_revision",
            before_status=before,
            after_status=submission.status,
            current_admin=current_admin,
            note=note,
        )
        self.db.commit()
        return submission

    def reject(
        self,
        submission_id: UUID | str,
        *,
        current_admin: AdminPrincipal | None = None,
        note: str | None = None,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        self._require_status(submission, DRAFT_STATUSES | REVIEWABLE_STATUSES | {"second_approved"})
        before = submission.status
        submission.status = "rejected"
        self._record(
            submission,
            action="rejected",
            before_status=before,
            after_status=submission.status,
            current_admin=current_admin,
            note=note,
        )
        self.db.commit()
        return submission

    def publish_to_knowledge(
        self,
        submission_id: UUID | str,
        *,
        current_admin: AdminPrincipal | None = None,
    ) -> Submission:
        submission = self._get_or_raise(submission_id)
        self._require_status(submission, {"second_approved"})
        if submission.knowledge_item_id:
            raise ValueError("Submission has already been published to knowledge.")

        before = submission.status
        item = self._create_knowledge_item(submission)
        submission.knowledge_item_id = item.id
        submission.status = "published"
        submission.published_at = datetime.now(UTC)
        self._record(
            submission,
            action="published",
            before_status=before,
            after_status=submission.status,
            current_admin=current_admin,
            note=f"Created knowledge item {item.id}.",
        )
        KnowledgeService(self.db).rebuild_chunks_and_embedding(item.id, commit=False)
        submission.status = "embedded"
        submission.embedded_at = datetime.now(UTC)
        self._record(
            submission,
            action="embedded",
            before_status="published",
            after_status=submission.status,
            current_admin=current_admin,
            note=f"Embedded knowledge item {item.id}.",
        )
        self.db.commit()
        return submission

    def _create_knowledge_item(self, submission: Submission) -> KnowledgeItem:
        item = self.knowledge.create_item(
            owner_type="teacher",
            owner_school_id=submission.school_id,
            owner_region_id=submission.region_id,
            visibility_scope=submission.visibility_scope,
            review_status=self._knowledge_review_status(submission.visibility_scope),
            knowledge_type=submission.knowledge_type,
            subject=submission.subject,
            topic=submission.topic,
            title=submission.title,
            target_grade=submission.target_grade,
            grade_min=submission.grade_min,
            grade_max=submission.grade_max,
            grade_mode="exact" if submission.grade_min == submission.grade_max else "range",
            content_th=submission.content_th,
            content_ms=submission.content_ms,
            content_en=submission.content_en,
            local_context=submission.local_context,
            classroom_use=submission.classroom_use,
            safety_notes=submission.safety_notes,
            quality_score=3,
            source_type="teacher_submission",
            source_confidence="medium",
            source_note=submission.source_note or f"Teacher submission {submission.id}",
            copyright_status=submission.copyright_status,
            vector_status="not_embedded",
        )
        KnowledgeService(self.db).create_version(item, "created", f"Published from submission {submission.id}.")
        return item

    def _record(
        self,
        submission: Submission,
        *,
        action: str,
        before_status: str | None,
        after_status: str | None,
        current_admin: AdminPrincipal | None = None,
        note: str | None = None,
    ) -> None:
        self.submissions.create_review(
            submission_id=submission.id,
            stage=submission.current_review_stage,
            action=action,
            reviewer_username=current_admin.username if current_admin else None,
            reviewer_role=current_admin.role if current_admin else None,
            note=note,
            before_status=before_status,
            after_status=after_status,
        )
        self.audit.create(
            action=f"submission_{action}",
            target_type="submission",
            target_id=str(submission.id),
            before_snapshot={"status": before_status} if before_status else None,
            after_snapshot={"status": after_status, "stage": submission.current_review_stage},
        )

    def _get_or_raise(self, submission_id: UUID | str) -> Submission:
        if isinstance(submission_id, str):
            submission_id = UUID(submission_id)
        submission = self.submissions.get(submission_id)
        if not submission:
            raise ValueError(f"Submission not found: {submission_id}")
        return submission

    def _require_status(self, submission: Submission, allowed: set[str]) -> None:
        if submission.status not in allowed:
            allowed_text = ", ".join(sorted(allowed))
            raise ValueError(
                f"Submission {submission.id} is {submission.status}; expected one of: {allowed_text}."
            )

    def snapshot(self, submission: Submission) -> dict:
        return {
            "id": str(submission.id),
            "status": submission.status,
            "title": submission.title,
            "subject": submission.subject,
            "topic": submission.topic,
            "grade_min": submission.grade_min,
            "grade_max": submission.grade_max,
            "visibility_scope": submission.visibility_scope,
            "knowledge_item_id": str(submission.knowledge_item_id)
            if submission.knowledge_item_id
            else None,
        }

    def _title_from_text(self, text: str) -> str:
        first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
        if not first_line:
            return "Teacher contribution"
        return first_line[:120]

    def _classification_from_text(self, text: str, fallback_topic: str) -> dict:
        parsed = self.parser.parse(text)
        topic = parsed["topic"] or fallback_topic
        subject = parsed["subject"] or TOPIC_SUBJECTS.get(topic, "general")
        grade = parsed["grade"]
        return {
            "subject": subject,
            "topic": topic,
            "target_grade": grade,
            "grade_min": grade or 1,
            "grade_max": grade or 12,
        }

    def _knowledge_review_status(self, visibility_scope: str) -> str:
        if visibility_scope == "shared_global":
            return "approved_global_shared"
        if visibility_scope == "private_school":
            return "approved_school_private"
        return "approved_region_shared"


def detect_submission_text(text: str) -> SubmissionPrefixMatch:
    stripped = text.strip()
    prefixes = ("投稿:", "投稿：", "submit:", "submission:")
    lowered = stripped.lower()
    for prefix in prefixes:
        if lowered.startswith(prefix.lower()):
            return SubmissionPrefixMatch(is_submission=True, body=stripped[len(prefix) :].strip())
    return SubmissionPrefixMatch(is_submission=False, body=stripped)
