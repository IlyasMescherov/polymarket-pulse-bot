"""create initial tables

Revision ID: 202605130001
Revises:
Create Date: 2026-05-13 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605130001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column(
            "notifications_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_users_telegram_id", "users", ["telegram_id"], unique=False)

    op.create_table(
        "market_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("slug", sa.String(length=512), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("yes_probability", sa.Float(), nullable=True),
        sa.Column("volume", sa.Float(), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("market_url", sa.Text(), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_market_snapshots_created_at", "market_snapshots", ["created_at"], unique=False)
    op.create_index("ix_market_snapshots_market_id", "market_snapshots", ["market_id"], unique=False)
    op.create_index(
        "ix_market_snapshots_market_created",
        "market_snapshots",
        ["market_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_market_snapshots_market_created", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_market_id", table_name="market_snapshots")
    op.drop_index("ix_market_snapshots_created_at", table_name="market_snapshots")
    op.drop_table("market_snapshots")
    op.drop_index("ix_users_telegram_id", table_name="users")
    op.drop_table("users")

