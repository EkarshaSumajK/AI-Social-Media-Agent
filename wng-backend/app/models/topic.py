from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Topic(Base):
    __tablename__ = 'topics'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), index=True)
    source_url: Mapped[str] = mapped_column(String(2048), unique=True, index=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    relevance_label: Mapped[str] = mapped_column(String(16), default='low', index=True)
    relevance_score: Mapped[int] = mapped_column(Integer, default=0)
    age_group: Mapped[str] = mapped_column(String(16), default='unknown')
    topic_type: Mapped[str] = mapped_column(String(20), default='general')
    mental_health_specific: Mapped[bool] = mapped_column(Boolean, default=False)
    screening_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    trust_score: Mapped[int] = mapped_column(Integer, default=0)
    is_trending: Mapped[bool] = mapped_column(Boolean, default=False)
    x_engagement_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    x_tweet_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    x_trend_phrase: Mapped[str | None] = mapped_column(String(500), nullable=True)
    x_top_tweet_raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    trend_regions: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    public_concerns: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    trend_statements: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    trend_sentiment: Mapped[str | None] = mapped_column(String(32), nullable=True)
    statistics: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    related_keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    original_published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    platform: Mapped[str] = mapped_column(String(50), default='horizon', index=True)
    topic_category: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    region: Mapped[str] = mapped_column(String(10), default='global', index=True)
    status: Mapped[str] = mapped_column(String(50), default='new', index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles = relationship('Article', back_populates='topic', cascade='all, delete-orphan')
