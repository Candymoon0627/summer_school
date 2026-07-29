import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class QueueService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def enqueue_lesson_generation(self, lesson_request_id: str) -> str:
        try:
            from redis import Redis
            from rq import Queue

            redis = Redis.from_url(self.settings.redis_url)
            queue = Queue("lesson_generation", connection=redis)
            job = queue.enqueue(
                "app.worker.jobs.generate_lesson_job",
                lesson_request_id,
                job_timeout=180,
                result_ttl=86400,
                failure_ttl=86400,
            )
            return job.id
        except Exception:
            logger.exception("Failed to enqueue lesson generation; leaving request queued.")
            raise
