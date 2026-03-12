"""Initial schema

Revision ID: 20260218_0001
Revises:
Create Date: 2026-02-18 20:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260218_0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('REVIEWER', 'ADMIN', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'], unique=False)

    op.create_table(
        'topics',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('source_url', sa.String(length=2048), nullable=False),
        sa.Column('source_name', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('embedding', sa.JSON(), nullable=True),
        sa.Column('related_keywords', sa.JSON(), nullable=True),
        sa.Column('original_published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('NEW', 'PROCESSED', 'DUPLICATE_REJECTED', name='topicstatus'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_topics_source_url', 'topics', ['source_url'], unique=True)
    op.create_index('ix_topics_status', 'topics', ['status'], unique=False)
    op.create_index('ix_topics_title', 'topics', ['title'], unique=False)

    op.create_table(
        'articles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('topic_id', sa.Integer(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=False),
        sa.Column('seo_title', sa.String(length=300), nullable=False),
        sa.Column('meta_description', sa.String(length=500), nullable=False),
        sa.Column('keywords', sa.JSON(), nullable=True),
        sa.Column('issue_summary', sa.Text(), nullable=False),
        sa.Column('why_it_matters', sa.Text(), nullable=False),
        sa.Column('mental_health_implications', sa.Text(), nullable=False),
        sa.Column('professional_insight', sa.Text(), nullable=False),
        sa.Column('how_services_help', sa.Text(), nullable=False),
        sa.Column('call_to_action', sa.Text(), nullable=False),
        sa.Column('disclaimer_text', sa.String(length=255), nullable=False),
        sa.Column('source_url', sa.String(length=2048), nullable=False),
        sa.Column('status', sa.Enum('DRAFT', 'APPROVED', 'REJECTED', 'PUBLISHED', name='articlestatus'), nullable=False),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_url', sa.String(length=2048), nullable=True),
        sa.Column('wordpress_post_id', sa.String(length=100), nullable=True),
        sa.Column('requires_review', sa.Boolean(), nullable=False),
        sa.Column('internal_links_added', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['topic_id'], ['topics.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_articles_status', 'articles', ['status'], unique=False)
    op.create_index('ix_articles_topic_id', 'articles', ['topic_id'], unique=True)

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(length=120), nullable=False),
        sa.Column('entity_type', sa.String(length=80), nullable=False),
        sa.Column('entity_id', sa.String(length=120), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_logs_action', 'audit_logs', ['action'], unique=False)
    op.create_index('ix_audit_logs_actor_id', 'audit_logs', ['actor_id'], unique=False)
    op.create_index('ix_audit_logs_created_at', 'audit_logs', ['created_at'], unique=False)
    op.create_index('ix_audit_logs_entity_id', 'audit_logs', ['entity_id'], unique=False)
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'], unique=False)

    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.Enum('INSTAGRAM', 'LINKEDIN', 'TWITTER', 'FACEBOOK', name='socialplatform'), nullable=False),
        sa.Column('caption', sa.Text(), nullable=False),
        sa.Column('edited_caption', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DRAFT', 'READY', 'POSTED', 'FAILED', name='socialstatus'), nullable=False),
        sa.Column('external_post_id', sa.String(length=255), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('posted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['article_id'], ['articles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_social_posts_article_id', 'social_posts', ['article_id'], unique=False)
    op.create_index('ix_social_posts_platform', 'social_posts', ['platform'], unique=False)
    op.create_index('ix_social_posts_status', 'social_posts', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_social_posts_status', table_name='social_posts')
    op.drop_index('ix_social_posts_platform', table_name='social_posts')
    op.drop_index('ix_social_posts_article_id', table_name='social_posts')
    op.drop_table('social_posts')

    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_created_at', table_name='audit_logs')
    op.drop_index('ix_audit_logs_actor_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_action', table_name='audit_logs')
    op.drop_table('audit_logs')

    op.drop_index('ix_articles_topic_id', table_name='articles')
    op.drop_index('ix_articles_status', table_name='articles')
    op.drop_table('articles')

    op.drop_index('ix_topics_title', table_name='topics')
    op.drop_index('ix_topics_status', table_name='topics')
    op.drop_index('ix_topics_source_url', table_name='topics')
    op.drop_table('topics')

    op.drop_index('ix_users_role', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

    sa.Enum('DRAFT', 'READY', 'POSTED', 'FAILED', name='socialstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('INSTAGRAM', 'LINKEDIN', 'TWITTER', 'FACEBOOK', name='socialplatform').drop(op.get_bind(), checkfirst=True)
    sa.Enum('DRAFT', 'APPROVED', 'REJECTED', 'PUBLISHED', name='articlestatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('NEW', 'PROCESSED', 'DUPLICATE_REJECTED', name='topicstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('REVIEWER', 'ADMIN', name='userrole').drop(op.get_bind(), checkfirst=True)
