from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import StudyPlanItemStatus, StudyPlanStatus


class StudyPlanCreate(BaseModel):
    course_ids: list[str] = Field(min_length=1)
    goal: str = Field(min_length=1, max_length=2000)
    deadline: datetime
    daily_minutes: int = Field(ge=15, le=720)

    @field_validator("course_ids")
    @classmethod
    def deduplicate_course_ids(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for course_id in value:
            stripped = course_id.strip()
            if stripped and stripped not in cleaned:
                cleaned.append(stripped)
        if not cleaned:
            raise ValueError("At least one course is required")
        return cleaned

    @field_validator("goal")
    @classmethod
    def trim_goal(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Study goal is required")
        return stripped


class StudyPlanUpdate(BaseModel):
    goal: str | None = Field(default=None, min_length=1, max_length=2000)
    deadline: datetime | None = None
    daily_minutes: int | None = Field(default=None, ge=15, le=720)
    status: StudyPlanStatus | None = None

    @field_validator("goal")
    @classmethod
    def trim_goal(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Study goal is required")
        return stripped


class StudyPlanItemUpdate(BaseModel):
    status: StudyPlanItemStatus


class StudyPlanItemRead(BaseModel):
    id: str
    plan_id: str
    user_id: str
    course_id: str
    title: str
    description: str | None
    scheduled_date: date
    estimated_minutes: int
    status: StudyPlanItemStatus
    sort_order: int
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StudyPlanRead(BaseModel):
    id: str
    user_id: str
    goal: str
    course_ids: list[str]
    deadline: datetime
    daily_minutes: int
    status: StudyPlanStatus
    risk_level: str
    risk_message: str | None
    created_at: datetime
    updated_at: datetime
    items: list[StudyPlanItemRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class StudyPlanPage(BaseModel):
    items: list[StudyPlanRead]
    total: int
    page: int
    page_size: int
