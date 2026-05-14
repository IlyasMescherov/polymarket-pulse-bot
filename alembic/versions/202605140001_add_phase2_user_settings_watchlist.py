"""add phase 2 user settings and watchlist

Revision ID: 202605140001
Revises: 202605130001
Create Date: 2026-05-14 09:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605140001"
down_revision = "202605130001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "daily_digest_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "language",
            sa.String(length=8),
            server_default=sa.text("'ru'"),
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column(
            "movement_threshold",
            sa.Float(),
            server_default=sa.text("0.10"),
            nullable=False,
        ),
    )

    op.create_table(
        "user_watchlist",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("market_title", sa.Text(), nullable=False),
        sa.Column("market_url", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "market_id",
            name="uq_user_watchlist_user_market",
        ),
    )
    op.create_index(
        "ix_user_watchlist_market_id",
        "user_watchlist",
        ["market_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_watchlist_user_created",
        "user_watchlist",
        ["user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_watchlist_user_id",
        "user_watchlist",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_watchlist_user_id", table_name="user_watchlist")
    op.drop_index("ix_user_watchlist_user_created", table_name="user_watchlist")
    op.drop_index("ix_user_watchlist_market_id", table_name="user_watchlist")
    op.drop_table("user_watchlist")
    op.drop_column("users", "movement_threshold")
    op.drop_column("users", "language")
    op.drop_column("users", "daily_digest_enabled")
