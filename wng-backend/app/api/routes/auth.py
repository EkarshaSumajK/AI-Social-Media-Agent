from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserOut
from app.services.user_service import authenticate_user

router = APIRouter()
settings = get_settings()


@router.post('/login', response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    user = await authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid credentials')

    access_token = create_access_token(user.email)
    
    # For development, set cookie domain to allow cross-port access
    cookie_kwargs = {
        'key': settings.jwt_cookie_name,
        'value': access_token,
        'max_age': settings.access_token_expire_minutes * 60,
        'httponly': True,
        'secure': bool(settings.jwt_cookie_secure or settings.environment.lower() == 'production'),
        'samesite': settings.jwt_cookie_samesite,
        'path': '/',
    }
    
    # In development, set domain to localhost to work across ports
    if settings.environment.lower() == 'development':
        cookie_kwargs['domain'] = 'localhost'
    
    response.set_cookie(**cookie_kwargs)
    return TokenResponse(access_token=access_token, user=UserOut.model_validate(user))


@router.get('/me', response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(current_user)


@router.post('/logout')
async def logout(response: Response) -> dict[str, str]:
    cookie_kwargs = {
        'key': settings.jwt_cookie_name,
        'path': '/',
        'samesite': settings.jwt_cookie_samesite,
    }
    
    # In development, set domain to localhost to work across ports
    if settings.environment.lower() == 'development':
        cookie_kwargs['domain'] = 'localhost'
    
    response.delete_cookie(**cookie_kwargs)
    return {'message': 'Logged out'}
