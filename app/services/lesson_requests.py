from sqlalchemy.orm import Session

from app.repositories.lesson import LessonRepository
from app.repositories.org import OrgRepository
from app.services.language import DEFAULT_LANGUAGE
from app.services.language import text as localized_text
from app.services.queue import QueueService
from app.services.request_parser import LessonRequestParser


class LessonRequestService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.orgs = OrgRepository(db)
        self.lessons = LessonRepository(db)
        self.parser = LessonRequestParser()

    def create_from_teacher_text(
        self,
        *,
        line_user_id: str,
        text: str,
        enqueue: bool = True,
        language: str = DEFAULT_LANGUAGE,
    ) -> dict:
        teacher = self.orgs.get_teacher_by_line_user_id(line_user_id)
        if not teacher:
            return {
                "status": "needs_binding",
                "message": localized_text("needs_binding", language),
            }
        if teacher.status != "active":
            return {"status": "disabled", "message": localized_text("account_disabled", language)}

        parsed = self.parser.parse(text)
        if parsed["missing"]:
            return {
                "status": "missing_fields",
                "missing": parsed["missing"],
                "message": localized_text("missing_lesson_fields", language),
            }

        lesson_request = self.lessons.create_lesson_request(
            teacher_id=teacher.id,
            school_id=teacher.school_id,
            region_id=teacher.region_id,
            raw_user_input=text,
            subject=parsed["subject"],
            grade=parsed["grade"],
            topic=parsed["topic"],
        )
        self.db.commit()
        queue_job_id = None
        if enqueue:
            try:
                queue_job_id = QueueService().enqueue_lesson_generation(str(lesson_request.id))
            except Exception:  # noqa: BLE001 - any queue backend failure should not lose the saved request.
                lesson_request.status = "queue_failed"
                lesson_request.error_message = "Failed to enqueue lesson generation."
                self.db.commit()
                return {
                    "status": "queue_failed",
                    "lesson_request_id": str(lesson_request.id),
                    "message": localized_text("queue_failed", language),
                }
        return {
            "status": "queued",
            "lesson_request_id": str(lesson_request.id),
            "queue_job_id": queue_job_id,
            "message": localized_text("lesson_started", language),
        }
