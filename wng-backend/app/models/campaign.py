from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Campaign(Base):
    __tablename__ = 'campaigns'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500))
    event_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    goal: Mapped[str | None] = mapped_column(String(255), nullable=True)
    audience_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    platforms: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    platform_entity: Mapped[str] = mapped_column(String(20), index=True)  # horizon/connect/parentshala
    status: Mapped[str] = mapped_column(String(20), default='draft', index=True)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    pieces = relationship('CampaignPiece', back_populates='campaign', cascade='all, delete-orphan')


class CampaignPiece(Base):
    __tablename__ = 'campaign_pieces'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    campaign_id: Mapped[int] = mapped_column(ForeignKey('campaigns.id', ondelete='CASCADE'), index=True)
    phase: Mapped[str] = mapped_column(String(20), index=True)  # pre, during, post
    content_type: Mapped[str] = mapped_column(String(30))  # email, social, ad, landing_page, countdown, reel_script
    platform: Mapped[str | None] = mapped_column(String(20), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    scheduled_for: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default='draft')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    campaign = relationship('Campaign', back_populates='pieces')
