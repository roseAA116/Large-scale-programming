from typing import Annotated

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.core.errors import AppError
from app.core.responses import ok
from app.models import AnswerCitation, ChatMessage, ChatSession
from app.schemas.chat import (
    AnswerCitationRead,
    ChatAskRequest,
    ChatMessageRead,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionRead,
    SearchMode,
)
from app.services.agent_service import AgentService, ensure_course_owner
from app.services.search_service import SearchService

router = APIRouter(tags=["chats"])


@router.get("/courses/{course_id}/search")
async def search_course_materials(
    course_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    q: Annotated[str, Query(min_length=1, max_length=2000)],
    material_type: Annotated[str | None, Query(max_length=20)] = None,
    mode: SearchMode = "hybrid",
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
):
    await ensure_course_owner(db, course_id=course_id, user_id=current_user.id)
    service = SearchService(db)
    results = await service.search_course_materials(
        user_id=current_user.id,
        course_id=course_id,
        query=q,
        material_type=material_type,
        mode=mode,
        limit=limit,
    )
    return ok(request, [result.model_dump(mode="json") for result in results])


@router.post("/chat/sessions")
async def create_chat_session(
    payload: ChatSessionCreate,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    await ensure_course_owner(db, course_id=payload.course_id, user_id=current_user.id)
    session = ChatSession(
        user_id=current_user.id,
        course_id=payload.course_id,
        title=payload.title or "新的课程问答",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return ok(
        request,
        ChatSessionRead.model_validate(session).model_dump(mode="json"),
        status_code=201,
    )


@router.get("/chat/sessions")
async def list_chat_sessions(
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
    course_id: Annotated[str | None, Query()] = None,
):
    statement = (
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id, ChatSession.deleted_at.is_(None))
        .order_by(ChatSession.updated_at.desc())
    )
    if course_id:
        await ensure_course_owner(db, course_id=course_id, user_id=current_user.id)
        statement = statement.where(ChatSession.course_id == course_id)

    sessions = (await db.scalars(statement)).all()
    return ok(
        request,
        [ChatSessionRead.model_validate(session).model_dump(mode="json") for session in sessions],
    )


@router.get("/chat/sessions/{session_id}")
async def read_chat_session(
    session_id: str,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    session = await db.scalar(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
            ChatSession.deleted_at.is_(None),
        )
    )
    if session is None:
        raise AppError("CHAT_SESSION_NOT_FOUND", "Chat session not found.", status_code=404)

    messages = (
        await db.scalars(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id, ChatMessage.user_id == current_user.id)
            .order_by(ChatMessage.created_at.asc())
        )
    ).all()
    citations = (
        await db.scalars(
            select(AnswerCitation)
            .where(
                AnswerCitation.session_id == session.id,
                AnswerCitation.user_id == current_user.id,
            )
            .order_by(AnswerCitation.sort_order.asc())
        )
    ).all()
    citations_by_message: dict[str, list[AnswerCitation]] = {}
    for citation in citations:
        citations_by_message.setdefault(citation.answer_message_id, []).append(citation)

    detail = ChatSessionDetail(
        session=ChatSessionRead.model_validate(session),
        messages=[
            _message_read(message, citations_by_message.get(message.id, [])) for message in messages
        ],
    )
    return ok(request, detail.model_dump(mode="json"))


@router.post("/chat/ask")
async def ask_agent(
    payload: ChatAskRequest,
    current_user: CurrentUser,
    db: DbSession,
    request: Request,
):
    service = AgentService(db)
    result = await service.ask(user_id=current_user.id, payload=payload)
    return ok(request, result.model_dump(mode="json"), status_code=201)


def _message_read(message: ChatMessage, citations: list[AnswerCitation]) -> ChatMessageRead:
    data = ChatMessageRead.model_validate(message)
    data.citations = [AnswerCitationRead.model_validate(citation) for citation in citations]
    return data
