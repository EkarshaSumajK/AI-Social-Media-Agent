import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.swipe_file import SwipeFile
from app.models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class SwipeFileCreateRequest(BaseModel):
    platform: str
    title: str
    content: str
    source_url: str | None = None
    performance_notes: str | None = None
    tags: list[str] | None = None


class SwipeFileOut(BaseModel):
    id: int
    created_by: int
    platform: str
    title: str
    content: str
    source_url: str | None = None
    performance_notes: str | None = None
    tags: list[str] | None = None
    created_at: datetime

    model_config = {'from_attributes': True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get('', response_model=list[SwipeFileOut])
async def list_swipe_files(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[SwipeFileOut]:
    """List the current user's saved swipe files."""
    result = await db.execute(
        select(SwipeFile)
        .where(SwipeFile.created_by == current_user.id)
        .order_by(SwipeFile.created_at.desc()),
    )
    swipe_files = result.scalars().all()
    return [SwipeFileOut.model_validate(sf) for sf in swipe_files]


@router.post('', response_model=SwipeFileOut)
async def save_swipe_file(
    payload: SwipeFileCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> SwipeFileOut:
    """Save a post to the user's swipe file."""
    swipe = SwipeFile(
        created_by=current_user.id,
        platform=payload.platform,
        title=payload.title,
        content=payload.content,
        source_url=payload.source_url,
        performance_notes=payload.performance_notes,
        tags=payload.tags,
    )
    db.add(swipe)
    await db.commit()
    await db.refresh(swipe)
    return SwipeFileOut.model_validate(swipe)


@router.delete('/{swipe_id}', status_code=204)
async def delete_swipe_file(
    swipe_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> None:
    """Remove a post from the user's swipe file."""
    result = await db.execute(
        select(SwipeFile).where(
            SwipeFile.id == swipe_id,
            SwipeFile.created_by == current_user.id,
        ),
    )
    swipe = result.scalar_one_or_none()
    if not swipe:
        raise HTTPException(status_code=404, detail='Swipe file entry not found')

    await db.delete(swipe)
    await db.commit()
