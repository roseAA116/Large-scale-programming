"""create answer citations

Revision ID: 202607110006
Revises: 202607100005
Create Date: 2026-07-11 00:00:06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202607110006"
down_revision: str | None = "202607100005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "answer_citations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("answer_message_id", sa.String(length=36), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("material_id", sa.String(length=36), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("material_title", sa.String(length=255), nullable=False),
        sa.Column("material_type", sa.String(length=20), nullable=False),
        sa.Column("section_title", sa.String(length=255), nullable=True),
        sa.Column("page_no", sa.Integer(), nullable=True),
        sa.Column("slide_no", sa.Integer(), nullable=True),
        sa.Column("quote", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["answer_message_id"], ["chat_messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["chunk_id"], ["material_chunks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["material_id"], ["materials.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["session_id"], ["chat_sessions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_answer_citations_answer_message_id"),
        "answer_citations",
        ["answer_message_id"],
    )
    op.create_index(op.f("ix_answer_citations_chunk_id"), "answer_citations", ["chunk_id"])
    op.create_index(op.f("ix_answer_citations_course_id"), "answer_citations", ["course_id"])
    op.create_index(op.f("ix_answer_citations_material_id"), "answer_citations", ["material_id"])
    op.create_index(op.f("ix_answer_citations_session_id"), "answer_citations", ["session_id"])
    op.create_index(op.f("ix_answer_citations_user_id"), "answer_citations", ["user_id"])
    op.create_index(
        "ix_answer_citations_message_order",
        "answer_citations",
        ["answer_message_id", "sort_order"],
    )


def downgrade() -> None:
    op.drop_index("ix_answer_citations_message_order", table_name="answer_citations")
    op.drop_index(op.f("ix_answer_citations_user_id"), table_name="answer_citations")
    op.drop_index(op.f("ix_answer_citations_session_id"), table_name="answer_citations")
    op.drop_index(op.f("ix_answer_citations_material_id"), table_name="answer_citations")
    op.drop_index(op.f("ix_answer_citations_course_id"), table_name="answer_citations")
    op.drop_index(op.f("ix_answer_citations_chunk_id"), table_name="answer_citations")
    op.drop_index(
        op.f("ix_answer_citations_answer_message_id"),
        table_name="answer_citations",
    )
    op.drop_table("answer_citations")
