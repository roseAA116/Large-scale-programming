import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db_session
from app.db.base import Base
from app.main import create_app
from app.models import Material, MaterialChunk, MaterialStatus
from app.services.embeddings import deterministic_embedding


@pytest.fixture
async def acceptance_app():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async def override_db_session():
        async with session_factory() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db_session] = override_db_session

    try:
        yield app, session_factory
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


@pytest.mark.asyncio
async def test_stage7_user_can_ask_and_review_answer_citations(acceptance_app):
    app, session_factory = acceptance_app
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "stage7@example.com",
                "username": "stage7_user",
                "password": "stage7-password",
                "full_name": "Stage 7 User",
            },
        )
        assert register_response.status_code == 201
        token = _api_data(register_response)["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        course_response = await client.post(
            "/api/v1/courses",
            headers=headers,
            json={
                "name": "高等数学",
                "description": "阶段七引用验收课程",
                "teacher": "Li",
                "semester": "2026 Spring",
            },
        )
        assert course_response.status_code == 201
        course = _api_data(course_response)

        async with session_factory() as session:
            material = Material(
                user_id=course["user_id"],
                course_id=course["id"],
                title="函数极限讲义",
                material_type="pdf",
                original_filename="limits.pdf",
                content_type="application/pdf",
                file_size=1024,
                object_key="stage7/limits.pdf",
                status=MaterialStatus.READY,
            )
            session.add(material)
            await session.flush()

            chunk = MaterialChunk(
                id="stage7-chunk-1",
                material_id=material.id,
                course_id=course["id"],
                user_id=course["user_id"],
                position=1,
                text="函数极限描述自变量趋近某点时函数值的变化趋势，是连续性和导数学习的基础。",
                token_count=36,
                page_no=5,
                slide_no=None,
                section_title="函数极限",
                chunk_metadata={"acceptance": "stage7"},
                embedding=deterministic_embedding("函数极限", 1536),
            )
            session.add(chunk)
            await session.commit()

        ask_response = await client.post(
            "/api/v1/chat/ask",
            headers=headers,
            json={
                "course_id": course["id"],
                "question": "函数极限",
                "search_mode": "keyword",
            },
        )
        assert ask_response.status_code == 201
        ask_payload = _api_data(ask_response)
        answer = ask_payload["answer"]
        citations = answer["citations"]
        assert citations, "Agent answer should include source citations."
        assert citations[0]["material_title"] == "函数极限讲义"
        assert citations[0]["material_id"] == material.id
        assert citations[0]["chunk_id"] == "stage7-chunk-1"
        assert citations[0]["page_no"] == 5
        assert "函数极限" in citations[0]["quote"]

        session_id = ask_payload["session"]["id"]
        history_response = await client.get(f"/api/v1/chat/sessions/{session_id}", headers=headers)
        assert history_response.status_code == 200
        messages = _api_data(history_response)["messages"]
        assistant_messages = [message for message in messages if message["role"] == "ASSISTANT"]
        assert len(assistant_messages) == 1
        history_citation = assistant_messages[0]["citations"][0]
        assert history_citation["answer_message_id"] == answer["id"]
        assert history_citation["material_title"] == "函数极限讲义"
        assert history_citation["page_no"] == 5


def _api_data(response):
    body = response.json()
    assert body["success"] is True
    return body["data"]
