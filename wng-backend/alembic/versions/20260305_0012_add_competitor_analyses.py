"""Add competitor_analyses table

Revision ID: 20260305_0012
Revises: 20260305_0011
Create Date: 2026-03-05 00:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '20260305_0012'
down_revision: str | None = '20260305_0011'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'competitor_analyses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('analysis', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_competitor_analyses_competitor_id', 'competitor_analyses', ['competitor_id'])


def downgrade() -> None:
    op.drop_index('ix_competitor_analyses_competitor_id', table_name='competitor_analyses')
    op.drop_table('competitor_analyses')
