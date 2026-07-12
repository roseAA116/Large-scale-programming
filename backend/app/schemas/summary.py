from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseSummaryCreate(BaseModel):
    material_id: str | None = Field(default=None, max_length=36)
    regenerate: bool = False

    @field_validator("material_id")
    @classmethod
    def trim_material_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class KnowledgePointRead(BaseModel):
    title: str
    detail: str
    source_count: int = 1


class CourseSummaryRead(BaseModel):
    id: str
    user_id: str
    course_id: str
    material_id: str | None
    scope: str
    version: int
    title: str
    outline_md: str
    knowledge_points: list[KnowledgePointRead]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CourseSummaryPage(BaseModel):
    items: list[CourseSummaryRead]
    total: int
