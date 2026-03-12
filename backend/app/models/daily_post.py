from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class DailyPostBatch(Base):
    __tablename__ = 'daily_post_batches'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    industry: Mapped[str] = mapped_column(String(255))
    region: Mapped[str] = mapped_column(String(50), default='global')
    target_audience: Mapped[str] = mapped_column(String(500))
    business_goal: Mapped[str] = mapped_column(String(50), default='brand')
    suggestions: Mapped[list] = mapped_column(JSON)  # list[{post_type, content, platform_hint}]
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
