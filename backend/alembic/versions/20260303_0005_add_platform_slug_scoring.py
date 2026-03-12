"""Add platform, slug, and scoring columns

Revision ID: 20260303_0005
Revises: 20260224_0004
Create Date: 2026-03-03 00:05:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260303_0005'
down_revision = '20260224_0004'
branch_labels = None
depends_on = None

platform_enum = sa.Enum('horizon', 'connect', 'parentshala', name='platform')


def upgrade() -> None:
    platform_enum.create(op.get_bind(), checkfirst=True)

    # -- users --
    op.add_column('users', sa.Column('platform', platform_enum, server_default='horizon', nullable=False))
    op.create_index('ix_users_platform', 'users', ['platform'], unique=False)

    # -- articles --
    op.add_column('articles', sa.Column('platform', platform_enum, server_default='horizon', nullable=False))
    op.add_column('articles', sa.Column('slug', sa.String(length=500), nullable=True, unique=True))
    op.add_column('articles', sa.Column('virality_score', sa.Float(), nullable=True))
    op.add_column('articles', sa.Column('clarity_score', sa.Float(), nullable=True))
    op.add_column('articles', sa.Column('hook_strength_score', sa.Float(), nullable=True))
    op.add_column('articles', sa.Column('conversion_score', sa.Float(), nullable=True))
    op.create_index('ix_articles_platform', 'articles', ['platform'], unique=False)
    op.create_index('ix_articles_slug', 'articles', ['slug'], unique=True)

    # -- topics --
    op.add_column('topics', sa.Column('platform', platform_enum, server_default='horizon', nullable=False))
    op.add_column('topics', sa.Column('topic_category', sa.String(length=30), nullable=True))
    op.add_column('topics', sa.Column('region', sa.String(length=10), server_default='global', nullable=False))
    op.create_index('ix_topics_platform', 'topics', ['platform'], unique=False)
    op.create_index('ix_topics_topic_category', 'topics', ['topic_category'], unique=False)
    op.create_index('ix_topics_region', 'topics', ['region'], unique=False)


def downgrade() -> None:
    # -- topics --
    op.drop_index('ix_topics_region', table_name='topics')
    op.drop_index('ix_topics_topic_category', table_name='topics')
    op.drop_index('ix_topics_platform', table_name='topics')
    op.drop_column('topics', 'region')
    op.drop_column('topics', 'topic_category')
    op.drop_column('topics', 'platform')

    # -- articles --
    op.drop_index('ix_articles_slug', table_name='articles')
    op.drop_index('ix_articles_platform', table_name='articles')
    op.drop_column('articles', 'conversion_score')
    op.drop_column('articles', 'hook_strength_score')
    op.drop_column('articles', 'clarity_score')
    op.drop_column('articles', 'virality_score')
    op.drop_column('articles', 'slug')
    op.drop_column('articles', 'platform')

    # -- users --
    op.drop_index('ix_users_platform', table_name='users')
    op.drop_column('users', 'platform')

    platform_enum.drop(op.get_bind(), checkfirst=True)
