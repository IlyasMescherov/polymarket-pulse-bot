"""add external news intelligence

Revision ID: 202605160001
Revises: 202605140006
Create Date: 2026-05-16 16:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605160001"
down_revision: str | None = "202605140006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "external_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column(
            "credibility_score",
            sa.Float(),
            server_default=sa.text("60"),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(length=64),
            server_default=sa.text("'global'"),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url", name="uq_external_sources_url"),
    )
    op.create_index(
        "ix_external_sources_category_active",
        "external_sources",
        ["category", "is_active"],
        unique=False,
    )
    op.create_index(
        "ix_external_sources_type_active",
        "external_sources",
        ["source_type", "is_active"],
        unique=False,
    )
    op.create_index(op.f("ix_external_sources_category"), "external_sources", ["category"], unique=False)
    op.create_index(op.f("ix_external_sources_is_active"), "external_sources", ["is_active"], unique=False)
    op.create_index(op.f("ix_external_sources_source_type"), "external_sources", ["source_type"], unique=False)

    op.create_table(
        "external_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("entities", sa.JSON(), nullable=True),
        sa.Column("topics", sa.JSON(), nullable=True),
        sa.Column("sentiment", sa.String(length=32), nullable=True),
        sa.Column(
            "urgency_score",
            sa.Float(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column(
            "credibility_score",
            sa.Float(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["source_id"], ["external_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "url", name="uq_external_events_source_url"),
    )
    op.create_index(
        "ix_external_events_category_published",
        "external_events",
        ["category", "published_at"],
        unique=False,
    )
    op.create_index(
        "ix_external_events_created",
        "external_events",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_external_events_source_published",
        "external_events",
        ["source_id", "published_at"],
        unique=False,
    )
    op.create_index(op.f("ix_external_events_category"), "external_events", ["category"], unique=False)
    op.create_index(op.f("ix_external_events_created_at"), "external_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_external_events_published_at"), "external_events", ["published_at"], unique=False)
    op.create_index(op.f("ix_external_events_source_id"), "external_events", ["source_id"], unique=False)

    op.create_table(
        "market_event_links",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("market_id", sa.String(length=128), nullable=False),
        sa.Column("external_event_id", sa.Integer(), nullable=False),
        sa.Column(
            "relevance_score",
            sa.Float(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("match_reason", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["external_event_id"], ["external_events.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "market_id",
            "external_event_id",
            name="uq_market_event_links_market_event",
        ),
    )
    op.create_index(
        "ix_market_event_links_event_created",
        "market_event_links",
        ["external_event_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_market_event_links_market_created",
        "market_event_links",
        ["market_id", "created_at"],
        unique=False,
    )
    op.create_index(op.f("ix_market_event_links_created_at"), "market_event_links", ["created_at"], unique=False)
    op.create_index(op.f("ix_market_event_links_external_event_id"), "market_event_links", ["external_event_id"], unique=False)
    op.create_index(op.f("ix_market_event_links_market_id"), "market_event_links", ["market_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_market_event_links_market_id"), table_name="market_event_links")
    op.drop_index(op.f("ix_market_event_links_external_event_id"), table_name="market_event_links")
    op.drop_index(op.f("ix_market_event_links_created_at"), table_name="market_event_links")
    op.drop_index("ix_market_event_links_market_created", table_name="market_event_links")
    op.drop_index("ix_market_event_links_event_created", table_name="market_event_links")
    op.drop_table("market_event_links")

    op.drop_index(op.f("ix_external_events_source_id"), table_name="external_events")
    op.drop_index(op.f("ix_external_events_published_at"), table_name="external_events")
    op.drop_index(op.f("ix_external_events_created_at"), table_name="external_events")
    op.drop_index(op.f("ix_external_events_category"), table_name="external_events")
    op.drop_index("ix_external_events_source_published", table_name="external_events")
    op.drop_index("ix_external_events_created", table_name="external_events")
    op.drop_index("ix_external_events_category_published", table_name="external_events")
    op.drop_table("external_events")

    op.drop_index(op.f("ix_external_sources_source_type"), table_name="external_sources")
    op.drop_index(op.f("ix_external_sources_is_active"), table_name="external_sources")
    op.drop_index(op.f("ix_external_sources_category"), table_name="external_sources")
    op.drop_index("ix_external_sources_type_active", table_name="external_sources")
    op.drop_index("ix_external_sources_category_active", table_name="external_sources")
    op.drop_table("external_sources")
