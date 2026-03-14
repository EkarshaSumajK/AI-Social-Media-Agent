from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

security = HTTPBearer(auto_error=False)
settings = get_settings()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    bearer_token = credentials.credentials if credentials else None
    cookie_token = request.cookies.get(settings.jwt_cookie_name)
    token = bearer_token or cookie_token

    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Authentication required')

    email = decode_access_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid token')

    result = await db.execute(select(User).where(User.email == email, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


async def get_current_reviewer(user: User = Depends(get_current_user)) -> User:
    # Accept admin roles (both cases) and reviewer
    admin_roles = {'admin', 'ADMIN'}
    if user.role not in {'reviewer', 'REVIEWER'} | admin_roles:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Reviewer role required')
    return user
