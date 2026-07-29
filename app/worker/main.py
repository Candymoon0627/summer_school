import logging
import os

from redis import Redis
from rq import SimpleWorker, Worker

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.sentry import init_sentry

QUEUES = ["lesson_generation", "embedding", "publication", "default"]


def main() -> None:
    configure_logging()
    init_sentry()
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url)
    logging.getLogger(__name__).info("Starting RQ worker for queues: %s", ", ".join(QUEUES))
    worker_cls = SimpleWorker if os.name == "nt" else Worker
    worker_cls(QUEUES, connection=redis).work()


if __name__ == "__main__":
    main()
