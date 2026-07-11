from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.models import AnswerCitation, ChatMessage, ChatMessageRole, ChatSession, Course
from app.schemas.chat import (
    AnswerCitationRead,
    ChatAskRequest,
    ChatAskResponse,
    ChatMessageRead,
    ChatSessionRead,
    SearchResultRead,
)
from app.services.llm_client import LLMClient
from app.services.search_service import SearchService


class AgentService:
    def __init__(
        self,
        db: AsyncSession,
        search_service: SearchService | None = None,
        llm_client: LLMClient | None = None,
    ) -> None:
        self.db = db
        self.search_service = search_service or SearchService(db)
        self.llm_client = llm_client or LLMClient()

    async def ask(self, *, user_id: str, payload: ChatAskRequest) -> ChatAskResponse:
        await ensure_course_owner(self.db, course_id=payload.course_id, user_id=user_id)

        ready_count = await self.search_service.ready_material_count(
            user_id=user_id,
            course_id=payload.course_id,
        )
        if ready_count == 0:
            raise AppError(
                "SEARCH_INDEX_NOT_READY",
                "当前课程还没有 READY 状态的资料，请等待资料解析和索引完成后再提问。",
                status_code=409,
            )

        session = await self._get_or_create_session(
            user_id=user_id,
            course_id=payload.course_id,
            session_id=payload.session_id,
            title=_title_from_question(payload.question),
        )
        question_message = ChatMessage(
            session_id=session.id,
            user_id=user_id,
            course_id=payload.course_id,
            role=ChatMessageRole.USER,
            content=payload.question,
            token_count=_estimate_tokens(payload.question),
        )
        self.db.add(question_message)
        await self.db.flush()

        contexts = await self.search_service.search_course_materials(
            user_id=user_id,
            course_id=payload.course_id,
            query=payload.question,
            material_type=payload.material_type,
            mode=payload.search_mode,
            limit=8,
        )
        answer_text = await self.llm_client.answer_question(
            question=payload.question,
            contexts=contexts,
        )
        answer_message = ChatMessage(
            session_id=session.id,
            user_id=user_id,
            course_id=payload.course_id,
            role=ChatMessageRole.ASSISTANT,
            content=answer_text,
            token_count=_estimate_tokens(answer_text),
        )
        session.updated_at = datetime.now(UTC)
        self.db.add(answer_message)
        await self.db.flush()
        citations = _build_citations(
            answer_message=answer_message,
            contexts=contexts,
            user_id=user_id,
        )
        self.db.add_all(citations)
        await self.db.commit()
        await self.db.refresh(session)
        await self.db.refresh(question_message)
        await self.db.refresh(answer_message)
        for citation in citations:
            await self.db.refresh(citation)

        return ChatAskResponse(
            session=ChatSessionRead.model_validate(session),
            question=ChatMessageRead.model_validate(question_message),
            answer=_message_read(answer_message, citations),
            contexts=contexts,
        )

    async def _get_or_create_session(
        self,
        *,
        user_id: str,
        course_id: str,
        session_id: str | None,
        title: str,
    ) -> ChatSession:
        if session_id:
            session = await self.db.scalar(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id,
                    ChatSession.course_id == course_id,
                    ChatSession.deleted_at.is_(None),
                )
            )
            if session is None:
                raise AppError("CHAT_SESSION_NOT_FOUND", "Chat session not found.", status_code=404)
            return session

        session = ChatSession(user_id=user_id, course_id=course_id, title=title)
        self.db.add(session)
        await self.db.flush()
        return session


async def ensure_course_owner(db: AsyncSession, *, course_id: str, user_id: str) -> Course:
    course = await db.scalar(
        select(Course).where(
            Course.id == course_id,
            Course.user_id == user_id,
            Course.deleted_at.is_(None),
        )
    )
    if course is None:
        raise AppError("COURSE_NOT_FOUND", "Course not found.", status_code=404)
    return course


def _title_from_question(question: str) -> str:
    compacted = " ".join(question.split())
    if len(compacted) <= 36:
        return compacted
    return f"{compacted[:35]}…"


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 3)


def _build_citations(
    *,
    answer_message: ChatMessage,
    contexts: list[SearchResultRead],
    user_id: str,
) -> list[AnswerCitation]:
    citations: list[AnswerCitation] = []
    for index, context in enumerate(contexts, start=1):
        citations.append(
            AnswerCitation(
                answer_message_id=answer_message.id,
                session_id=answer_message.session_id,
                user_id=user_id,
                course_id=answer_message.course_id,
                material_id=context.material_id,
                chunk_id=context.chunk_id,
                material_title=context.material_title,
                material_type=context.material_type,
                section_title=context.section_title,
                page_no=context.page_no,
                slide_no=context.slide_no,
                quote=_compact_quote(context.text),
                score=context.score,
                sort_order=index,
            )
        )
    return citations


def _message_read(
    message: ChatMessage,
    citations: list[AnswerCitation] | None = None,
) -> ChatMessageRead:
    data = ChatMessageRead.model_validate(message)
    data.citations = [
        AnswerCitationRead.model_validate(citation)
        for citation in sorted(citations or [], key=lambda item: item.sort_order)
    ]
    return data


def _compact_quote(text: str, max_length: int = 360) -> str:
    compacted = " ".join(text.split())
    if len(compacted) <= max_length:
        return compacted
    return f"{compacted[: max_length - 1]}…"
