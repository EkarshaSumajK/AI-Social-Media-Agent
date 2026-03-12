from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.security import get_password_hash, verify_password
from app.models.enums import Platform, UserRole
from app.models.user import User

settings = get_settings()


async def ensure_admin_user() -> None:
    async with SessionLocal() as db:
        # Set search_path to ensure we're in the correct schema
        await db.execute(text(f"SET search_path TO {settings.database_schema}, public"))

        result = await db.execute(select(User).where(User.email == settings.admin_email))
        existing = result.scalar_one_or_none()
        if existing:
            return

        db.add(
            User(
                email=settings.admin_email,
                full_name=settings.admin_full_name,
                hashed_password=get_password_hash(settings.admin_password),
                role=UserRole.ADMIN,
                platform=Platform.HORIZON,
                is_active=True,
            )
        )
        await db.commit()


async def get_user_by_email(db, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(db, email: str, password: str) -> User | None:
    user = await get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
