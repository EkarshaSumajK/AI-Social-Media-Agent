from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RegionalContent(Base):
    __tablename__ = 'regional_content'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    region: Mapped[str] = mapped_column(String(100))           # india, usa, uk, uae, global, etc.
    industry: Mapped[str] = mapped_column(String(200))
    language_style: Mapped[str] = mapped_column(String(100), default='english')
    original_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    localised_content: Mapped[str | None] = mapped_column(Text, nullable=True)
    trending_topics: Mapped[list | None] = mapped_column(JSON, nullable=True)  # [{topic, relevance_reason, content_angle, urgency}]
    hashtags: Mapped[dict | None] = mapped_column(JSON, nullable=True)         # {primary, secondary, trending}
    platform: Mapped[str | None] = mapped_column(String(50), nullable=True)
    request_type: Mapped[str] = mapped_column(String(50), default='localise')  # localise, trending_topics, hashtags
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
