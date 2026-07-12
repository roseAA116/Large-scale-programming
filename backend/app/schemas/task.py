from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import TaskPriority, TaskStatus


class PlanTaskSelection(BaseModel):
    plan_item_ids: list[str] | None = None

    @field_validator("plan_item_ids")
    @classmethod
    def deduplicate_plan_item_ids(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        for item_id in value:
            stripped = item_id.strip()
            if stripped and stripped not in cleaned:
                cleaned.append(stripped)
        return cleaned or None


class TaskPreviewItemRead(BaseModel):
    source_id: str
    plan_id: str
    course_id: str
    title: str
    description: str | None
    due_date: date
    estimated_minutes: int
    priority: TaskPriority
    risk_message: str | None = None
    already_added: bool = False


class TaskPreviewRead(BaseModel):
    items: list[TaskPreviewItemRead]
    risk_level: str
    risk_message: str | None
    total_estimated_minutes: int
    already_added_count: int = 0


class TaskRead(BaseModel):
    id: str
    user_id: str
    course_id: str
    plan_id: str | None
    source_id: str | None
    title: str
    description: str | None
    due_date: date
    estimated_minutes: int
    priority: TaskPriority
    status: TaskStatus
    completed_at: datetime | None
    canceled_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskCreate(BaseModel):
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    due_date: date
    estimated_minutes: int = Field(ge=5, le=720)
    priority: TaskPriority = TaskPriority.MEDIUM

    @field_validator("course_id", "title")
    @classmethod
    def trim_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value is required")
        return stripped

    @field_validator("description")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TaskUpdate(BaseModel):
    course_id: str | None = Field(default=None, min_length=1)
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=1200)
    due_date: date | None = None
    estimated_minutes: int | None = Field(default=None, ge=5, le=720)
    priority: TaskPriority | None = None
    status: TaskStatus | None = None

    @field_validator("course_id", "title")
    @classmethod
    def trim_required(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value is required")
        return stripped

    @field_validator("description")
    @classmethod
    def trim_optional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class TaskPostpone(BaseModel):
    due_date: date


class TaskPage(BaseModel):
    items: list[TaskRead]
    total: int
    page: int
    page_size: int
