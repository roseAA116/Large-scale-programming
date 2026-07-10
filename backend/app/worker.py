import asyncio

from redis.exceptions import RedisError

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.services.material_processing import process_index_material, process_parse_material
from app.services.task_queue import (
    TASK_INDEX_MATERIAL,
    TASK_PARSE_MATERIAL,
    Job,
    get_sync_redis_client,
    requeue_job,
)

logger = get_logger(__name__)


def main() -> None:
    configure_logging()
    logger.info("worker_started", extra={"queue": settings.worker_queue_name})
    client = get_sync_redis_client()
    try:
        while True:
            try:
                item = client.brpop(
                    settings.worker_queue_name,
                    timeout=settings.worker_poll_timeout_seconds,
                )
            except RedisError:
                logger.exception("worker_redis_poll_failed")
                continue
            if item is None:
                continue
            _, raw_job = item
            job = Job.from_json(raw_job)
            run_job(job)
    finally:
        client.close()


def run_job(job: Job) -> None:
    logger.info(
        "job_started",
        extra={"job_name": job.name, "payload": job.payload, "attempts": job.attempts},
    )
    try:
        if job.name == TASK_PARSE_MATERIAL:
            asyncio.run(process_parse_material(job.payload["material_id"]))
        elif job.name == TASK_INDEX_MATERIAL:
            asyncio.run(process_index_material(job.payload["material_id"]))
        else:
            logger.error("job_unknown", extra={"job_name": job.name})
            return
    except Exception:
        failed_attempts = job.attempts + 1
        logger.exception(
            "job_failed",
            extra={
                "job_name": job.name,
                "payload": job.payload,
                "failed_attempts": failed_attempts,
            },
        )
        if failed_attempts < settings.worker_max_retries:
            requeue_job(job)
        return
    logger.info("job_completed", extra={"job_name": job.name, "payload": job.payload})


if __name__ == "__main__":
    main()
