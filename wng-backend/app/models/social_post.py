from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SocialPlatform, SocialStatus


class SocialPost(Base):
    __tablename__ = 'social_posts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey('articles.id', ondelete='CASCADE'), index=True)
    platform: Mapped[SocialPlatform] = mapped_column(Enum(SocialPlatform), index=True)
    caption: Mapped[str] = mapped_column(Text)
    edited_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[SocialStatus] = mapped_column(Enum(SocialStatus), default=SocialStatus.DRAFT, index=True)
    external_post_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    article = relationship('Article', back_populates='social_posts')
