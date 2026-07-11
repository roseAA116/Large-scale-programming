from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.chat import ChatMessageRole

SearchMode = Literal["keyword", "vector", "hybrid"]


class SearchResultRead(BaseModel):
    chunk_id: str
    material_id: str
    material_title: str
    material_type: str
    text: str
    score: float
    keyword_score: float
    vector_score: float
    page_no: int | None
    slide_no: int | None
    section_title: str | None


class AnswerCitationRead(BaseModel):
    id: str
    answer_message_id: str
    material_id: str
    chunk_id: str
    material_title: str
    material_type: str
    section_title: str | None
    page_no: int | None
    slide_no: int | None
    quote: str
    score: float
    sort_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatAskRequest(BaseModel):
    course_id: str
    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    material_type: str | None = Field(default=None, max_length=20)
    search_mode: SearchMode = "hybrid"

    @field_validator("question", "session_id", "material_type")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ChatSessionCreate(BaseModel):
    course_id: str
    title: str | None = Field(default=None, max_length=120)

    @field_validator("title")
    @classmethod
    def trim_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ChatSessionRead(BaseModel):
    id: str
    user_id: str
    course_id: str
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(BaseModel):
    id: str
    session_id: str
    user_id: str
    course_id: str
    role: ChatMessageRole
    content: str
    token_count: int
    created_at: datetime
    citations: list[AnswerCitationRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetail(BaseModel):
    session: ChatSessionRead
    messages: list[ChatMessageRead]


class ChatAskResponse(BaseModel):
    session: ChatSessionRead
    answer: ChatMessageRead
    question: ChatMessageRead
    contexts: list[SearchResultRead]
