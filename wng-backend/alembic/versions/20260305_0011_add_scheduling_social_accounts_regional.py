"""add scheduling social_accounts regional_content

Revision ID: 20260305_0011
Revises: 20260304_0010_add_youtube_shorts
Create Date: 2026-03-05 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '20260305_0011'
down_revision: str | None = '20260304_0010'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # -- social_accounts --
    op.create_table(
        'social_accounts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('account_name', sa.String(255), nullable=False),
        sa.Column('account_id', sa.String(255), nullable=True),
        sa.Column('access_token', sa.Text, nullable=True),
        sa.Column('refresh_token', sa.Text, nullable=True),
        sa.Column('token_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='connected'),
        sa.Column('scopes', sa.Text, nullable=True),
        sa.Column('profile_image_url', sa.Text, nullable=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # -- scheduled_posts --
    op.create_table(
        'scheduled_posts',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('content_type', sa.String(100), nullable=False, server_default='post'),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='draft'),
        sa.Column('hashtags', sa.JSON, nullable=True),
        sa.Column('media_urls', sa.JSON, nullable=True),
        sa.Column('campaign_id', sa.Integer, sa.ForeignKey('campaigns.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('social_account_id', sa.Integer, nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # -- regional_content --
    op.create_table(
        'regional_content',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('region', sa.String(100), nullable=False),
        sa.Column('industry', sa.String(200), nullable=False),
        sa.Column('language_style', sa.String(100), nullable=False, server_default='english'),
        sa.Column('original_content', sa.Text, nullable=True),
        sa.Column('localised_content', sa.Text, nullable=True),
        sa.Column('trending_topics', sa.JSON, nullable=True),
        sa.Column('hashtags', sa.JSON, nullable=True),
        sa.Column('platform', sa.String(50), nullable=True),
        sa.Column('request_type', sa.String(50), nullable=False, server_default='localise'),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('regional_content')
    op.drop_table('scheduled_posts')
    op.drop_table('social_accounts')
