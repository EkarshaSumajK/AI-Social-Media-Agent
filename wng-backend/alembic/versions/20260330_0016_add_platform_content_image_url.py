"""Add image_url to platform_content_generations and thought_leadership_generations

Revision ID: 20260330_0016
Revises: 20260322_0015
Create Date: 2026-03-30 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260330_0016'
down_revision = '20260322_0015'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('platform_content_generations', sa.Column('image_url', sa.Text(), nullable=True))
    op.add_column('thought_leadership_generations', sa.Column('image_url', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('thought_leadership_generations', 'image_url')
    op.drop_column('platform_content_generations', 'image_url')
