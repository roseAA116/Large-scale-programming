from typing import Annotated

from fastapi import APIRouter, Query, Request

from app.api.deps import CurrentUser, DbSession
from app.core.responses import ok
from app.schemas import CourseSummaryCreate, CourseSummaryPage
from app.services.summary_service import SummaryService

router = APIRouter(tags=["summaries"])


@router.post("/courses/{course_id}/summaries")
async def generate_course_summary(
    course_id: str,
    payload: CourseSummaryCreate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = SummaryService(db)
    summary = await service.generate_summary(
        user_id=current_user.id,
        course_id=course_id,
        material_id=payload.material_id,
    )
    return ok(request, summary.model_dump(mode="json"), status_code=201)


@router.get("/summaries")
async def list_course_summaries(
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    course_id: Annotated[str | None, Query()] = None,
    material_id: Annotated[str | None, Query()] = None,
):
    service = SummaryService(db)
    summaries, total = await service.list_summaries(
        user_id=current_user.id,
        course_id=course_id,
        material_id=material_id,
    )
    payload = CourseSummaryPage(items=summaries, total=total)
    return ok(request, payload.model_dump(mode="json"))


@router.get("/summaries/{summary_id}")
async def read_course_summary(
    summary_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = SummaryService(db)
    summary = await service.read_summary(user_id=current_user.id, summary_id=summary_id)
    return ok(request, summary.model_dump(mode="json"))
