from redis.asyncio import Redis

from app.core.config import settings


def get_redis_client() -> Redis:
    return Redis.from_url(settings.redis_url, decode_responses=True)


async def check_redis_connection() -> dict:
    client = get_redis_client()
    try:
        await client.ping()
        return {"ok": True}
    except Exception as exc:
        return {"ok": False, "error": exc.__class__.__name__}
    finally:
        await client.aclose()

