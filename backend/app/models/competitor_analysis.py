from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CompetitorAnalysis(Base):
    __tablename__ = 'competitor_analyses'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey('competitors.id', ondelete='CASCADE'), index=True)
    analysis: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
