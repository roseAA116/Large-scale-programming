from datetime import date, datetime

from pydantic import BaseModel


class DashboardTaskRead(BaseModel):
    id: str
    course_id: str
    title: str
    due_date: date
    priority: str
    status: str


class DashboardChatRead(BaseModel):
    id: str
    course_id: str
    title: str
    updated_at: datetime


class DashboardPlanRead(BaseModel):
    id: str
    goal: str
    deadline: datetime
    risk_level: str
    status: str


class DashboardSummaryRead(BaseModel):
    course_count: int
    material_count: int
    ready_material_count: int
    ready_material_ratio: float
    today_tasks: list[DashboardTaskRead]
    recent_chats: list[DashboardChatRead]
    recent_plans: list[DashboardPlanRead]
