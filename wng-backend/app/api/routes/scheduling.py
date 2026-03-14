import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.scheduled_post import ScheduledPost
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ScheduledPostCreate(BaseModel):
    title: str
    content: str
    platform: str
    content_type: str = 'post'
    scheduled_for: datetime | None = None
    hashtags: list[str] | None = None
    media_urls: list[str] | None = None
    campaign_id: int | None = None


class ScheduledPostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    platform: str | None = None
    content_type: str | None = None
    scheduled_for: datetime | None = None
    status: str | None = None
    hashtags: list[str] | None = None


class ScheduledPostOut(BaseModel):
    id: int
    title: str
    content: str
    platform: str
    content_type: str
    scheduled_for: datetime | None
    status: str
    hashtags: list[str] | None
    media_urls: list[str] | None
    campaign_id: int | None
    social_account_id: int | None
    published_at: datetime | None
    error_message: str | None
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = {'from_attributes': True}


class CalendarStats(BaseModel):
    total: int
    scheduled: int
    draft: int
    published: int
    failed: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('', response_model=ScheduledPostOut)
async def create_scheduled_post(
    payload: ScheduledPostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ScheduledPostOut:
    """Create a new scheduled post."""
    post = ScheduledPost(
        title=payload.title,
        content=payload.content,
        platform=payload.platform,
        content_type=payload.content_type,
        scheduled_for=payload.scheduled_for,
        status='scheduled' if payload.scheduled_for else 'draft',
        hashtags=payload.hashtags,
        media_urls=payload.media_urls,
        campaign_id=payload.campaign_id,
        created_by=current_user.id,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    return ScheduledPostOut.model_validate(post)


@router.get('', response_model=list[ScheduledPostOut])
async def list_scheduled_posts(
    platform: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[ScheduledPostOut]:
    """List scheduled posts for the current user, optionally filtered."""
    query = select(ScheduledPost).where(ScheduledPost.created_by == current_user.id)
    if platform:
        query = query.where(ScheduledPost.platform == platform)
    if status:
        query = query.where(ScheduledPost.status == status)
    query = query.order_by(ScheduledPost.scheduled_for.asc().nulls_last(), ScheduledPost.created_at.desc())
    result = await db.execute(query)
    return [ScheduledPostOut.model_validate(p) for p in result.scalars().all()]


@router.get('/stats', response_model=CalendarStats)
async def get_calendar_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CalendarStats:
    """Get summary counts for the content calendar."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.created_by == current_user.id)
    )
    posts = result.scalars().all()
    return CalendarStats(
        total=len(posts),
        scheduled=sum(1 for p in posts if p.status == 'scheduled'),
        draft=sum(1 for p in posts if p.status == 'draft'),
        published=sum(1 for p in posts if p.status == 'published'),
        failed=sum(1 for p in posts if p.status == 'failed'),
    )


@router.get('/{post_id}', response_model=ScheduledPostOut)
async def get_scheduled_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ScheduledPostOut:
    """Get a single scheduled post."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id, ScheduledPost.created_by == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail='Scheduled post not found')
    return ScheduledPostOut.model_validate(post)


@router.patch('/{post_id}', response_model=ScheduledPostOut)
async def update_scheduled_post(
    post_id: int,
    payload: ScheduledPostUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ScheduledPostOut:
    """Update a scheduled post."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id, ScheduledPost.created_by == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail='Scheduled post not found')

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return ScheduledPostOut.model_validate(post)


@router.delete('/{post_id}', status_code=204)
async def delete_scheduled_post(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> None:
    """Delete a scheduled post."""
    result = await db.execute(
        select(ScheduledPost).where(ScheduledPost.id == post_id, ScheduledPost.created_by == current_user.id)
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail='Scheduled post not found')
    await db.delete(post)
    await db.commit()
