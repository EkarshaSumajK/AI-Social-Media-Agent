"""Add daily_post_batches table for storing generated post history

Revision ID: 20260304_0008
Revises: 20260303_0007
Create Date: 2026-03-04 00:08:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260304_0008'
down_revision = '20260303_0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'daily_post_batches',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('industry', sa.String(255), nullable=False),
        sa.Column('region', sa.String(50), nullable=False, server_default='global'),
        sa.Column('target_audience', sa.String(500), nullable=False),
        sa.Column('business_goal', sa.String(50), nullable=False, server_default='brand'),
        sa.Column('suggestions', sa.JSON(), nullable=False),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_daily_post_batches_created_by', 'daily_post_batches', ['created_by'])


def downgrade() -> None:
    op.drop_index('ix_daily_post_batches_created_by', table_name='daily_post_batches')
    op.drop_table('daily_post_batches')
