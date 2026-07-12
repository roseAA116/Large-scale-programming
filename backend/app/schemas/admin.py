from datetime import datetime

from pydantic import BaseModel


class AdminSystemStatusRead(BaseModel):
    users: int
    courses: int
    materials: int
    failed_materials: int
    tasks: int
    plans: int
    generated_at: datetime


class AdminUserRead(BaseModel):
    id: str
    email: str
    username: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime


class AdminMaterialRead(BaseModel):
    id: str
    user_id: str
    course_id: str
    title: str
    status: str
    error_message: str | None
    updated_at: datetime


class AdminQueueStatusRead(BaseModel):
    queue_name: str
    retry_queue_name: str
    pending_count: int | None
    retry_count: int | None
    available: bool
    error: str | None = None
