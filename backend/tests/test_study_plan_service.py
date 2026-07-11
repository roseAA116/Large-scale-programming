from datetime import UTC, datetime, timedelta

import pytest

from app.services.study_plan_service import (
    StudyPlanService,
    coerce_agent_plan_payload,
    generate_plan_items,
)


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


def test_coerce_agent_plan_payload_accepts_structured_items():
    deadline = datetime.now(UTC) + timedelta(days=2)
    scheduled_date = datetime.now(UTC).date().isoformat()

    items, risk_level, risk_message = coerce_agent_plan_payload(
        payload={
            "risk_level": "medium",
            "risk_message": "资料较多，建议每天复盘。",
            "items": [
                {
                    "course_id": "course-1",
                    "title": "复习极限定义",
                    "description": "阅读讲义并整理 3 个典型题。",
                    "scheduled_date": scheduled_date,
                    "estimated_minutes": 45,
                }
            ],
        },
        course_ids=["course-1"],
        course_names={"course-1": "高等数学"},
        deadline=deadline,
        daily_minutes=120,
    )

    assert len(items) == 1
    assert items[0].course_id == "course-1"
    assert items[0].scheduled_date.isoformat() == scheduled_date
    assert risk_level == "MEDIUM"
    assert risk_message == "资料较多，建议每天复盘。"


def test_coerce_agent_plan_payload_rejects_unknown_courses():
    deadline = datetime.now(UTC) + timedelta(days=2)

    with pytest.raises(ValueError):
        coerce_agent_plan_payload(
            payload={
                "items": [
                    {
                        "course_id": "course-2",
                        "title": "复习",
                        "scheduled_date": datetime.now(UTC).date().isoformat(),
                        "estimated_minutes": 30,
                    }
                ]
            },
            course_ids=["course-1"],
            course_names={"course-1": "高等数学"},
            deadline=deadline,
            daily_minutes=120,
        )


@pytest.mark.asyncio
async def test_study_plan_service_uses_agent_plan_when_valid():
    service = StudyPlanService(db=None, llm_client=FakePlanClient())
    deadline = datetime.now(UTC) + timedelta(days=1)

    items, risk_level, risk_message = await service._generate_plan_items(
        course_ids=["course-1"],
        course_names={"course-1": "高等数学"},
        ready_material_counts={"course-1": 2},
        goal="完成期末复习",
        deadline=deadline,
        daily_minutes=90,
    )

    assert [item.title for item in items] == ["Agent 生成的计划"]
    assert risk_level == "LOW"
    assert risk_message is None


@pytest.mark.asyncio
async def test_study_plan_service_falls_back_when_agent_plan_is_invalid():
    service = StudyPlanService(db=None, llm_client=InvalidPlanClient())
    deadline = datetime.now(UTC) + timedelta(days=1)

    items, risk_level, risk_message = await service._generate_plan_items(
        course_ids=["course-1"],
        course_names={"course-1": "高等数学"},
        ready_material_counts={"course-1": 2},
        goal="完成期末复习",
        deadline=deadline,
        daily_minutes=90,
    )

    assert items
    assert items[0].title != "Agent 生成的计划"
    assert risk_level in {"LOW", "MEDIUM", "HIGH"}


class FakePlanClient:
    async def generate_study_plan(self, **kwargs):
        return {
            "risk_level": "LOW",
            "items": [
                {
                    "course_id": "course-1",
                    "title": "Agent 生成的计划",
                    "description": "按资料复习并完成练习。",
                    "scheduled_date": datetime.now(UTC).date().isoformat(),
                    "estimated_minutes": 45,
                }
            ],
        }


class InvalidPlanClient:
    async def generate_study_plan(self, **kwargs):
        return {"items": []}
