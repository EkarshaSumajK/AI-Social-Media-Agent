import hashlib
import json
import logging
import secrets
import urllib.parse
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.config import get_settings
from app.core.database import get_db
from app.models.enums import SocialPlatform
from app.models.social_account import SocialAccount
from app.models.user import User
from app.services.social_service import SocialPublisher

router = APIRouter()
logger = logging.getLogger(__name__)
settings = get_settings()

# ---------------------------------------------------------------------------
# Platform OAuth config
# ---------------------------------------------------------------------------

PLATFORM_OAUTH: dict[str, dict] = {
    'linkedin': {
        'auth_url': 'https://www.linkedin.com/oauth/v2/authorization',
        'token_url': 'https://www.linkedin.com/oauth/v2/accessToken',
        'profile_url': 'https://api.linkedin.com/v2/userinfo',
        'scopes': 'openid profile email w_member_social',
        'client_id_setting': 'linkedin_client_id',
        'client_secret_setting': 'linkedin_client_secret',
    },
    'twitter': {
        'auth_url': 'https://twitter.com/i/oauth2/authorize',
        'token_url': 'https://api.twitter.com/2/oauth2/token',
        'profile_url': 'https://api.twitter.com/2/users/me',
        'scopes': 'tweet.read tweet.write users.read offline.access',
        'client_id_setting': 'twitter_client_id',
        'client_secret_setting': 'twitter_client_secret',
        'pkce': True,
    },
    'instagram': {
        'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'profile_url': 'https://graph.facebook.com/me?fields=id,name,picture',
        'scopes': 'instagram_basic instagram_content_publish pages_read_engagement',
        'client_id_setting': 'facebook_app_id',
        'client_secret_setting': 'facebook_app_secret',
    },
    'facebook': {
        'auth_url': 'https://www.facebook.com/v18.0/dialog/oauth',
        'token_url': 'https://graph.facebook.com/v18.0/oauth/access_token',
        'profile_url': 'https://graph.facebook.com/me?fields=id,name,picture',
        'scopes': 'public_profile pages_manage_posts pages_read_engagement',
        'client_id_setting': 'facebook_app_id',
        'client_secret_setting': 'facebook_app_secret',
    },
    'youtube': {
        'auth_url': 'https://accounts.google.com/o/oauth2/v2/auth',
        'token_url': 'https://oauth2.googleapis.com/token',
        'profile_url': 'https://www.googleapis.com/oauth2/v3/userinfo',
        'scopes': 'https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly openid profile email',
        'client_id_setting': 'google_client_id',
        'client_secret_setting': 'google_client_secret',
    },
}

# In-memory state store (production: use Redis with TTL)
_oauth_states: dict[str, dict] = {}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_client_id(platform: str) -> str | None:
    cfg = PLATFORM_OAUTH.get(platform)
    if not cfg:
        return None
    return getattr(settings, cfg['client_id_setting'], None)


def _get_client_secret(platform: str) -> str | None:
    cfg = PLATFORM_OAUTH.get(platform)
    if not cfg:
        return None
    return getattr(settings, cfg['client_secret_setting'], None)


def _redirect_uri(platform: str) -> str:
    return f'{settings.frontend_url.rstrip("/")}/api/v1/social-accounts/oauth/{platform}/callback'


