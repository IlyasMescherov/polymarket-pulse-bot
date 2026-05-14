"""add published posts

Revision ID: 202605140006
Revises: 202605140005
Create Date: 2026-05-14 17:00:00.000000
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "202605140006"
down_revision: str | None = "202605140005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "published_posts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("platform", sa.String(length=32), nullable=False),
        sa.Column("post_type", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "platform",
            "content_hash",
            name="uq_published_posts_platform_hash",
        ),
    )
    op.create_index(
        op.f("ix_published_posts_content_hash"),
        "published_posts",
        ["content_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_published_posts_created_at"),
        "published_posts",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_published_posts_platform_created",
        "published_posts",
        ["platform", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_published_posts_platform_status_created",
        "published_posts",
        ["platform", "status", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_published_posts_platform"),
        "published_posts",
        ["platform"],
        unique=False,
    )
    op.create_index(
        op.f("ix_published_posts_post_type"),
        "published_posts",
        ["post_type"],
        unique=False,
    )
    op.create_index(
        "ix_published_posts_type_created",
        "published_posts",
        ["post_type", "created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_published_posts_published_at"),
        "published_posts",
        ["published_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_published_posts_status"),
        "published_posts",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_published_posts_status"), table_name="published_posts")
    op.drop_index(op.f("ix_published_posts_published_at"), table_name="published_posts")
    op.drop_index("ix_published_posts_type_created", table_name="published_posts")
    op.drop_index(op.f("ix_published_posts_post_type"), table_name="published_posts")
    op.drop_index(op.f("ix_published_posts_platform"), table_name="published_posts")
    op.drop_index(
        "ix_published_posts_platform_status_created",
        table_name="published_posts",
    )
    op.drop_index("ix_published_posts_platform_created", table_name="published_posts")
    op.drop_index(op.f("ix_published_posts_created_at"), table_name="published_posts")
    op.drop_index(op.f("ix_published_posts_content_hash"), table_name="published_posts")
    op.drop_table("published_posts")
