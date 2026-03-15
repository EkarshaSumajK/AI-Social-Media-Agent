"""Add x_top_tweet_raw to topics

Revision ID: 20260224_0004
Revises: 20260223_0003
Create Date: 2026-02-24 14:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260224_0004'
down_revision = '20260223_0003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('topics', sa.Column('x_top_tweet_raw', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('topics', 'x_top_tweet_raw')
