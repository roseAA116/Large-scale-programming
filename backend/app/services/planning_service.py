from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import Course, Material, MaterialStatus, Task, TaskPriority, TaskStatus
from app.schemas.planning import CoursePlanningStatRead, MultiCoursePlanAnalysisRead


class PlanningService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def analyze_multi_course_plan(
        self,
        *,
        user_id: str,
        course_ids: list[str],
        deadline: datetime | None,
        daily_minutes: int,
    ) -> MultiCoursePlanAnalysisRead:
        courses = await self._load_courses(user_id=user_id, course_ids=course_ids)
        task_rows = await self._task_stats(user_id=user_id, course_ids=course_ids)
        ready_counts = await self._ready_counts(user_id=user_id, course_ids=course_ids)

        days = _days_until(deadline)
        available_minutes = days * daily_minutes
        raw_stats = []
        for course_id in course_ids:
            course = courses[course_id]
            task_count, total_minutes, earliest_due, high_count = task_rows.get(
                course_id,
                (0, 0, None, 0),
            )
            urgency_score = _urgency_score(
                task_count=task_count,
                total_minutes=total_minutes,
                earliest_due=earliest_due,
                high_count=high_count,
                ready_count=ready_counts.get(course_id, 0),
            )
            raw_stats.append(
                {
                    "course_id": course_id,
                    "course_name": course.name,
                    "task_count": task_count,
                    "total_estimated_minutes": total_minutes,
                    "earliest_due_date": earliest_due.isoformat() if earliest_due else None,
                    "high_priority_count": high_count,
                    "ready_material_count": ready_counts.get(course_id, 0),
                    "urgency_score": urgency_score,
                }
            )

        total_score = sum(item["urgency_score"] for item in raw_stats) or len(raw_stats)
        course_stats = []
        for item in raw_stats:
            ratio = item["urgency_score"] / total_score if total_score else 1 / len(raw_stats)
            course_stats.append(
                CoursePlanningStatRead(
                    **item,
                    allocation_minutes=max(15, round(available_minutes * ratio)),
                    allocation_ratio=round(ratio, 4),
                )
            )

        total_task_minutes = sum(item.total_estimated_minutes for item in course_stats)
        risk_level = "LOW"
        risk_message = None
        if total_task_minutes > available_minutes:
            risk_level = "HIGH"
            risk_message = "当前多课程任务估时超过可用学习时间，建议延后截止时间或缩小目标范围。"
        elif total_task_minutes > available_minutes * 0.8:
            risk_level = "MEDIUM"
            risk_message = "当前多课程安排较紧，建议优先处理高优先级和临近截止任务。"

        names = "、".join(course.name for course in courses.values())
        return MultiCoursePlanAnalysisRead(
            course_stats=course_stats,
            total_task_minutes=total_task_minutes,
            available_minutes=available_minutes,
            risk_level=risk_level,
            risk_message=risk_message,
            suggested_goal=f"综合规划 {names} 的复习、作业与资料整理",
        )

    async def _load_courses(self, *, user_id: str, course_ids: list[str]) -> dict[str, Course]:
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
                "MULTI_PLAN_COURSE_NOT_FOUND",
                "One or more courses are not available.",
                status_code=404,
                details={"course_ids": missing},
            )
        return course_by_id

    async def _task_stats(self, *, user_id: str, course_ids: list[str]) -> dict[str, tuple]:
        rows = (
            await self.db.execute(
                select(
                    Task.course_id,
                    func.count(Task.id),
                    func.coalesce(func.sum(Task.estimated_minutes), 0),
                    func.min(Task.due_date),
                    func.sum(case((Task.priority == TaskPriority.HIGH, 1), else_=0)),
                )
                .where(
                    Task.user_id == user_id,
                    Task.course_id.in_(course_ids),
                    Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
                )
                .group_by(Task.course_id)
            )
        ).all()
        return {
            course_id: (int(count or 0), int(minutes or 0), earliest_due, int(high_count or 0))
            for course_id, count, minutes, earliest_due, high_count in rows
        }

    async def _ready_counts(self, *, user_id: str, course_ids: list[str]) -> dict[str, int]:
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
        return {course_id: int(count or 0) for course_id, count in rows}


def _days_until(deadline: datetime | None) -> int:
    if deadline is None:
        return 14
    normalized = deadline if deadline.tzinfo else deadline.replace(tzinfo=UTC)
    return max(1, (normalized.date() - datetime.now(UTC).date()).days + 1)


def _urgency_score(
    *,
    task_count: int,
    total_minutes: int,
    earliest_due,
    high_count: int,
    ready_count: int,
) -> float:
    score = 1.0 + task_count * 1.4 + total_minutes / 60 + high_count * 2.2 + ready_count * 0.35
    if earliest_due is not None:
        days_left = (earliest_due - datetime.now(UTC).date()).days
        score += max(0, 12 - days_left)
    return round(score, 4)
