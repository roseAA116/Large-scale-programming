from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import (
    Course,
    Material,
    MaterialChunk,
    MaterialStatus,
    Task,
    TaskPriority,
    TaskStatus,
    User,
)
from app.services.planning_service import PlanningService
from app.services.summary_service import SummaryService


@pytest.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_summary_service_generates_versioned_course_outline(session_factory):
    async with session_factory() as session:
        user = User(email="summary@example.com", username="summary", hashed_password="x")
        session.add(user)
        await session.flush()
        course = Course(user_id=user.id, name="数据结构")
        session.add(course)
        await session.flush()
        material = Material(
            user_id=user.id,
            course_id=course.id,
            title="树与图讲义",
            material_type="pdf",
            original_filename="graph.pdf",
            file_size=100,
            object_key="summary/graph.pdf",
            status=MaterialStatus.READY,
        )
        session.add(material)
        await session.flush()
        session.add_all(
            [
                MaterialChunk(
                    material_id=material.id,
                    course_id=course.id,
                    user_id=user.id,
                    position=1,
                    text="二叉树是一种每个节点最多有两个子节点的数据结构。",
                    token_count=24,
                    section_title="二叉树",
                    chunk_metadata={},
                ),
                MaterialChunk(
                    material_id=material.id,
                    course_id=course.id,
                    user_id=user.id,
                    position=2,
                    text="图遍历包括深度优先搜索和广度优先搜索。",
                    token_count=22,
                    section_title="图遍历",
                    chunk_metadata={},
                ),
            ]
        )
        await session.commit()

        summary = await SummaryService(session).generate_summary(
            user_id=user.id,
            course_id=course.id,
        )

        assert summary.version == 1
        assert summary.scope == "COURSE"
        assert "复习提纲" in summary.outline_md
        assert [point.title for point in summary.knowledge_points] == ["二叉树", "图遍历"]


@pytest.mark.asyncio
async def test_planning_service_allocates_time_by_course_urgency(session_factory):
    async with session_factory() as session:
        user = User(email="planning@example.com", username="planning", hashed_password="x")
        session.add(user)
        await session.flush()
        math = Course(user_id=user.id, name="高等数学")
        english = Course(user_id=user.id, name="大学英语")
        session.add_all([math, english])
        await session.flush()
        session.add_all(
            [
                Task(
                    user_id=user.id,
                    course_id=math.id,
                    title="完成高数作业",
                    due_date=date.today(),
                    estimated_minutes=180,
                    priority=TaskPriority.HIGH,
                    status=TaskStatus.TODO,
                ),
                Task(
                    user_id=user.id,
                    course_id=english.id,
                    title="背单词",
                    due_date=date.today() + timedelta(days=7),
                    estimated_minutes=30,
                    priority=TaskPriority.LOW,
                    status=TaskStatus.TODO,
                ),
            ]
        )
        await session.commit()

        analysis = await PlanningService(session).analyze_multi_course_plan(
            user_id=user.id,
            course_ids=[math.id, english.id],
            deadline=datetime.now(UTC) + timedelta(days=1),
            daily_minutes=60,
        )

        stats = {item.course_name: item for item in analysis.course_stats}
        assert stats["高等数学"].allocation_ratio > stats["大学英语"].allocation_ratio
        assert analysis.total_task_minutes == 210
        assert analysis.risk_level == "HIGH"
