from datetime import UTC, datetime, timedelta

from app.services.study_plan_service import generate_plan_items


def test_generate_plan_items_stays_before_deadline():
    deadline = datetime.now(UTC) + timedelta(days=2)

    items, risk_level, risk_message = generate_plan_items(
        course_ids=["course-1", "course-2"],
        course_names={"course-1": "高等数学", "course-2": "大学物理"},
        ready_material_counts={"course-1": 3, "course-2": 2},
        goal="完成期末复习",
        deadline=deadline,
        daily_minutes=120,
    )

    assert items
    assert all(item.scheduled_date <= deadline.date() for item in items)
    assert {item.course_id for item in items} == {"course-1", "course-2"}
    assert risk_level == "LOW"
    assert risk_message is None


def test_generate_plan_items_warns_when_daily_time_is_tight():
    deadline = datetime.now(UTC) + timedelta(days=1)

    items, risk_level, risk_message = generate_plan_items(
        course_ids=["course-1", "course-2"],
        course_names={"course-1": "高等数学", "course-2": "大学物理"},
        ready_material_counts={"course-1": 0, "course-2": 0},
        goal="冲刺复习",
        deadline=deadline,
        daily_minutes=15,
    )

    assert items
    assert risk_level == "HIGH"
    assert risk_message is not None
