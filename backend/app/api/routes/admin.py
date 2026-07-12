from datetime import UTC, datetime

from fastapi import APIRouter, Request
from redis.exceptions import RedisError
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession, ensure_admin
from app.core.config import settings
from app.core.responses import ok
from app.models import Course, Material, MaterialStatus, StudyPlan, Task, User
from app.schemas import (
    AdminMaterialRead,
    AdminQueueStatusRead,
    AdminSystemStatusRead,
    AdminUserRead,
)
from app.services.task_queue import get_sync_redis_client

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/status")
async def read_admin_status(current_user: CurrentUser, db: DbSession, request: Request):
    ensure_admin(current_user)
    payload = AdminSystemStatusRead(
        users=await _count(db, User),
        courses=await _count(db, Course),
        materials=await _count(db, Material),
        failed_materials=await _count(db, Material, Material.status == MaterialStatus.FAILED),
        tasks=await _count(db, Task),
        plans=await _count(db, StudyPlan),
        generated_at=datetime.now(UTC),
    )
    return ok(request, payload.model_dump(mode="json"))


@router.get("/users")
async def list_admin_users(current_user: CurrentUser, db: DbSession, request: Request):
    ensure_admin(current_user)
    users = (await db.scalars(select(User).order_by(User.created_at.desc()).limit(100))).all()
    payload = [
        AdminUserRead(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_active=user.is_active,
            is_admin=user.is_admin,
            created_at=user.created_at,
        ).model_dump(mode="json")
        for user in users
    ]
    return ok(request, payload)


@router.get("/materials/failed")
async def list_failed_materials(current_user: CurrentUser, db: DbSession, request: Request):
    ensure_admin(current_user)
    materials = (
        await db.scalars(
            select(Material)
            .where(Material.status == MaterialStatus.FAILED)
            .order_by(Material.updated_at.desc())
            .limit(100)
        )
    ).all()
    payload = [
        AdminMaterialRead(
            id=material.id,
            user_id=material.user_id,
            course_id=material.course_id,
            title=material.title,
            status=str(material.status),
            error_message=material.error_message,
            updated_at=material.updated_at,
        ).model_dump(mode="json")
        for material in materials
    ]
    return ok(request, payload)


@router.get("/queues")
async def read_queue_status(current_user: CurrentUser, request: Request):
    ensure_admin(current_user)
    client = get_sync_redis_client()
    try:
        pending = client.llen(settings.worker_queue_name)
        retry = client.llen(settings.worker_retry_queue_name)
        payload = AdminQueueStatusRead(
            queue_name=settings.worker_queue_name,
            retry_queue_name=settings.worker_retry_queue_name,
            pending_count=pending,
            retry_count=retry,
            available=True,
        )
    except RedisError as exc:
        payload = AdminQueueStatusRead(
            queue_name=settings.worker_queue_name,
            retry_queue_name=settings.worker_retry_queue_name,
            pending_count=None,
            retry_count=None,
            available=False,
            error=exc.__class__.__name__,
        )
    finally:
        client.close()
    return ok(request, payload.model_dump(mode="json"))


async def _count(db: DbSession, model, *conditions) -> int:
    statement = select(func.count()).select_from(model)
    if conditions:
        statement = statement.where(*conditions)
    return int(await db.scalar(statement) or 0)
