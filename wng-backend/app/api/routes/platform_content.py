import json
import logging
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.platform_content import PlatformContentGeneration
from app.models.user import User
from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog
from app.services.social_service import SocialPublisher

router = APIRouter()
_llm = LLMClient()
_prompts = get_prompt_catalog()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class PlatformContentRequest(BaseModel):
    topic: str
    platform: Literal['linkedin', 'instagram', 'twitter', 'youtube']
    content_type: str  # authority_post, thread, reel_script, video_outline, etc.


class PlatformContentResponse(BaseModel):
    id: int
    topic: str
    platform: str
    content_type: str
    content: str
    metadata: dict[str, Any] = {}
    created_at: datetime


class PublishPlatformContentRequest(BaseModel):
    image_url: str | None = None


class PublishPlatformContentResponse(BaseModel):
    id: int
    platform: str
    status: str
    external_id: str | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/generate', response_model=PlatformContentResponse)
async def generate_platform_content(
    payload: PlatformContentRequest,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> PlatformContentResponse:
    """Generate content optimised for a specific platform and persist it."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='platform_specific/v1/prompts.yaml',
            key='generate_platform_content',
            context={
                'topic': payload.topic,
                'platform': payload.platform,
                'content_type': payload.content_type,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    content, meta = _parse_platform_response(raw, payload.platform, payload.content_type)

    record = PlatformContentGeneration(
        topic=payload.topic,
        platform=payload.platform,
        content_type=payload.content_type,
        content=content,
        gen_metadata=meta,
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return PlatformContentResponse(
        id=record.id,
        topic=record.topic,
        platform=record.platform,
        content_type=record.content_type,
        content=record.content,
        metadata=record.gen_metadata or {},
        created_at=record.created_at,
    )


@router.get('/history', response_model=list[PlatformContentResponse])
async def get_platform_content_history(
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> list[PlatformContentResponse]:
    """Return past platform content generations for the current user, newest first."""
    result = await db.execute(
        select(PlatformContentGeneration)
        .where(PlatformContentGeneration.created_by == current_user.id)
        .order_by(PlatformContentGeneration.created_at.desc())
        .limit(50)
    )
    records = result.scalars().all()
    return [
        PlatformContentResponse(
            id=r.id,
            topic=r.topic,
            platform=r.platform,
            content_type=r.content_type,
            content=r.content,
            metadata=r.gen_metadata or {},
            created_at=r.created_at,
        )
        for r in records
    ]


@router.post('/{content_id}/publish', response_model=PublishPlatformContentResponse)
async def publish_platform_content(
    content_id: int,
    payload: PublishPlatformContentRequest | None = None,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> PublishPlatformContentResponse:
    """Publish a generated platform content item directly to its social platform."""
    result = await db.execute(
        select(PlatformContentGeneration).where(
            PlatformContentGeneration.id == content_id,
            PlatformContentGeneration.created_by == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail='Content not found')

    platform_lower = record.platform.lower()

    if platform_lower == 'youtube':
        raise HTTPException(
            status_code=400,
            detail='YouTube scripts/outlines cannot be published via API. Use YouTube Studio to upload.',
        )

    try:
        social_platform = platform_lower
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f'Unsupported platform: {record.platform}') from exc

    publisher = SocialPublisher()
    try:
        external_id = await publisher._dispatch(
            platform=social_platform,
            caption=record.content,
            link=None,
            image_url=payload.image_url if payload else None,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return PublishPlatformContentResponse(
        id=content_id,
        platform=record.platform,
        status='posted',
        external_id=external_id,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_fences(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0].strip()
    return cleaned


def _parse_platform_response(raw: str, platform: str, content_type: str) -> tuple[str, dict[str, Any]]:
    """Extract content and optional metadata from LLM output."""
    try:
        data = json.loads(_strip_fences(raw))
        if isinstance(data, dict):
            return (
                data.get('content', raw),
                {k: v for k, v in data.items() if k != 'content'},
            )
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    return raw, {'platform': platform, 'content_type': content_type}
