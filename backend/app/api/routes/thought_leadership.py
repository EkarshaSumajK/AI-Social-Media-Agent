import logging
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.thought_leadership import ThoughtLeadershipGeneration
from app.models.user import User
from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog

router = APIRouter()
_llm = LLMClient()
_prompts = get_prompt_catalog()
logger = logging.getLogger(__name__)

CONTENT_TYPES = {
    'deep_insight',
    'predictions',
    'contrarian',
    'framework',
    'case_study',
    'authority_thread',
    'hard_truths',
    'founder_journey',
    'myth_busting',
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class ThoughtLeadershipRequest(BaseModel):
    topic: str
    content_type: Literal[
        'deep_insight',
        'predictions',
        'contrarian',
        'framework',
        'case_study',
        'authority_thread',
        'hard_truths',
        'founder_journey',
        'myth_busting',
    ]
    industry: str


class ThoughtLeadershipResponse(BaseModel):
    id: int
    content_type: str
    topic: str
    industry: str
    content: str
    created_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/generate', response_model=ThoughtLeadershipResponse)
async def generate_thought_leadership(
    payload: ThoughtLeadershipRequest,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> ThoughtLeadershipResponse:
    """Generate thought-leadership content and persist it for the current user."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='thought_leadership/v1/prompts.yaml',
            key=payload.content_type,
            context={
                'topic': payload.topic,
                'industry': payload.industry,
                'content_type': payload.content_type,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    record = ThoughtLeadershipGeneration(
        topic=payload.topic,
        industry=payload.industry,
        content_type=payload.content_type,
        content=raw,
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return ThoughtLeadershipResponse(
        id=record.id,
        content_type=record.content_type,
        topic=record.topic,
        industry=record.industry,
        content=record.content,
        created_at=record.created_at,
    )


@router.get('/history', response_model=list[ThoughtLeadershipResponse])
async def get_thought_leadership_history(
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> list[ThoughtLeadershipResponse]:
    """Return past thought leadership generations for the current user, newest first."""
    result = await db.execute(
        select(ThoughtLeadershipGeneration)
        .where(ThoughtLeadershipGeneration.created_by == current_user.id)
        .order_by(ThoughtLeadershipGeneration.created_at.desc())
        .limit(50)
    )
    records = result.scalars().all()
    return [
        ThoughtLeadershipResponse(
            id=r.id,
            content_type=r.content_type,
            topic=r.topic,
            industry=r.industry,
            content=r.content,
            created_at=r.created_at,
        )
        for r in records
    ]
