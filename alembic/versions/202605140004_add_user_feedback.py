"""add user feedback

Revision ID: 202605140004
Revises: 202605140003
Create Date: 2026-05-14 16:45:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605140004"
down_revision = "202605140003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_feedback_created_at",
        "user_feedback",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_feedback_telegram_user_id",
        "user_feedback",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_feedback_user_created",
        "user_feedback",
        ["telegram_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_feedback_user_created", table_name="user_feedback")
    op.drop_index("ix_user_feedback_telegram_user_id", table_name="user_feedback")
    op.drop_index("ix_user_feedback_created_at", table_name="user_feedback")
    op.drop_table("user_feedback")
