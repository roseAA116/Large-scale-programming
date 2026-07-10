"""create materials table

Revision ID: 202607100003
Revises: 202607100002
Create Date: 2026-07-10 00:00:03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "202607100003"
down_revision: str | None = "202607100002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

material_status = postgresql.ENUM(
    "UPLOADED",
    "PARSING",
    "PARSED",
    "INDEXING",
    "READY",
    "FAILED",
    name="material_status",
    create_type=False,
)


def upgrade() -> None:
    material_status.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "materials",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("material_type", sa.String(length=20), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=120), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("object_key", sa.String(length=1024), nullable=False),
        sa.Column("status", material_status, nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(op.f("ix_materials_course_id"), "materials", ["course_id"], unique=False)
    op.create_index(op.f("ix_materials_user_id"), "materials", ["user_id"], unique=False)
    op.create_index(
        "ix_materials_course_id_deleted_at",
        "materials",
        ["course_id", "deleted_at"],
        unique=False,
    )
    op.create_index(
        "ix_materials_user_id_deleted_at",
        "materials",
        ["user_id", "deleted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_materials_user_id_deleted_at", table_name="materials")
    op.drop_index("ix_materials_course_id_deleted_at", table_name="materials")
    op.drop_index(op.f("ix_materials_user_id"), table_name="materials")
    op.drop_index(op.f("ix_materials_course_id"), table_name="materials")
    op.drop_table("materials")
    material_status.drop(op.get_bind(), checkfirst=True)
