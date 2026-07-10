from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.material import MaterialStatus


class MaterialRead(BaseModel):
    id: str
    user_id: str
    course_id: str
    title: str
    material_type: str
    original_filename: str
    content_type: str | None
    file_size: int
    status: MaterialStatus
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MaterialUploadMeta(BaseModel):
    title: str | None = Field(default=None, max_length=255)
    material_type: str | None = Field(default=None, max_length=20)

    @field_validator("title", "material_type")
    @classmethod
    def trim_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None
