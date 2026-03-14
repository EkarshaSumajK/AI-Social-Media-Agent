from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class HookTemplate(Base):
    __tablename__ = 'hook_templates'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    hook_text: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(30), index=True)  # business, marketing, ai, etc.
    platform: Mapped[str] = mapped_column(String(20), index=True)  # linkedin, instagram, twitter, youtube
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    use_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int | None] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
