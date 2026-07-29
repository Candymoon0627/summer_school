from uuid import UUID

from app.db.session import SessionLocal
from app.services.lesson_generation import LessonGenerationService


def generate_lesson_job(lesson_request_id: str) -> None:
    with SessionLocal() as db:
        LessonGenerationService(db).generate(UUID(lesson_request_id))

