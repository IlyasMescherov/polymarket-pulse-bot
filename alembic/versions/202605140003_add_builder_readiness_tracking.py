"""add builder readiness tracking

Revision ID: 202605140003
Revises: 202605140002
Create Date: 2026-05-14 11:30:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "202605140003"
down_revision = "202605140002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_link_clicks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("market_id", sa.String(length=64), nullable=False),
        sa.Column("market_title", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_link_clicks_created_at",
        "market_link_clicks",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_link_clicks_market_created",
        "market_link_clicks",
        ["market_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_link_clicks_market_id",
        "market_link_clicks",
        ["market_id"],
        unique=False,
    )
    op.create_index(
        "ix_market_link_clicks_source",
        "market_link_clicks",
        ["source"],
        unique=False,
    )
    op.create_index(
        "ix_market_link_clicks_telegram_user_id",
        "market_link_clicks",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_market_link_clicks_user_created",
        "market_link_clicks",
        ["telegram_user_id", "created_at"],
        unique=False,
    )

    op.create_table(
        "search_queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_user_id", sa.BigInteger(), nullable=False),
        sa.Column("query", sa.String(length=255), nullable=False),
        sa.Column(
            "results_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_search_queries_created_at",
        "search_queries",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_search_queries_query",
        "search_queries",
        ["query"],
        unique=False,
    )
    op.create_index(
        "ix_search_queries_query_created",
        "search_queries",
        ["query", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_search_queries_telegram_user_id",
        "search_queries",
        ["telegram_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_search_queries_user_created",
        "search_queries",
        ["telegram_user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_search_queries_user_created", table_name="search_queries")
    op.drop_index("ix_search_queries_telegram_user_id", table_name="search_queries")
    op.drop_index("ix_search_queries_query_created", table_name="search_queries")
    op.drop_index("ix_search_queries_query", table_name="search_queries")
    op.drop_index("ix_search_queries_created_at", table_name="search_queries")
    op.drop_table("search_queries")
    op.drop_index("ix_market_link_clicks_user_created", table_name="market_link_clicks")
    op.drop_index(
        "ix_market_link_clicks_telegram_user_id",
        table_name="market_link_clicks",
    )
    op.drop_index("ix_market_link_clicks_source", table_name="market_link_clicks")
    op.drop_index("ix_market_link_clicks_market_id", table_name="market_link_clicks")
    op.drop_index("ix_market_link_clicks_market_created", table_name="market_link_clicks")
    op.drop_index("ix_market_link_clicks_created_at", table_name="market_link_clicks")
    op.drop_table("market_link_clicks")
