from datetime import UTC, datetime

from redis import Redis
from rq import Queue, SimpleWorker

from app.db.models.lesson import LessonRequest
from app.db.session import SessionLocal
from app.schemas.admin import CreateSchoolRequest
from app.services.lesson_requests import LessonRequestService
from app.services.onboarding import OnboardingService

QUEUE_NAME = "lesson_generation"


def main() -> None:
    stamp = datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    line_user_id = f"rq-smoke-user-{stamp}"

    from app.core.config import get_settings

    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    redis.ping()
    queue = Queue(QUEUE_NAME, connection=redis)
    if queue.count:
        raise RuntimeError(
            f"Queue {QUEUE_NAME!r} already has {queue.count} job(s). "
            "Run a worker or clear stale test jobs before this smoke test."
        )
    print(f"PASS | Redis reachable | url={settings.redis_url}")

    with SessionLocal() as db:
        school = OnboardingService(db).create_school_with_code(
            CreateSchoolRequest(
                name=f"RQ Smoke Test School {stamp}",
                region_code="pattani",
                region_name="Pattani",
                country_code="th",
                resource_level="low",
            )
        )
        teacher = OnboardingService(db).bind_teacher_by_school_code(
            line_user_id=line_user_id,
            school_code=school.school_code,
            display_name="RQ Smoke Test Teacher",
        )
        if teacher is None:
            raise RuntimeError("Teacher binding failed.")
        print(f"PASS | database test teacher ready | teacher_id={teacher.teacher_id}")

        request = LessonRequestService(db).create_from_teacher_text(
            line_user_id=line_user_id,
            text="Grade 4 math fractions, 45 minutes, low-resource classroom",
            enqueue=True,
        )
        if request["status"] != "queued" or not request.get("queue_job_id"):
            raise RuntimeError(f"Lesson request was not enqueued: {request}")
        lesson_request_id = request["lesson_request_id"]
        queue_job_id = request["queue_job_id"]
        print(f"PASS | lesson request enqueued | lesson_request_id={lesson_request_id}")

        job = queue.fetch_job(queue_job_id)
        if job is None:
            raise RuntimeError(f"Queued job not found in Redis: {queue_job_id}")
        print(f"PASS | RQ job found | job_id={queue_job_id}")

        worker = SimpleWorker([queue], connection=redis)
        worker.work(burst=True, max_jobs=1, logging_level="WARNING")

        lesson = db.get(LessonRequest, lesson_request_id)
        if lesson is None:
            raise RuntimeError(f"Lesson request not found after worker run: {lesson_request_id}")
        db.refresh(lesson)
        if lesson.status != "completed" or not lesson.docx_media_asset_id:
            raise RuntimeError(
                "RQ worker did not complete lesson generation: "
                f"status={lesson.status}, docx_media_asset_id={lesson.docx_media_asset_id}"
            )
        print(
            "PASS | RQ worker completed lesson generation | "
            f"lesson_request_id={lesson.id} docx_media_asset_id={lesson.docx_media_asset_id}"
        )


if __name__ == "__main__":
    main()
