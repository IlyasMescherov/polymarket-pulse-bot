"""add intelligence alerts topics and watchlist metadata

Revision ID: 202605140002
Revises: 202605140001
Create Date: 2026-05-14 10:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605140002"
down_revision = "202605140001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "min_volume_for_alerts",
            sa.Float(),
            server_default=sa.text("0"),
            nullable=False,
        ),
    )

    op.add_column(
        "user_watchlist",
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=True),
    )
    op.add_column(
        "user_watchlist",
        sa.Column("initial_probability", sa.Float(), nullable=True),
    )
    op.add_column(
        "user_watchlist",
        sa.Column("last_probability", sa.Float(), nullable=True),
    )
    op.add_column(
        "user_watchlist",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.execute(
        """
        UPDATE user_watchlist AS watchlist
        SET telegram_user_id = users.telegram_id
        FROM users
        WHERE watchlist.user_id = users.id
        """
    )
    op.alter_column("user_watchlist", "telegram_user_id", nullable=False)
    op.create_index(
        "ix_user_watchlist_telegram_user_id",
        "user_watchlist",
        ["telegram_user_id"],
        unique=False,
    )

    op.create_table(
        "user_topics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("topic", sa.String(length=80), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_user_id",
            "topic",
            name="uq_user_topics_user_topic",
        ),
    )
    op.create_index(
        "ix_user_topics_telegram_user_id",
        "user_topics",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_topics_user_created",
        "user_topics",
        ["telegram_user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "user_alerts_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("alert_type", sa.String(length=64), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_user_alerts_log_market_id",
        "user_alerts_log",
        ["market_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_alerts_log_sent_at",
        "user_alerts_log",
        ["sent_at"],
        unique=False,
    )
    op.create_index(
        "ix_user_alerts_log_telegram_user_id",
        "user_alerts_log",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_alerts_user_market_type_sent",
        "user_alerts_log",
        ["telegram_user_id", "market_id", "alert_type", "sent_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_alerts_user_market_type_sent", table_name="user_alerts_log")
    op.drop_index("ix_user_alerts_log_telegram_user_id", table_name="user_alerts_log")
    op.drop_index("ix_user_alerts_log_sent_at", table_name="user_alerts_log")
    op.drop_index("ix_user_alerts_log_market_id", table_name="user_alerts_log")
    op.drop_table("user_alerts_log")
    op.drop_index("ix_user_topics_user_created", table_name="user_topics")
    op.drop_index("ix_user_topics_telegram_user_id", table_name="user_topics")
    op.drop_table("user_topics")
    op.drop_index("ix_user_watchlist_telegram_user_id", table_name="user_watchlist")
    op.drop_column("user_watchlist", "updated_at")
    op.drop_column("user_watchlist", "last_probability")
    op.drop_column("user_watchlist", "initial_probability")
    op.drop_column("user_watchlist", "telegram_user_id")
    op.drop_column("users", "min_volume_for_alerts")