def _popup_html(success: bool, platform: str, message: str = '') -> str:
    """Return a tiny HTML page that posts a message to the opener and closes."""
    payload = json.dumps({'success': success, 'platform': platform, 'message': message})
    return f"""<!DOCTYPE html>
<html>
<head><title>Connecting {platform}…</title>
<style>
  body {{ margin:0; display:flex; align-items:center; justify-content:center;
         min-height:100vh; background:#06080d; font-family:system-ui,sans-serif; color:#e2e8f0; }}
  .box {{ text-align:center; padding:2rem; }}
  .icon {{ font-size:3rem; margin-bottom:1rem; }}
  p {{ color:#94a3b8; font-size:.9rem; }}
</style>
</head>
<body>
<div class="box">
  <div class="icon">{"✅" if success else "❌"}</div>
  <h2>{"Connected!" if success else "Connection failed"}</h2>
  <p>{message or ("Your account has been connected." if success else "Please try again.")}</p>
</div>
<script>
  try {{
    if (window.opener) {{
      window.opener.postMessage({payload}, "*");
    }}
  }} catch(e) {{}}
  setTimeout(() => window.close(), 1200);
</script>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class OAuthStartResponse(BaseModel):
    platform: str
    configured: bool
    auth_url: str | None = None
    setup_url: str | None = None


class SocialAccountCreate(BaseModel):
    platform: str
    account_name: str
    account_id: str | None = None


class SocialAccountOut(BaseModel):
    id: int
    platform: str
    account_name: str
    account_id: str | None
    status: str
    profile_image_url: str | None
    token_expires_at: datetime | None
    created_at: datetime

    model_config = {'from_attributes': True}


# ---------------------------------------------------------------------------
# OAuth endpoints
# ---------------------------------------------------------------------------

@router.get('/oauth/{platform}/start', response_model=OAuthStartResponse)
async def oauth_start(
    platform: str,
    current_user: User = Depends(get_current_reviewer),
) -> OAuthStartResponse:
    """Return the OAuth authorization URL for a platform popup.

    If credentials are not configured, returns configured=False with a docs link.
    """
    if platform not in PLATFORM_OAUTH:
        raise HTTPException(status_code=400, detail=f'Unsupported platform: {platform}')

    client_id = _get_client_id(platform)
    cfg = PLATFORM_OAUTH[platform]

    DOCS_URLS = {
        'linkedin': 'https://developer.linkedin.com/docs/v2/oauth2-client-credentials-flow',
        'twitter': 'https://developer.twitter.com/en/docs/authentication/oauth-2-0',
        'instagram': 'https://developers.facebook.com/docs/instagram-api/getting-started',
        'facebook': 'https://developers.facebook.com/docs/facebook-login/web',
        'youtube': 'https://developers.google.com/youtube/v3/guides/auth/client-side-web-apps',
    }

    if not client_id:
        return OAuthStartResponse(
            platform=platform,
            configured=False,
            setup_url=DOCS_URLS.get(platform),
        )

    # Generate state token tied to user
    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        'user_id': current_user.id,
        'platform': platform,
        'expires': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
    }

    params: dict[str, str] = {
        'client_id': client_id,
        'redirect_uri': _redirect_uri(platform),
        'response_type': 'code',
        'scope': cfg['scopes'],
        'state': state,
    }

    # Twitter needs PKCE
    if cfg.get('pkce'):
        code_verifier = secrets.token_urlsafe(43)
        code_challenge = hashlib.sha256(code_verifier.encode()).digest()
        import base64
        code_challenge_b64 = base64.urlsafe_b64encode(code_challenge).rstrip(b'=').decode()
        _oauth_states[state]['code_verifier'] = code_verifier
        params['code_challenge'] = code_challenge_b64
        params['code_challenge_method'] = 'S256'

    auth_url = cfg['auth_url'] + '?' + urllib.parse.urlencode(params)

    return OAuthStartResponse(platform=platform, configured=True, auth_url=auth_url)


@router.get('/oauth/{platform}/callback', response_class=HTMLResponse)
async def oauth_callback(
    platform: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Handle the OAuth callback from the platform.

    Exchanges the code for tokens, saves the social account, and returns
    a small HTML page that posts success/failure to window.opener and closes.
    """
    params = dict(request.query_params)
    code = params.get('code')
    state = params.get('state')
    error = params.get('error')

    if error:
        return HTMLResponse(_popup_html(False, platform, f'Platform returned: {error}'))

    if not code or not state:
        return HTMLResponse(_popup_html(False, platform, 'Missing code or state parameter.'))

    state_data = _oauth_states.pop(state, None)
    if not state_data:
        return HTMLResponse(_popup_html(False, platform, 'Invalid or expired OAuth state.'))

    # Check expiry
    try:
        expires = datetime.fromisoformat(state_data['expires'])
        if datetime.now(timezone.utc) > expires:
            return HTMLResponse(_popup_html(False, platform, 'OAuth session expired. Please try again.'))
    except (ValueError, KeyError):
        return HTMLResponse(_popup_html(False, platform, 'Invalid session data.'))

    cfg = PLATFORM_OAUTH.get(platform)
    if not cfg:
        return HTMLResponse(_popup_html(False, platform, 'Unsupported platform.'))

    client_id = _get_client_id(platform)
    client_secret = _get_client_secret(platform)
    if not client_id or not client_secret:
        return HTMLResponse(_popup_html(False, platform, 'Platform credentials not configured on server.'))

    # Exchange code for token
    try:
        token_params: dict[str, str] = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': _redirect_uri(platform),
            'client_id': client_id,
            'client_secret': client_secret,
        }
        if state_data.get('code_verifier'):
            token_params['code_verifier'] = state_data['code_verifier']

        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(cfg['token_url'], data=token_params)
            token_resp.raise_for_status()
            token_data = token_resp.json()

        access_token = token_data.get('access_token') or token_data.get('token')
        refresh_token = token_data.get('refresh_token')
        expires_in = token_data.get('expires_in')
        token_expires_at = (
            datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
            if expires_in else None
        )

        # Fetch profile
        profile_headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient(timeout=10) as client:
            profile_resp = await client.get(cfg['profile_url'], headers=profile_headers)
            profile_data = profile_resp.json() if profile_resp.is_success else {}

        account_name = (
            profile_data.get('name')
            or profile_data.get('username')
            or profile_data.get('login')
            or profile_data.get('email')
            or platform.title()
        )
        account_id = str(
            profile_data.get('id')
            or profile_data.get('sub')
            or ''
        ) or None
        profile_image = (
            profile_data.get('picture')
            or (profile_data.get('picture', {}) or {}).get('data', {}).get('url')
            or None
        )

    except httpx.HTTPStatusError as exc:
        logger.error('OAuth token exchange failed for %s: %s', platform, exc)
        return HTMLResponse(_popup_html(False, platform, f'Token exchange failed ({exc.response.status_code}).'))
    except Exception as exc:
        logger.error('OAuth callback error for %s: %s', platform, exc)
        return HTMLResponse(_popup_html(False, platform, 'An error occurred during connection.'))

    # Save to DB — upsert: if same user+platform already exists, update tokens
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.created_by == state_data['user_id'],
            SocialAccount.platform == platform,
            SocialAccount.account_id == account_id,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.account_name = account_name
        existing.access_token = access_token
        existing.refresh_token = refresh_token
        existing.token_expires_at = token_expires_at
        existing.profile_image_url = profile_image
        existing.status = 'connected'
    else:
        db.add(SocialAccount(
            platform=platform,
            account_name=account_name,
            account_id=account_id,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at,
            profile_image_url=profile_image,
            status='connected',
            created_by=state_data['user_id'],
        ))

    await db.commit()
    return HTMLResponse(_popup_html(True, platform, f'Connected as {account_name}'))


