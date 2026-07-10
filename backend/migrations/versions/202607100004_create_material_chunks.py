"""create material chunks table

Revision ID: 202607100004
Revises: 202607100003
Create Date: 2026-07-10 00:00:04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.core.config import settings
from app.db.types import Vector

revision: str = "202607100004"
down_revision: str | None = "202607100003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "material_chunks",
        sa.Column("id", sa.String(length=64), nullable=False),
        sa.Column("material_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("page_no", sa.Integer(), nullable=True),
        sa.Column("slide_no", sa.Integer(), nullable=True),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("embedding", Vector(settings.embedding_dimension), nullable=True),
        sa.Column("indexing_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("material_id", "position", name="uq_material_chunks_material_position"),
    )
    op.create_index(op.f("ix_material_chunks_course_id"), "material_chunks", ["course_id"])
    op.create_index(op.f("ix_material_chunks_material_id"), "material_chunks", ["material_id"])
    op.create_index(op.f("ix_material_chunks_user_id"), "material_chunks", ["user_id"])
    op.create_index(
        "ix_material_chunks_material_position",
        "material_chunks",
        ["material_id", "position"],
    )
    op.execute(
        "CREATE INDEX ix_material_chunks_embedding "
        "ON material_chunks USING hnsw (embedding vector_cosine_ops) "
        "WHERE embedding IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_material_chunks_embedding")
    op.drop_index("ix_material_chunks_material_position", table_name="material_chunks")
    op.drop_index(op.f("ix_material_chunks_user_id"), table_name="material_chunks")
    op.drop_index(op.f("ix_material_chunks_material_id"), table_name="material_chunks")
    op.drop_index(op.f("ix_material_chunks_course_id"), table_name="material_chunks")
    op.drop_table("material_chunks")
