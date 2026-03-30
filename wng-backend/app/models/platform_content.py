from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PlatformContentGeneration(Base):
    __tablename__ = 'platform_content_generations'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String(500))
    platform: Mapped[str] = mapped_column(String(50))
    content_type: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    gen_metadata: Mapped[dict | None] = mapped_column('metadata', JSON, nullable=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
