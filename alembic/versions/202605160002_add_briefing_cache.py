"""add briefing cache

Revision ID: 202605160002
Revises: 202605160001
Create Date: 2026-05-16 21:45:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605160002"
down_revision: str | None = "202605160001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "briefing_cache",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cache_key", sa.String(length=128), nullable=False),
        sa.Column("payload_json", sa.JSON(), nullable=False),
        sa.Column("source_commit", sa.String(length=64), nullable=True),
        sa.Column(
            "status",
            sa.String(length=32),
            server_default=sa.text("'ready'"),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cache_key", name="uq_briefing_cache_key"),
    )
    op.create_index("ix_briefing_cache_key_status", "briefing_cache", ["cache_key", "status"], unique=False)
    op.create_index("ix_briefing_cache_expires", "briefing_cache", ["expires_at"], unique=False)
    op.create_index(op.f("ix_briefing_cache_cache_key"), "briefing_cache", ["cache_key"], unique=False)
    op.create_index(op.f("ix_briefing_cache_expires_at"), "briefing_cache", ["expires_at"], unique=False)
    op.create_index(op.f("ix_briefing_cache_status"), "briefing_cache", ["status"], unique=False)
    op.create_index(op.f("ix_briefing_cache_updated_at"), "briefing_cache", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_briefing_cache_updated_at"), table_name="briefing_cache")
    op.drop_index(op.f("ix_briefing_cache_status"), table_name="briefing_cache")
    op.drop_index(op.f("ix_briefing_cache_expires_at"), table_name="briefing_cache")
    op.drop_index(op.f("ix_briefing_cache_cache_key"), table_name="briefing_cache")
    op.drop_index("ix_briefing_cache_expires", table_name="briefing_cache")
    op.drop_index("ix_briefing_cache_key_status", table_name="briefing_cache")
    op.drop_table("briefing_cache")
