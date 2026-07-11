"""create study plans

Revision ID: 202607110007
Revises: 202607110006
Create Date: 2026-07-11 00:00:07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607110007"
down_revision: str | None = "202607110006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    study_plan_status = sa.Enum("ACTIVE", "COMPLETED", "ARCHIVED", name="study_plan_status")
    study_plan_item_status = sa.Enum("TODO", "DONE", "SKIPPED", name="study_plan_item_status")
    study_plan_status.create(op.get_bind(), checkfirst=True)
    study_plan_item_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "study_plans",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("course_ids", sa.JSON(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("daily_minutes", sa.Integer(), nullable=False),
        sa.Column("status", study_plan_status, nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("risk_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_plans_user_id"), "study_plans", ["user_id"])
    op.create_index(
        "ix_study_plans_user_status_updated",
        "study_plans",
        ["user_id", "status", "updated_at"],
    )

    op.create_table(
        "study_plan_items",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("plan_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("scheduled_date", sa.Date(), nullable=False),
        sa.Column("estimated_minutes", sa.Integer(), nullable=False),
        sa.Column("status", study_plan_item_status, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["plan_id"], ["study_plans.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_study_plan_items_course_id"), "study_plan_items", ["course_id"])
    op.create_index(op.f("ix_study_plan_items_plan_id"), "study_plan_items", ["plan_id"])
    op.create_index(op.f("ix_study_plan_items_user_id"), "study_plan_items", ["user_id"])
    op.create_index(
        "ix_study_plan_items_plan_date_order",
        "study_plan_items",
        ["plan_id", "scheduled_date", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_study_plan_items_plan_date_order", table_name="study_plan_items")
    op.drop_index(op.f("ix_study_plan_items_user_id"), table_name="study_plan_items")
    op.drop_index(op.f("ix_study_plan_items_plan_id"), table_name="study_plan_items")
    op.drop_index(op.f("ix_study_plan_items_course_id"), table_name="study_plan_items")
    op.drop_table("study_plan_items")
    op.drop_index("ix_study_plans_user_status_updated", table_name="study_plans")
    op.drop_index(op.f("ix_study_plans_user_id"), table_name="study_plans")
    op.drop_table("study_plans")
    sa.Enum(name="study_plan_item_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="study_plan_status").drop(op.get_bind(), checkfirst=True)
