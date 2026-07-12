from datetime import UTC, datetime, timedelta

from app.models import StudyPlan, StudyPlanItem, Task, TaskPriority, TaskStatus
from app.services.task_service import apply_task_status, generate_tasks_from_plan


def test_generate_tasks_from_plan_marks_today_task_high_priority():
    plan = StudyPlan(
        id="plan-1",
        user_id="user-1",
        goal="完成期末复习",
        course_ids=["course-1"],
        deadline=datetime.now(UTC) + timedelta(days=3),
        daily_minutes=90,
        risk_level="LOW",
    )
    item = StudyPlanItem(
        id="item-1",
        plan_id="plan-1",
        user_id="user-1",
        course_id="course-1",
        title="复习极限定义",
        description="完成讲义和例题。",
        scheduled_date=datetime.now(UTC).date(),
        estimated_minutes=45,
        sort_order=1,
    )

    tasks = generate_tasks_from_plan(plan=plan, items=[item])

    assert len(tasks) == 1
    assert tasks[0].source_id == "item-1"
    assert tasks[0].priority == TaskPriority.HIGH
    assert tasks[0].risk_message is not None


def test_generate_tasks_from_plan_raises_priority_for_high_risk_plan():
    plan = StudyPlan(
        id="plan-1",
        user_id="user-1",
        goal="冲刺复习",
        course_ids=["course-1"],
        deadline=datetime.now(UTC) + timedelta(days=7),
        daily_minutes=30,
        risk_level="HIGH",
        risk_message="时间不足。",
    )
    item = StudyPlanItem(
        id="item-1",
        plan_id="plan-1",
        user_id="user-1",
        course_id="course-1",
        title="完成综合练习",
        scheduled_date=(datetime.now(UTC) + timedelta(days=5)).date(),
        estimated_minutes=60,
        sort_order=1,
    )

    tasks = generate_tasks_from_plan(plan=plan, items=[item])

    assert tasks[0].priority == TaskPriority.HIGH
    assert "时间不足" in tasks[0].risk_message


def test_apply_task_status_sets_completion_timestamp_and_clears_cancelation():
    task = Task(
        user_id="user-1",
        course_id="course-1",
        title="复习极限",
        due_date=datetime.now(UTC).date(),
        estimated_minutes=45,
        priority=TaskPriority.MEDIUM,
        canceled_at=datetime.now(UTC),
    )

    apply_task_status(task, TaskStatus.DONE)

    assert task.status == TaskStatus.DONE
    assert task.completed_at is not None
    assert task.canceled_at is None


def test_apply_task_status_can_reopen_done_task():
    task = Task(
        user_id="user-1",
        course_id="course-1",
        title="复习极限",
        due_date=datetime.now(UTC).date(),
        estimated_minutes=45,
        priority=TaskPriority.MEDIUM,
        status=TaskStatus.DONE,
        completed_at=datetime.now(UTC),
    )

    apply_task_status(task, TaskStatus.TODO)

    assert task.status == TaskStatus.TODO
    assert task.completed_at is None
    assert task.canceled_at is None
