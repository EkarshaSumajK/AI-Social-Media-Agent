"""Add thought_leadership_generations and platform_content_generations tables

Revision ID: 20260304_0009
Revises: 20260304_0008
Create Date: 2026-03-04 00:09:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260304_0009'
down_revision = '20260304_0008'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'thought_leadership_generations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic', sa.String(500), nullable=False),
        sa.Column('industry', sa.String(255), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_thought_leadership_generations_created_by', 'thought_leadership_generations', ['created_by'])

    op.create_table(
        'platform_content_generations',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic', sa.String(500), nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_platform_content_generations_created_by', 'platform_content_generations', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_platform_content_generations_created_by', table_name='platform_content_generations')
    op.drop_table('platform_content_generations')
    op.drop_index('ix_thought_leadership_generations_created_by', table_name='thought_leadership_generations')
    op.drop_table('thought_leadership_generations')
