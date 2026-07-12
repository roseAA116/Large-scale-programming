from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import (
    Course,
    StudyPlan,
    StudyPlanItem,
    Task,
    TaskPriority,
    TaskStatus,
)
from app.schemas.task import (
    TaskCreate,
    TaskPostpone,
    TaskPreviewItemRead,
    TaskPreviewRead,
    TaskRead,
    TaskUpdate,
)


@dataclass(frozen=True)
class GeneratedTask:
    source_id: str
    plan_id: str
    course_id: str
    title: str
    description: str | None
    due_date: date
    estimated_minutes: int
    priority: TaskPriority
    risk_message: str | None


class TaskService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def preview_plan_tasks(
        self,
        *,
        user_id: str,
        plan_id: str,
        plan_item_ids: list[str] | None = None,
    ) -> TaskPreviewRead:
        plan, items = await self._load_plan_items(
            user_id=user_id,
            plan_id=plan_id,
            plan_item_ids=plan_item_ids,
        )
        generated = generate_tasks_from_plan(plan=plan, items=items)
        existing_source_ids = await self._existing_source_ids(
            user_id=user_id,
            source_ids=[task.source_id for task in generated],
        )
        previews = [
            TaskPreviewItemRead(
                source_id=task.source_id,
                plan_id=task.plan_id,
                course_id=task.course_id,
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                estimated_minutes=task.estimated_minutes,
                priority=task.priority,
                risk_message=task.risk_message,
                already_added=task.source_id in existing_source_ids,
            )
            for task in generated
        ]
        return TaskPreviewRead(
            items=previews,
            risk_level=plan.risk_level,
            risk_message=plan.risk_message,
            total_estimated_minutes=sum(task.estimated_minutes for task in generated),
            already_added_count=sum(1 for item in previews if item.already_added),
        )

    async def create_plan_tasks(
        self,
        *,
        user_id: str,
        plan_id: str,
        plan_item_ids: list[str] | None = None,
    ) -> list[TaskRead]:
        plan, items = await self._load_plan_items(
            user_id=user_id,
            plan_id=plan_id,
            plan_item_ids=plan_item_ids,
        )
        generated = generate_tasks_from_plan(plan=plan, items=items)
        existing_source_ids = await self._existing_source_ids(
            user_id=user_id,
            source_ids=[task.source_id for task in generated],
        )

        tasks = [
            Task(
                user_id=user_id,
                course_id=task.course_id,
                plan_id=task.plan_id,
                source_id=task.source_id,
                title=task.title,
                description=task.description,
                due_date=task.due_date,
                estimated_minutes=task.estimated_minutes,
                priority=task.priority,
                status=TaskStatus.TODO,
            )
            for task in generated
            if task.source_id not in existing_source_ids
        ]
        if tasks:
            self.db.add_all(tasks)
            await self.db.commit()
            for task in tasks:
                await self.db.refresh(task)
        return [TaskRead.model_validate(task) for task in tasks]

    async def create_task(self, *, user_id: str, payload: TaskCreate) -> TaskRead:
        await self._ensure_course_owner(user_id=user_id, course_id=payload.course_id)
        task = Task(
            user_id=user_id,
            course_id=payload.course_id,
            title=payload.title,
            description=payload.description,
            due_date=payload.due_date,
            estimated_minutes=payload.estimated_minutes,
            priority=payload.priority,
            status=TaskStatus.TODO,
        )
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def list_tasks(
        self,
        *,
        user_id: str,
        page: int,
        page_size: int,
        course_id: str | None = None,
        status: TaskStatus | None = None,
        due_from: date | None = None,
        due_to: date | None = None,
    ) -> tuple[list[TaskRead], int]:
        statement = select(Task).where(Task.user_id == user_id)
        count_statement = select(func.count()).select_from(Task).where(Task.user_id == user_id)
        if course_id:
            statement = statement.where(Task.course_id == course_id)
            count_statement = count_statement.where(Task.course_id == course_id)
        if status:
            statement = statement.where(Task.status == status)
            count_statement = count_statement.where(Task.status == status)
        if due_from:
            statement = statement.where(Task.due_date >= due_from)
            count_statement = count_statement.where(Task.due_date >= due_from)
        if due_to:
            statement = statement.where(Task.due_date <= due_to)
            count_statement = count_statement.where(Task.due_date <= due_to)

        total = await self.db.scalar(count_statement) or 0
        tasks = (
            await self.db.scalars(
                statement.order_by(Task.due_date.asc(), Task.priority.desc(), Task.created_at.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).all()
        return [TaskRead.model_validate(task) for task in tasks], total

    async def update_task(
        self,
        *,
        user_id: str,
        task_id: str,
        payload: TaskUpdate,
    ) -> TaskRead:
        task = await self._get_owned_task(user_id=user_id, task_id=task_id)
        updates = payload.model_dump(exclude_unset=True)
        if "course_id" in updates and updates["course_id"] is not None:
            await self._ensure_course_owner(user_id=user_id, course_id=updates["course_id"])

        status = updates.pop("status", None)
        for field, value in updates.items():
            setattr(task, field, value)
        if status is not None:
            apply_task_status(task, status)

        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def complete_task(self, *, user_id: str, task_id: str) -> TaskRead:
        task = await self._get_owned_task(user_id=user_id, task_id=task_id)
        apply_task_status(task, TaskStatus.DONE)
        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def cancel_task(self, *, user_id: str, task_id: str) -> TaskRead:
        task = await self._get_owned_task(user_id=user_id, task_id=task_id)
        apply_task_status(task, TaskStatus.CANCELED)
        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def postpone_task(
        self,
        *,
        user_id: str,
        task_id: str,
        payload: TaskPostpone,
    ) -> TaskRead:
        task = await self._get_owned_task(user_id=user_id, task_id=task_id)
        task.due_date = payload.due_date
        if task.status == TaskStatus.CANCELED:
            apply_task_status(task, TaskStatus.TODO)
        await self.db.commit()
        await self.db.refresh(task)
        return TaskRead.model_validate(task)

    async def _get_owned_task(self, *, user_id: str, task_id: str) -> Task:
        task = await self.db.scalar(select(Task).where(Task.id == task_id, Task.user_id == user_id))
        if task is None:
            raise AppError("TASK_NOT_FOUND", "Task not found.", status_code=404)
        return task

    async def _load_plan_items(
        self,
        *,
        user_id: str,
        plan_id: str,
        plan_item_ids: list[str] | None,
    ) -> tuple[StudyPlan, list[StudyPlanItem]]:
        plan = await self.db.scalar(
            select(StudyPlan).where(
                StudyPlan.id == plan_id,
                StudyPlan.user_id == user_id,
                StudyPlan.deleted_at.is_(None),
            )
        )
        if plan is None:
            raise AppError("PLAN_NOT_FOUND", "Study plan not found.", status_code=404)

        statement = (
            select(StudyPlanItem)
            .where(StudyPlanItem.plan_id == plan_id, StudyPlanItem.user_id == user_id)
            .order_by(StudyPlanItem.scheduled_date.asc(), StudyPlanItem.sort_order.asc())
        )
        if plan_item_ids:
            statement = statement.where(StudyPlanItem.id.in_(plan_item_ids))

        items = (await self.db.scalars(statement)).all()
        if not items:
            raise AppError(
                "PLAN_TASK_SOURCE_EMPTY",
                "No study plan items are available.",
                status_code=404,
            )
        if plan_item_ids and len(items) != len(plan_item_ids):
            found_ids = {item.id for item in items}
            missing = [item_id for item_id in plan_item_ids if item_id not in found_ids]
            raise AppError(
                "PLAN_ITEM_NOT_FOUND",
                "One or more study plan items are not available.",
                status_code=404,
                details={"plan_item_ids": missing},
            )
        return plan, list(items)

    async def _existing_source_ids(self, *, user_id: str, source_ids: list[str]) -> set[str]:
        if not source_ids:
            return set()
        existing = (
            await self.db.scalars(
                select(Task.source_id).where(
                    Task.user_id == user_id,
                    Task.source_id.in_(source_ids),
                )
            )
        ).all()
        return {source_id for source_id in existing if source_id is not None}

    async def _ensure_course_owner(self, *, user_id: str, course_id: str) -> None:
        course_id = await self.db.scalar(
            select(Course.id).where(
                Course.id == course_id,
                Course.user_id == user_id,
                Course.deleted_at.is_(None),
            )
        )
        if course_id is None:
            raise AppError("TASK_COURSE_NOT_FOUND", "Course not found.", status_code=404)


def generate_tasks_from_plan(*, plan: StudyPlan, items: list[StudyPlanItem]) -> list[GeneratedTask]:
    today = datetime.now(UTC).date()
    return [
        GeneratedTask(
            source_id=item.id,
            plan_id=plan.id,
            course_id=item.course_id,
            title=_task_title(item.title),
            description=_task_description(item.description, plan.goal),
            due_date=item.scheduled_date,
            estimated_minutes=item.estimated_minutes,
            priority=_task_priority(
                due_date=item.scheduled_date,
                estimated_minutes=item.estimated_minutes,
                plan_risk_level=plan.risk_level,
                today=today,
            ),
            risk_message=_task_risk_message(
                due_date=item.scheduled_date,
                plan_risk_level=plan.risk_level,
                today=today,
            ),
        )
        for item in items
    ]


def apply_task_status(task: Task, status: TaskStatus) -> None:
    task.status = status
    if status == TaskStatus.DONE:
        task.completed_at = datetime.now(UTC)
        task.canceled_at = None
        return
    if status == TaskStatus.CANCELED:
        task.canceled_at = datetime.now(UTC)
        task.completed_at = None
        return
    task.completed_at = None
    task.canceled_at = None


def _task_title(title: str) -> str:
    cleaned = " ".join(title.split())
    return cleaned[:160] or "学习任务"


def _task_description(description: str | None, goal: str) -> str:
    base = " ".join((description or "").split())
    if base:
        return base[:1200]
    compact_goal = " ".join(goal.split())
    return f"围绕学习目标完成本计划项：{compact_goal}"[:1200]


def _task_priority(
    *,
    due_date: date,
    estimated_minutes: int,
    plan_risk_level: str,
    today: date,
) -> TaskPriority:
    days_left = (due_date - today).days
    normalized_risk = plan_risk_level.upper()
    if days_left <= 0 or (normalized_risk == "HIGH" and estimated_minutes >= 60):
        return TaskPriority.HIGH
    if days_left <= 2 or estimated_minutes >= 90 or normalized_risk in {"MEDIUM", "HIGH"}:
        return TaskPriority.MEDIUM
    return TaskPriority.LOW


def _task_risk_message(*, due_date: date, plan_risk_level: str, today: date) -> str | None:
    days_left = (due_date - today).days
    if days_left < 0:
        return "计划日期已过期，加入待办后建议优先处理或重新调整日期。"
    if days_left == 0:
        return "任务安排在今天，建议加入待办后优先执行。"
    if plan_risk_level.upper() == "HIGH":
        return "原学习计划存在时间不足风险，此任务优先级已相应提高。"
    return None
