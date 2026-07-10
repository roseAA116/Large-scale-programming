from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.core.errors import AppError
from app.core.logging import get_logger

logger = get_logger(__name__)

TASK_PARSE_MATERIAL = "parse_material"
TASK_INDEX_MATERIAL = "index_material"


@dataclass(slots=True)
class Job:
    name: str
    payload: dict[str, Any]
    attempts: int = 0

    @classmethod
    def from_json(cls, raw: str | bytes) -> Job:
        data = json.loads(raw)
        return cls(
            name=data["name"],
            payload=data.get("payload", {}),
            attempts=int(data.get("attempts", 0)),
        )

    def to_json(self) -> str:
        return json.dumps(
            {"name": self.name, "payload": self.payload, "attempts": self.attempts},
            ensure_ascii=False,
        )


def get_sync_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_parse_material(material_id: str) -> None:
    enqueue_job(TASK_PARSE_MATERIAL, {"material_id": material_id})


def enqueue_index_material(material_id: str) -> None:
    enqueue_job(TASK_INDEX_MATERIAL, {"material_id": material_id})


def enqueue_job(name: str, payload: dict[str, Any], *, attempts: int = 0) -> None:
    job = Job(name=name, payload=payload, attempts=attempts)
    client = get_sync_redis_client()
    try:
        client.lpush(settings.worker_queue_name, job.to_json())
    except RedisError as exc:
        raise AppError(
            "JOB_QUEUE_UNAVAILABLE",
            "Background job queue is unavailable.",
            status_code=503,
            details={"job_name": name},
        ) from exc
    finally:
        client.close()
    logger.info("job_enqueued", extra={"job_name": name, "payload": payload, "attempts": attempts})


def requeue_job(job: Job) -> None:
    enqueue_job(job.name, job.payload, attempts=job.attempts + 1)
