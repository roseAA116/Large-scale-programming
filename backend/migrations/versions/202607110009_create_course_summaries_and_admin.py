"""create course summaries and admin flag

Revision ID: 202607110009
Revises: 202607110008
Create Date: 2026-07-11 00:00:09
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607110009"
down_revision: str | None = "202607110008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_table(
        "course_summaries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("material_id", sa.String(length=36), nullable=True),
        sa.Column("scope", sa.String(length=20), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("outline_md", sa.Text(), nullable=False),
        sa.Column("knowledge_points", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_course_summaries_course_id"), "course_summaries", ["course_id"])
    op.create_index(op.f("ix_course_summaries_material_id"), "course_summaries", ["material_id"])
    op.create_index(op.f("ix_course_summaries_user_id"), "course_summaries", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_course_summaries_user_id"), table_name="course_summaries")
    op.drop_index(op.f("ix_course_summaries_material_id"), table_name="course_summaries")
    op.drop_index(op.f("ix_course_summaries_course_id"), table_name="course_summaries")
    op.drop_table("course_summaries")
    op.drop_column("users", "is_admin")
