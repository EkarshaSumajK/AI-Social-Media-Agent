from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import Platform, UserRole


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.REVIEWER, index=True)
    platform: Mapped[Platform] = mapped_column(Enum(Platform, values_callable=lambda obj: [e.value for e in obj]), default=Platform.HORIZON, index=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    approved_articles = relationship('Article', foreign_keys='Article.approved_by', back_populates='approver')
    created_articles = relationship('Article', foreign_keys='Article.created_by', back_populates='creator')
