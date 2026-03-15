"""Add image_url column to social_posts table

Revision ID: 20260314_0014
Revises: 20260307_0013
Create Date: 2026-03-14 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260314_0014'
down_revision = '20260307_0013'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('social_posts', sa.Column('image_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('social_posts', 'image_url')
