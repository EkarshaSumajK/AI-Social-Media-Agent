"""Add quality intelligence and trend metadata

Revision ID: 20260220_0002
Revises: 20260218_0001
Create Date: 2026-02-20 13:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260220_0002'
down_revision = '20260218_0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('topics', sa.Column('relevance_label', sa.String(length=16), server_default='low', nullable=False))
    op.add_column('topics', sa.Column('relevance_score', sa.Integer(), server_default='0', nullable=False))
    op.add_column('topics', sa.Column('age_group', sa.String(length=16), server_default='unknown', nullable=False))
    op.add_column('topics', sa.Column('topic_type', sa.String(length=20), server_default='general', nullable=False))
    op.add_column('topics', sa.Column('mental_health_specific', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('topics', sa.Column('screening_reason', sa.Text(), nullable=True))
    op.add_column('topics', sa.Column('trust_score', sa.Integer(), server_default='0', nullable=False))
    op.add_column('topics', sa.Column('is_trending', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('topics', sa.Column('trend_regions', sa.JSON(), nullable=True))
    op.add_column('topics', sa.Column('public_concerns', sa.JSON(), nullable=True))
    op.add_column('topics', sa.Column('trend_statements', sa.JSON(), nullable=True))
    op.add_column('topics', sa.Column('trend_sentiment', sa.String(length=32), nullable=True))
    op.add_column('topics', sa.Column('statistics', sa.JSON(), nullable=True))
    op.create_index('ix_topics_relevance_label', 'topics', ['relevance_label'], unique=False)

    op.add_column('articles', sa.Column('readability_score', sa.Float(), nullable=True))
    op.add_column('articles', sa.Column('ai_generated_probability', sa.Float(), nullable=True))
    op.add_column('articles', sa.Column('source_similarity_score', sa.Float(), nullable=True))
    op.add_column('articles', sa.Column('structure_valid', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('articles', sa.Column('quality_notes', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('articles', 'quality_notes')
    op.drop_column('articles', 'structure_valid')
    op.drop_column('articles', 'source_similarity_score')
    op.drop_column('articles', 'ai_generated_probability')
    op.drop_column('articles', 'readability_score')

    op.drop_index('ix_topics_relevance_label', table_name='topics')
    op.drop_column('topics', 'statistics')
    op.drop_column('topics', 'trend_sentiment')
    op.drop_column('topics', 'trend_statements')
    op.drop_column('topics', 'public_concerns')
    op.drop_column('topics', 'trend_regions')
    op.drop_column('topics', 'is_trending')
    op.drop_column('topics', 'trust_score')
    op.drop_column('topics', 'screening_reason')
    op.drop_column('topics', 'mental_health_specific')
    op.drop_column('topics', 'topic_type')
    op.drop_column('topics', 'age_group')
    op.drop_column('topics', 'relevance_score')
    op.drop_column('topics', 'relevance_label')
