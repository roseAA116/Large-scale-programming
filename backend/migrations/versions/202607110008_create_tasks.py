"""create tasks

Revision ID: 202607110008
Revises: 202607110007
Create Date: 2026-07-11 00:00:08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607110008"
down_revision: str | None = "202607110007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    task_status = sa.Enum("TODO", "IN_PROGRESS", "DONE", "CANCELED", name="task_status")
    task_priority = sa.Enum("LOW", "MEDIUM", "HIGH", name="task_priority")
    task_status.create(op.get_bind(), checkfirst=True)
    task_priority.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=True),
        sa.Column("source_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("priority", task_priority, nullable=False),
        sa.Column("status", task_status, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("canceled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["study_plans.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "source_id", name="uq_tasks_user_source"),
    )
    op.create_index(op.f("ix_tasks_course_id"), "tasks", ["course_id"])
    op.create_index(op.f("ix_tasks_plan_id"), "tasks", ["plan_id"])
    op.create_index(op.f("ix_tasks_source_id"), "tasks", ["source_id"])
    op.create_index(op.f("ix_tasks_user_id"), "tasks", ["user_id"])
    op.create_index("ix_tasks_user_status_due", "tasks", ["user_id", "status", "due_date"])


def downgrade() -> None:
    op.drop_index("ix_tasks_user_status_due", table_name="tasks")
    op.drop_index(op.f("ix_tasks_user_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_source_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_plan_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_course_id"), table_name="tasks")
    op.drop_table("tasks")
    sa.Enum(name="task_priority").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="task_status").drop(op.get_bind(), checkfirst=True)