# ---------------------------------------------------------------------------
# CRUD endpoints
# ---------------------------------------------------------------------------

@router.get('', response_model=list[SocialAccountOut])
async def list_social_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[SocialAccountOut]:
    result = await db.execute(
        select(SocialAccount)
        .where(SocialAccount.created_by == current_user.id)
        .order_by(SocialAccount.created_at.desc())
    )
    return [SocialAccountOut.model_validate(a) for a in result.scalars().all()]


@router.post('', response_model=SocialAccountOut)
async def add_social_account(
    payload: SocialAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> SocialAccountOut:
    """Manually register an account (fallback when OAuth isn't configured)."""
    account = SocialAccount(
        platform=payload.platform,
        account_name=payload.account_name,
        account_id=payload.account_id,
        status='connected',
        created_by=current_user.id,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return SocialAccountOut.model_validate(account)


class DirectPublishRequest(BaseModel):
    content: str
    platform: str  # twitter | linkedin | instagram | facebook
    image_url: str | None = None


class DirectPublishResponse(BaseModel):
    platform: str
    status: str
    external_id: str | None = None


@router.post('/publish', response_model=DirectPublishResponse)
async def direct_publish(
    payload: DirectPublishRequest,
    current_user: User = Depends(get_current_reviewer),
) -> DirectPublishResponse:
    """Publish arbitrary approved content directly to a social platform.

    Used by modules that do not have per-record DB IDs (Daily Posts,
    Audience Content, Repurpose, Thought Leadership).
    The caller is responsible for showing an approval gate in the UI
    before invoking this endpoint.
    """
    platform_lower = payload.platform.lower()

    if platform_lower == 'youtube':
        raise HTTPException(
            status_code=400,
            detail='YouTube content cannot be published via API. Use YouTube Studio.',
        )

    try:
        social_platform = SocialPlatform(platform_lower)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f'Unsupported platform: {payload.platform}') from exc

    publisher = SocialPublisher()
    try:
        external_id = await publisher._dispatch(
            platform=social_platform,
            caption=payload.content,
            link=None,
            image_url=payload.image_url,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return DirectPublishResponse(platform=payload.platform, status='posted', external_id=external_id)


@router.delete('/{account_id}', status_code=204)
async def disconnect_social_account(
    account_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> None:
    result = await db.execute(
        select(SocialAccount).where(
            SocialAccount.id == account_id,
            SocialAccount.created_by == current_user.id,
        )
    )
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail='Social account not found')
    await db.delete(account)
    await db.commit()
