import logging
import time
from uuid import UUID

from app.db.models.lesson import LessonRequest
from app.db.session import SessionLocal
from app.services.lesson_generation import LessonGenerationService

logger = logging.getLogger(__name__)

LESSON_REQUEST_VISIBILITY_ATTEMPTS = 10
LESSON_REQUEST_VISIBILITY_DELAY_SECONDS = 0.5


def generate_lesson_job(lesson_request_id: str) -> None:
    lesson_uuid = UUID(lesson_request_id)
    with SessionLocal() as db:
        if not _wait_for_lesson_request(db, lesson_uuid):
            logger.warning("Lesson request was not visible before generation: %s", lesson_uuid)
        LessonGenerationService(db).generate(lesson_uuid)


def _wait_for_lesson_request(
    db,
    lesson_request_id: UUID,
    *,
    attempts: int = LESSON_REQUEST_VISIBILITY_ATTEMPTS,
    delay_seconds: float = LESSON_REQUEST_VISIBILITY_DELAY_SECONDS,
) -> bool:
    for attempt in range(attempts):
        db.expire_all()
        if db.get(LessonRequest, lesson_request_id) is not None:
            return True
        db.rollback()
        if attempt < attempts - 1:
            time.sleep(delay_seconds)
    return False
