import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.daily_post import DailyPostBatch
from app.models.user import User
from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog

router = APIRouter()
_llm = LLMClient()
_prompts = get_prompt_catalog()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class DailyPostsRequest(BaseModel):
    industry: str
    region: str = 'global'
    target_audience: str
    business_goal: str = 'brand'


class PostSuggestion(BaseModel):
    post_type: str
    content: str
    platform_hint: str | None = None


class DailyPostsResponse(BaseModel):
    suggestions: list[PostSuggestion]


class DailyPostBatchOut(BaseModel):
    id: int
    industry: str
    region: str
    target_audience: str
    business_goal: str
    suggestions: list[PostSuggestion]
    created_at: datetime

    model_config = {'from_attributes': True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/generate', response_model=DailyPostBatchOut)
async def generate_daily_posts(
    payload: DailyPostsRequest,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> DailyPostBatchOut:
    """Generate daily post suggestions and persist them for the current user."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='daily_posts/v1/prompts.yaml',
            key='generate_daily_posts',
            context={
                'industry': payload.industry,
                'region': payload.region,
                'target_audience': payload.target_audience,
                'business_goal': payload.business_goal,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)
    suggestions = _parse_suggestions(raw)

    batch = DailyPostBatch(
        industry=payload.industry,
        region=payload.region,
        target_audience=payload.target_audience,
        business_goal=payload.business_goal,
        suggestions=[s.model_dump() for s in suggestions],
        created_by=current_user.id,
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)

    return DailyPostBatchOut(
        id=batch.id,
        industry=batch.industry,
        region=batch.region,
        target_audience=batch.target_audience,
        business_goal=batch.business_goal,
        suggestions=suggestions,
        created_at=batch.created_at,
    )


@router.get('/history', response_model=list[DailyPostBatchOut])
async def get_daily_posts_history(
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> list[DailyPostBatchOut]:
    """Return past generated daily post batches for the current user, newest first."""
    result = await db.execute(
        select(DailyPostBatch)
        .where(DailyPostBatch.created_by == current_user.id)
        .order_by(DailyPostBatch.created_at.desc())
        .limit(30)
    )
    batches = result.scalars().all()
    return [
        DailyPostBatchOut(
            id=b.id,
            industry=b.industry,
            region=b.region,
            target_audience=b.target_audience,
            business_goal=b.business_goal,
            suggestions=[PostSuggestion(**s) for s in b.suggestions],
            created_at=b.created_at,
        )
        for b in batches
    ]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_suggestions(raw: str) -> list[PostSuggestion]:
    """Best-effort parse of LLM output into structured suggestions."""
    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0].strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, list):
            return [PostSuggestion(**item) for item in data]
        if isinstance(data, dict) and 'suggestions' in data:
            return [PostSuggestion(**item) for item in data['suggestions']]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Fallback: return the whole response as a single suggestion
    return [PostSuggestion(post_type='mixed', content=raw)]
