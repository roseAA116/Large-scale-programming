from datetime import UTC, datetime

from fastapi import APIRouter, Request
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.responses import ok
from app.models import ChatSession, Course, Material, MaterialStatus, StudyPlan, Task, TaskStatus
from app.schemas import (
    DashboardChatRead,
    DashboardPlanRead,
    DashboardSummaryRead,
    DashboardTaskRead,
)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
async def read_dashboard_summary(current_user: CurrentUser, db: DbSession, request: Request):
    course_count = await db.scalar(
        select(func.count()).select_from(Course).where(
            Course.user_id == current_user.id,
            Course.deleted_at.is_(None),
        )
    )
    material_count = await db.scalar(
        select(func.count()).select_from(Material).where(
            Material.user_id == current_user.id,
            Material.deleted_at.is_(None),
        )
    )
    ready_material_count = await db.scalar(
        select(func.count()).select_from(Material).where(
            Material.user_id == current_user.id,
            Material.deleted_at.is_(None),
            Material.status == MaterialStatus.READY,
        )
    )
    today = datetime.now(UTC).date()
    tasks = (
        await db.scalars(
            select(Task)
            .where(
                Task.user_id == current_user.id,
                Task.due_date == today,
                Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
            )
            .order_by(Task.priority.desc(), Task.created_at.asc())
            .limit(8)
        )
    ).all()
    chats = (
        await db.scalars(
            select(ChatSession)
            .where(ChatSession.user_id == current_user.id, ChatSession.deleted_at.is_(None))
            .order_by(ChatSession.updated_at.desc())
            .limit(5)
        )
    ).all()
    plans = (
        await db.scalars(
            select(StudyPlan)
            .where(StudyPlan.user_id == current_user.id, StudyPlan.deleted_at.is_(None))
            .order_by(StudyPlan.updated_at.desc())
            .limit(5)
        )
    ).all()

    material_total = int(material_count or 0)
    payload = DashboardSummaryRead(
        course_count=int(course_count or 0),
        material_count=material_total,
        ready_material_count=int(ready_material_count or 0),
        ready_material_ratio=round((ready_material_count or 0) / material_total, 4)
        if material_total
        else 0,
        today_tasks=[
            DashboardTaskRead(
                id=task.id,
                course_id=task.course_id,
                title=task.title,
                due_date=task.due_date,
                priority=str(task.priority),
                status=str(task.status),
            )
            for task in tasks
        ],
        recent_chats=[
            DashboardChatRead(
                id=chat.id,
                course_id=chat.course_id,
                title=chat.title,
                updated_at=chat.updated_at,
            )
            for chat in chats
        ],
        recent_plans=[
            DashboardPlanRead(
                id=plan.id,
                goal=plan.goal,
                deadline=plan.deadline,
                risk_level=plan.risk_level,
                status=str(plan.status),
            )
            for plan in plans
        ],
    )
    return ok(request, payload.model_dump(mode="json"))
