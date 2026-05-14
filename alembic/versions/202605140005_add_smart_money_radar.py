"""add smart money radar

Revision ID: 202605140005
Revises: 202605140004
Create Date: 2026-05-14 18:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605140005"
down_revision = "202605140004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "smart_money_alerts_enabled",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )

    op.create_table(
        "smart_money_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("market_id", sa.String(length=128), nullable=True),
        sa.Column("market_title", sa.Text(), nullable=True),
        sa.Column("wallet_address", sa.String(length=64), nullable=True),
        sa.Column("amount_usd", sa.Float(), nullable=True),
        sa.Column("raw_data", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_smart_money_snapshots_created",
        "smart_money_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_snapshots_created_at",
        "smart_money_snapshots",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_snapshots_market_created",
        "smart_money_snapshots",
        ["market_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_snapshots_market_id",
        "smart_money_snapshots",
        ["market_id"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_snapshots_signal_type",
        "smart_money_snapshots",
        ["signal_type"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_snapshots_type_created",
        "smart_money_snapshots",
        ["signal_type", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_snapshots_wallet_address",
        "smart_money_snapshots",
        ["wallet_address"],
        unique=False,
    )

    op.create_table(
        "tracked_traders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("wallet_address", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "telegram_user_id",
            "wallet_address",
            name="uq_tracked_traders_user_wallet",
        ),
    )
    op.create_index(
        "ix_tracked_traders_created_at",
        "tracked_traders",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tracked_traders_telegram_user_id",
        "tracked_traders",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_tracked_traders_user_created",
        "tracked_traders",
        ["telegram_user_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_tracked_traders_user_id",
        "tracked_traders",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_tracked_traders_wallet_address",
        "tracked_traders",
        ["wallet_address"],
        unique=False,
    )

    op.create_table(
        "smart_money_alerts_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("signal_type", sa.String(length=64), nullable=False),
        sa.Column("market_id", sa.String(length=128), nullable=True),
        sa.Column("wallet_address", sa.String(length=64), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_smart_money_alerts_log_market_id",
        "smart_money_alerts_log",
        ["market_id"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_alerts_log_sent_at",
        "smart_money_alerts_log",
        ["sent_at"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_alerts_log_telegram_user_id",
        "smart_money_alerts_log",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_alerts_log_wallet_address",
        "smart_money_alerts_log",
        ["wallet_address"],
        unique=False,
    )
    op.create_index(
        "ix_smart_money_alerts_user_signal_sent",
        "smart_money_alerts_log",
        ["telegram_user_id", "signal_type", "sent_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_smart_money_alerts_user_signal_sent", table_name="smart_money_alerts_log")
    op.drop_index("ix_smart_money_alerts_log_wallet_address", table_name="smart_money_alerts_log")
    op.drop_index("ix_smart_money_alerts_log_telegram_user_id", table_name="smart_money_alerts_log")
    op.drop_index("ix_smart_money_alerts_log_sent_at", table_name="smart_money_alerts_log")
    op.drop_index("ix_smart_money_alerts_log_market_id", table_name="smart_money_alerts_log")
    op.drop_table("smart_money_alerts_log")

    op.drop_index("ix_tracked_traders_wallet_address", table_name="tracked_traders")
    op.drop_index("ix_tracked_traders_user_id", table_name="tracked_traders")
    op.drop_index("ix_tracked_traders_user_created", table_name="tracked_traders")
    op.drop_index("ix_tracked_traders_telegram_user_id", table_name="tracked_traders")
    op.drop_index("ix_tracked_traders_created_at", table_name="tracked_traders")
    op.drop_table("tracked_traders")

    op.drop_index("ix_smart_money_snapshots_wallet_address", table_name="smart_money_snapshots")
    op.drop_index("ix_smart_money_snapshots_type_created", table_name="smart_money_snapshots")
    op.drop_index("ix_smart_money_snapshots_signal_type", table_name="smart_money_snapshots")
    op.drop_index("ix_smart_money_snapshots_market_id", table_name="smart_money_snapshots")
    op.drop_index("ix_smart_money_snapshots_market_created", table_name="smart_money_snapshots")
    op.drop_index("ix_smart_money_snapshots_created_at", table_name="smart_money_snapshots")
    op.drop_index("ix_smart_money_snapshots_created", table_name="smart_money_snapshots")
    op.drop_table("smart_money_snapshots")

    op.drop_column("users", "smart_money_alerts_enabled")
