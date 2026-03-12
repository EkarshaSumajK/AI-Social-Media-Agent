"""Add campaigns, campaign_pieces, competitors, hook_templates, swipe_files tables

Revision ID: 20260303_0006
Revises: 20260303_0005
Create Date: 2026-03-03 00:06:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260303_0006'
down_revision = '20260303_0005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'campaigns',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('goal', sa.String(length=255), nullable=True),
        sa.Column('audience_description', sa.Text(), nullable=True),
        sa.Column('platforms', sa.JSON(), nullable=True),
        sa.Column('platform_entity', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_campaigns_platform_entity', 'campaigns', ['platform_entity'])
    op.create_index('ix_campaigns_status', 'campaigns', ['status'])
    op.create_index('ix_campaigns_created_by', 'campaigns', ['created_by'])

    op.create_table(
        'campaign_pieces',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('phase', sa.String(length=20), nullable=False),
        sa.Column('content_type', sa.String(length=30), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaigns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_campaign_pieces_campaign_id', 'campaign_pieces', ['campaign_id'])
    op.create_index('ix_campaign_pieces_phase', 'campaign_pieces', ['phase'])

    op.create_table(
        'competitors',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('profile_url', sa.String(length=2048), nullable=False),
        sa.Column('platform_entity', sa.String(length=20), nullable=False),
        sa.Column('tracked_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['tracked_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_competitors_platform', 'competitors', ['platform'])
    op.create_index('ix_competitors_platform_entity', 'competitors', ['platform_entity'])
    op.create_index('ix_competitors_tracked_by', 'competitors', ['tracked_by'])

    op.create_table(
        'hook_templates',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hook_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=30), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('industry', sa.String(length=100), nullable=True),
        sa.Column('use_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_hook_templates_category', 'hook_templates', ['category'])
    op.create_index('ix_hook_templates_platform', 'hook_templates', ['platform'])
    op.create_index('ix_hook_templates_industry', 'hook_templates', ['industry'])

    op.create_table(
        'swipe_files',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_url', sa.String(length=2048), nullable=True),
        sa.Column('performance_notes', sa.Text(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_swipe_files_user_id', 'swipe_files', ['user_id'])
    op.create_index('ix_swipe_files_platform', 'swipe_files', ['platform'])


def downgrade() -> None:
    op.drop_table('swipe_files')
    op.drop_table('hook_templates')
    op.drop_table('competitors')
    op.drop_table('campaign_pieces')
    op.drop_table('campaigns')
