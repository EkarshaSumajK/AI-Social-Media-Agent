"""Add youtube_shorts table

Revision ID: 20260304_0010
Revises: 20260304_0009
Create Date: 2026-03-04 00:10:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260304_0010'
down_revision = '20260304_0009'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'youtube_shorts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic', sa.String(500), nullable=False),
        sa.Column('target_audience', sa.String(500), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('hook', sa.Text(), nullable=False),
        sa.Column('script', sa.JSON(), nullable=False),
        sa.Column('titles', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_youtube_shorts_created_by', 'youtube_shorts', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_youtube_shorts_created_by', table_name='youtube_shorts')
    op.drop_table('youtube_shorts')
