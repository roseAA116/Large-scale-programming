from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MultiCoursePlanAnalyzeRequest(BaseModel):
    course_ids: list[str] = Field(min_length=1)
    deadline: datetime | None = None
    daily_minutes: int = Field(default=120, ge=15, le=720)

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


class CoursePlanningStatRead(BaseModel):
    course_id: str
    course_name: str
    task_count: int
    total_estimated_minutes: int
    earliest_due_date: str | None
    high_priority_count: int
    ready_material_count: int
    urgency_score: float
    allocation_minutes: int
    allocation_ratio: float


class MultiCoursePlanAnalysisRead(BaseModel):
    course_stats: list[CoursePlanningStatRead]
    total_task_minutes: int
    available_minutes: int
    risk_level: str
    risk_message: str | None
    suggested_goal: str
