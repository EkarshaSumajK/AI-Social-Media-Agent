"""Add x_engagement_score and x_tweet_count to topics

Revision ID: 20260223_0003
Revises: 20260220_0002
Create Date: 2026-02-23 11:45:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260223_0003'
down_revision = '20260220_0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('topics', sa.Column('x_engagement_score', sa.Float(), nullable=True))
    op.add_column('topics', sa.Column('x_tweet_count', sa.Integer(), nullable=True))
    op.add_column('topics', sa.Column('x_trend_phrase', sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column('topics', 'x_trend_phrase')
    op.drop_column('topics', 'x_tweet_count')
    op.drop_column('topics', 'x_engagement_score')
