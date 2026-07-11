from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.responses import ok
from app.models import StudyPlanStatus
from app.schemas.study_plan import (
    StudyPlanCreate,
    StudyPlanItemUpdate,
    StudyPlanPage,
    StudyPlanUpdate,
)
from app.services.study_plan_service import StudyPlanService

router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("")
async def create_study_plan(
    payload: StudyPlanCreate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = StudyPlanService(db)
    plan = await service.create_plan(user_id=current_user.id, payload=payload)
    return ok(request, plan.model_dump(mode="json"), status_code=201)


@router.get("")
async def list_study_plans(
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    status: Annotated[StudyPlanStatus | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=50)] = 20,
):
    service = StudyPlanService(db)
    plans, total = await service.list_plans(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )
    payload = StudyPlanPage(items=plans, total=total, page=page, page_size=page_size)
    return ok(request, payload.model_dump(mode="json"))


@router.get("/{plan_id}")
async def read_study_plan(
    plan_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = StudyPlanService(db)
    plan = await service.read_plan(user_id=current_user.id, plan_id=plan_id)
    return ok(request, plan.model_dump(mode="json"))


@router.patch("/{plan_id}")
async def update_study_plan(
    plan_id: str,
    payload: StudyPlanUpdate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = StudyPlanService(db)
    plan = await service.update_plan(user_id=current_user.id, plan_id=plan_id, payload=payload)
    return ok(request, plan.model_dump(mode="json"))


@router.patch("/{plan_id}/items/{item_id}")
async def update_study_plan_item(
    plan_id: str,
    item_id: str,
    payload: StudyPlanItemUpdate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = StudyPlanService(db)
    plan = await service.update_item_status(
        user_id=current_user.id,
        plan_id=plan_id,
        item_id=item_id,
        status=payload.status,
    )
    return ok(request, plan.model_dump(mode="json"))
