"""Standardize user tracking: rename user_id/tracked_by to created_by, add articles.created_by, add hook_templates.created_by

Revision ID: 20260303_0007
Revises: 20260303_0006
Create Date: 2026-03-03 00:07:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '20260303_0007'
down_revision = '20260303_0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -- swipe_files: rename user_id -> created_by --
    op.alter_column('swipe_files', 'user_id', new_column_name='created_by')
    op.drop_index('ix_swipe_files_user_id', table_name='swipe_files')
    op.create_index('ix_swipe_files_created_by', 'swipe_files', ['created_by'])

    # -- competitors: rename tracked_by -> created_by --
    op.alter_column('competitors', 'tracked_by', new_column_name='created_by')
    op.drop_index('ix_competitors_tracked_by', table_name='competitors')
    op.create_index('ix_competitors_created_by', 'competitors', ['created_by'])

    # -- articles: add created_by --
    op.add_column('articles', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_articles_created_by_users',
        'articles', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_articles_created_by', 'articles', ['created_by'])

    # -- hook_templates: add created_by --
    op.add_column('hook_templates', sa.Column('created_by', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_hook_templates_created_by_users',
        'hook_templates', 'users',
        ['created_by'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_hook_templates_created_by', 'hook_templates', ['created_by'])


def downgrade() -> None:
    # -- hook_templates --
    op.drop_index('ix_hook_templates_created_by', table_name='hook_templates')
    op.drop_constraint('fk_hook_templates_created_by_users', 'hook_templates', type_='foreignkey')
    op.drop_column('hook_templates', 'created_by')

    # -- articles --
    op.drop_index('ix_articles_created_by', table_name='articles')
    op.drop_constraint('fk_articles_created_by_users', 'articles', type_='foreignkey')
    op.drop_column('articles', 'created_by')

    # -- competitors: revert created_by -> tracked_by --
    op.drop_index('ix_competitors_created_by', table_name='competitors')
    op.alter_column('competitors', 'created_by', new_column_name='tracked_by')
    op.create_index('ix_competitors_tracked_by', 'competitors', ['tracked_by'])

    # -- swipe_files: revert created_by -> user_id --
    op.drop_index('ix_swipe_files_created_by', table_name='swipe_files')
    op.alter_column('swipe_files', 'created_by', new_column_name='user_id')
    op.create_index('ix_swipe_files_user_id', 'swipe_files', ['user_id'])
