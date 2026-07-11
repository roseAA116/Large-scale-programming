from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import (
    Course,
    Material,
    MaterialStatus,
    StudyPlan,
    StudyPlanItem,
    StudyPlanItemStatus,
    StudyPlanStatus,
)
from app.schemas.study_plan import (
    StudyPlanCreate,
    StudyPlanItemRead,
    StudyPlanRead,
    StudyPlanUpdate,
)


@dataclass(frozen=True)
class GeneratedPlanItem:
    course_id: str
    title: str
    description: str
    scheduled_date: date
    estimated_minutes: int
    sort_order: int


class StudyPlanService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_plan(self, *, user_id: str, payload: StudyPlanCreate) -> StudyPlanRead:
        deadline = _normalize_deadline(payload.deadline)
        _ensure_future_deadline(deadline)
        courses = await self._load_owned_courses(user_id=user_id, course_ids=payload.course_ids)
        ready_counts = await self._ready_material_counts(
            user_id=user_id,
            course_ids=list(courses.keys()),
        )
        generated_items, risk_level, risk_message = generate_plan_items(
            course_ids=payload.course_ids,
            course_names={course_id: course.name for course_id, course in courses.items()},
            ready_material_counts=ready_counts,
            goal=payload.goal,
            deadline=deadline,
            daily_minutes=payload.daily_minutes,
        )
        plan = StudyPlan(
            user_id=user_id,
            goal=payload.goal,
            course_ids=payload.course_ids,
            deadline=deadline,
            daily_minutes=payload.daily_minutes,
            risk_level=risk_level,
            risk_message=risk_message,
        )
        self.db.add(plan)
        await self.db.flush()
        self.db.add_all(
            [
                StudyPlanItem(
                    plan_id=plan.id,
                    user_id=user_id,
                    course_id=item.course_id,
                    title=item.title,
                    description=item.description,
                    scheduled_date=item.scheduled_date,
                    estimated_minutes=item.estimated_minutes,
                    sort_order=item.sort_order,
                )
                for item in generated_items
            ]
        )
        await self.db.commit()
        await self.db.refresh(plan)
        return await self.read_plan(user_id=user_id, plan_id=plan.id)

    async def list_plans(
        self,
        *,
        user_id: str,
        page: int,
        page_size: int,
        status: StudyPlanStatus | None = None,
    ) -> tuple[list[StudyPlanRead], int]:
        statement = select(StudyPlan).where(
            StudyPlan.user_id == user_id,
            StudyPlan.deleted_at.is_(None),
        )
        count_statement = select(func.count()).select_from(StudyPlan).where(
            StudyPlan.user_id == user_id,
            StudyPlan.deleted_at.is_(None),
        )
        if status:
            statement = statement.where(StudyPlan.status == status)
            count_statement = count_statement.where(StudyPlan.status == status)

        total = await self.db.scalar(count_statement) or 0
        plans = (
            await self.db.scalars(
                statement.order_by(StudyPlan.updated_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return [await self._to_read(plan, include_items=True) for plan in plans], total

    async def read_plan(self, *, user_id: str, plan_id: str) -> StudyPlanRead:
        plan = await self._get_owned_plan(user_id=user_id, plan_id=plan_id)
        return await self._to_read(plan, include_items=True)

    async def update_plan(
        self,
        *,
        user_id: str,
        plan_id: str,
        payload: StudyPlanUpdate,
    ) -> StudyPlanRead:
        plan = await self._get_owned_plan(user_id=user_id, plan_id=plan_id)
        updates = payload.model_dump(exclude_unset=True)
        if "deadline" in updates and updates["deadline"] is not None:
            updates["deadline"] = _normalize_deadline(updates["deadline"])
            _ensure_future_deadline(updates["deadline"])

        for field, value in updates.items():
            setattr(plan, field, value)
        await self.db.commit()
        await self.db.refresh(plan)
        return await self._to_read(plan, include_items=True)

    async def update_item_status(
        self,
        *,
        user_id: str,
        plan_id: str,
        item_id: str,
        status: StudyPlanItemStatus,
    ) -> StudyPlanRead:
        await self._get_owned_plan(user_id=user_id, plan_id=plan_id)
        item = await self.db.scalar(
            select(StudyPlanItem).where(
                StudyPlanItem.id == item_id,
                StudyPlanItem.plan_id == plan_id,
                StudyPlanItem.user_id == user_id,
            )
        )
        if item is None:
            raise AppError("PLAN_ITEM_NOT_FOUND", "Study plan item not found.", status_code=404)

        item.status = status
        item.completed_at = datetime.now(UTC) if status == StudyPlanItemStatus.DONE else None
        await self.db.commit()
        return await self.read_plan(user_id=user_id, plan_id=plan_id)

    async def _load_owned_courses(
        self,
        *,
        user_id: str,
        course_ids: list[str],
    ) -> dict[str, Course]:
        courses = (
            await self.db.scalars(
                select(Course).where(
                    Course.id.in_(course_ids),
                    Course.user_id == user_id,
                    Course.deleted_at.is_(None),
                )
            )
        ).all()
        course_by_id = {course.id: course for course in courses}
        missing = [course_id for course_id in course_ids if course_id not in course_by_id]
        if missing:
            raise AppError(
                "PLAN_COURSE_NOT_FOUND",
                "One or more courses are not available.",
                status_code=404,
                details={"course_ids": missing},
            )
        return course_by_id

    async def _ready_material_counts(
        self,
        *,
        user_id: str,
        course_ids: list[str],
    ) -> dict[str, int]:
        rows = (
            await self.db.execute(
                select(Material.course_id, func.count(Material.id))
                .where(
                    Material.user_id == user_id,
                    Material.course_id.in_(course_ids),
                    Material.deleted_at.is_(None),
                    Material.status == MaterialStatus.READY,
                )
                .group_by(Material.course_id)
            )
        ).all()
        return {course_id: count for course_id, count in rows}

    async def _get_owned_plan(self, *, user_id: str, plan_id: str) -> StudyPlan:
        plan = await self.db.scalar(
            select(StudyPlan).where(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id,
                StudyPlan.deleted_at.is_(None),
            )
        )
        if plan is None:
            raise AppError("PLAN_NOT_FOUND", "Study plan not found.", status_code=404)
        return plan

    async def _to_read(self, plan: StudyPlan, *, include_items: bool) -> StudyPlanRead:
        items: list[StudyPlanItem] = []
        if include_items:
            items = (
                await self.db.scalars(
                    select(StudyPlanItem)
                    .where(StudyPlanItem.plan_id == plan.id, StudyPlanItem.user_id == plan.user_id)
                    .order_by(StudyPlanItem.scheduled_date.asc(), StudyPlanItem.sort_order.asc())
                )
            ).all()
        data = StudyPlanRead.model_validate(plan)
        data.items = [StudyPlanItemRead.model_validate(item) for item in items]
        return data


def generate_plan_items(
    *,
    course_ids: list[str],
    course_names: dict[str, str],
    ready_material_counts: dict[str, int],
    goal: str,
    deadline: datetime,
    daily_minutes: int,
) -> tuple[list[GeneratedPlanItem], str, str | None]:
    dates = _study_dates_until(deadline)
    blocks_per_day = max(1, min(len(course_ids), daily_minutes // 30))
    minutes_per_block = max(15, daily_minutes // blocks_per_day)
    items: list[GeneratedPlanItem] = []
    cursor = 0

    for day_index, scheduled_date in enumerate(dates):
        for block_index in range(blocks_per_day):
            course_id = course_ids[cursor % len(course_ids)]
            cursor += 1
            course_name = course_names.get(course_id, "课程")
            material_count = ready_material_counts.get(course_id, 0)
            title = _plan_title(day_index=day_index, course_name=course_name, goal=goal)
            description = _plan_description(
                material_count=material_count,
                block_index=block_index,
                blocks_per_day=blocks_per_day,
            )
            items.append(
                GeneratedPlanItem(
                    course_id=course_id,
                    title=title,
                    description=description,
                    scheduled_date=scheduled_date,
                    estimated_minutes=minutes_per_block,
                    sort_order=len(items) + 1,
                )
            )

    total_minutes = len(dates) * daily_minutes
    minimum_minutes = max(180 * len(course_ids), 45 * len(dates))
    if total_minutes < minimum_minutes:
        return (
            items,
            "HIGH",
            "可用时间偏紧，建议降低目标范围、延后截止时间，或提高每日学习时长。",
        )
    if daily_minutes < 45:
        return items, "MEDIUM", "每日可用时间较少，计划已拆成小块，请保持连续执行。"
    if any(ready_material_counts.get(course_id, 0) == 0 for course_id in course_ids):
        return items, "MEDIUM", "部分课程还没有 READY 资料，计划会先安排目标复盘和资料整理。"
    return items, "LOW", None


def _study_dates_until(deadline: datetime) -> list[date]:
    today = datetime.now(UTC).date()
    end_date = deadline.date()
    day_count = max(1, (end_date - today).days + 1)
    return [today + timedelta(days=offset) for offset in range(day_count)]


def _plan_title(*, day_index: int, course_name: str, goal: str) -> str:
    verbs = ["梳理", "精读", "练习", "回顾", "自测"]
    verb = verbs[day_index % len(verbs)]
    compact_goal = " ".join(goal.split())
    if len(compact_goal) > 28:
        compact_goal = f"{compact_goal[:27]}…"
    return f"{verb}{course_name}：{compact_goal}"


def _plan_description(*, material_count: int, block_index: int, blocks_per_day: int) -> str:
    if material_count > 0:
        return (
            f"围绕已索引的 {material_count} 份 READY 资料学习，"
            f"完成当天第 {block_index + 1}/{blocks_per_day} 个学习块。"
        )
    return (
        "先整理课程目标、教材目录和待补资料；资料 READY 后可继续用问答模块核对理解。"
    )


def _normalize_deadline(deadline: datetime) -> datetime:
    if deadline.tzinfo is None:
        return deadline.replace(tzinfo=UTC)
    return deadline.astimezone(UTC)


def _ensure_future_deadline(deadline: datetime) -> None:
    if deadline <= datetime.now(UTC):
        raise AppError(
            "PLAN_INVALID_DEADLINE",
            "学习计划截止时间必须晚于当前时间。",
            status_code=422,
        )
