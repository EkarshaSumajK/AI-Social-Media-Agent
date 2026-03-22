from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import ArticleStatus, Platform


class Article(Base):
    __tablename__ = 'articles'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey('topics.id', ondelete='CASCADE'), unique=True, index=True)

    content_html: Mapped[str] = mapped_column(Text)
    seo_title: Mapped[str] = mapped_column(String(300))
    meta_description: Mapped[str] = mapped_column(String(500))
    keywords: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    issue_summary: Mapped[str] = mapped_column(Text)
    why_it_matters: Mapped[str] = mapped_column(Text)
    mental_health_implications: Mapped[str] = mapped_column(Text)
    professional_insight: Mapped[str] = mapped_column(Text)
    how_services_help: Mapped[str] = mapped_column(Text)
    call_to_action: Mapped[str] = mapped_column(Text)
    disclaimer_text: Mapped[str] = mapped_column(String(255), default='This content is for educational purposes only')
    readability_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_generated_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_similarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    structure_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_notes: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    source_url: Mapped[str] = mapped_column(String(2048))
    body_image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    field_image_urls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[ArticleStatus] = mapped_column(Enum(ArticleStatus), default=ArticleStatus.DRAFT, index=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, values_callable=lambda obj: [e.value for e in obj]), default=Platform.HORIZON, index=True)
    slug: Mapped[str | None] = mapped_column(String(500), unique=True, nullable=True, index=True)

    virality_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    clarity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    hook_strength_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    conversion_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    wordpress_post_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    requires_review: Mapped[bool] = mapped_column(default=True)
    internal_links_added: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    topic = relationship('Topic', back_populates='articles')
    creator = relationship('User', foreign_keys=[created_by], back_populates='created_articles')
    approver = relationship('User', foreign_keys=[approved_by], back_populates='approved_articles')
    social_posts = relationship('SocialPost', back_populates='article', cascade='all, delete-orphan')
