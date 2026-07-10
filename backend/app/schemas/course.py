from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    teacher: str | None = Field(default=None, max_length=120)
    semester: str | None = Field(default=None, max_length=60)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Course name is required")
        return stripped

    @field_validator("description", "teacher", "semester")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class CourseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=2000)
    teacher: str | None = Field(default=None, max_length=120)
    semester: str | None = Field(default=None, max_length=60)

    @field_validator("name")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Course name is required")
        return stripped

    @field_validator("description", "teacher", "semester")
    @classmethod
    def trim_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class CourseRead(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    teacher: str | None
    semester: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
