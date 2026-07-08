from fastapi import APIRouter, Request

from app.core.responses import ok
from app.db.session import check_database_connection
from app.services.cache import check_redis_connection
from app.services.storage import storage_settings_ready

router = APIRouter()


@router.get("/healthz")
async def healthz(request: Request):
    return ok(
        request,
        {
            "status": "ok",
            "service": "course-agent-backend",
        },
    )


@router.get("/readyz")
async def readyz(request: Request):
    checks = {
        "database": await check_database_connection(),
        "redis": await check_redis_connection(),
        "object_storage_config": storage_settings_ready(),
    }
    ready = all(item["ok"] for item in checks.values())
    return ok(request, {"ready": ready, "checks": checks}, status_code=200 if ready else 503)
