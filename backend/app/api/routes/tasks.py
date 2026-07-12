from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.responses import ok
from app.models import TaskStatus
from app.schemas import TaskCreate, TaskPage, TaskPostpone, TaskUpdate
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("")
async def create_task(
    payload: TaskCreate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = TaskService(db)
    task = await service.create_task(user_id=current_user.id, payload=payload)
    return ok(request, task.model_dump(mode="json"), status_code=201)


@router.get("")
async def list_tasks(
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    course_id: Annotated[str | None, Query(min_length=1)] = None,
    status: Annotated[TaskStatus | None, Query()] = None,
    due_from: Annotated[date | None, Query()] = None,
    due_to: Annotated[date | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 50,
):
    service = TaskService(db)
    tasks, total = await service.list_tasks(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        course_id=course_id,
        status=status,
        due_from=due_from,
        due_to=due_to,
    )
    payload = TaskPage(items=tasks, total=total, page=page, page_size=page_size)
    return ok(request, payload.model_dump(mode="json"))


@router.patch("/{task_id}")
async def update_task(
    task_id: str,
    payload: TaskUpdate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = TaskService(db)
    task = await service.update_task(user_id=current_user.id, task_id=task_id, payload=payload)
    return ok(request, task.model_dump(mode="json"))


@router.post("/{task_id}/complete")
async def complete_task(
    task_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = TaskService(db)
    task = await service.complete_task(user_id=current_user.id, task_id=task_id)
    return ok(request, task.model_dump(mode="json"))


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = TaskService(db)
    task = await service.cancel_task(user_id=current_user.id, task_id=task_id)
    return ok(request, task.model_dump(mode="json"))


@router.post("/{task_id}/postpone")
async def postpone_task(
    task_id: str,
    payload: TaskPostpone,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = TaskService(db)
    task = await service.postpone_task(user_id=current_user.id, task_id=task_id, payload=payload)
    return ok(request, task.model_dump(mode="json"))
