from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class YoutubeShort(Base):
    __tablename__ = 'youtube_shorts'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(500))
    target_audience: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration: Mapped[int] = mapped_column(Integer, default=60)  # seconds
    hook: Mapped[str] = mapped_column(Text)
    script: Mapped[dict] = mapped_column(JSON)   # {intro, main_points, cta}
    titles: Mapped[list] = mapped_column(JSON)   # list of 3 title options
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list] = mapped_column(JSON)     # list of tag strings
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
