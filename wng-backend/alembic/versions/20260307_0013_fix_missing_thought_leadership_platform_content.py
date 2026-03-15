"""Fix missing thought_leadership_generations and platform_content_generations tables

Revision ID: 20260307_0013
Revises: 20260305_0012
Create Date: 2026-03-07 00:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '20260307_0013'
down_revision = '20260305_0012'
branch_labels = None
depends_on = None


def _table_exists(name: str) -> bool:
    bind = op.get_bind()
    inspector = Inspector.from_engine(bind)
    return name in inspector.get_table_names()


def upgrade() -> None:
    if not _table_exists('thought_leadership_generations'):
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

    if not _table_exists('platform_content_generations'):
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
    pass
