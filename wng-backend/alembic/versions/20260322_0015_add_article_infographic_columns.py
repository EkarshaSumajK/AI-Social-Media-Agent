"""Add body_image_url and field_image_urls columns to articles table

Revision ID: 20260322_0015
Revises: 20260314_0014
Create Date: 2026-03-22 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260322_0015'
down_revision = '20260314_0014'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('articles', sa.Column('body_image_url', sa.String(2048), nullable=True))
    op.add_column('articles', sa.Column('field_image_urls', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('articles', 'field_image_urls')
    op.drop_column('articles', 'body_image_url')
