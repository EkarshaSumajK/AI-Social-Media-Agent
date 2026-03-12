import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.regional_content import RegionalContent
from app.models.user import User
from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog

router = APIRouter()
logger = logging.getLogger(__name__)
_llm = LLMClient()
_prompts = get_prompt_catalog()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class LocaliseRequest(BaseModel):
    content: str
    region: str
    language_style: str = 'english'


class TrendingTopicsRequest(BaseModel):
    region: str
    industry: str
    time_frame: str = 'this week'


class HashtagRequest(BaseModel):
    region: str
    topic: str
    platform: str = 'linkedin'


class RegionalTrendingTopic(BaseModel):
    topic: str
    relevance_reason: str
    content_angle: str
    urgency: str


class RegionalHashtags(BaseModel):
    primary: list[str]
    secondary: list[str]
    trending: list[str]


class LocaliseResponse(BaseModel):
    id: int
    region: str
    language_style: str
    original_content: str
    localised_content: str
    created_at: datetime

    model_config = {'from_attributes': True}


class TrendingTopicsResponse(BaseModel):
    id: int
    region: str
    industry: str
    trending_topics: list[RegionalTrendingTopic]
    created_at: datetime


class HashtagResponse(BaseModel):
    id: int
    region: str
    platform: str
    hashtags: RegionalHashtags
    created_at: datetime


class RegionalHistoryOut(BaseModel):
    id: int
    region: str
    industry: str
    language_style: str
    request_type: str
    original_content: str | None
    localised_content: str | None
    created_at: datetime

    model_config = {'from_attributes': True}


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


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/localise', response_model=LocaliseResponse)
async def localise_content(
    payload: LocaliseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> LocaliseResponse:
    """Localise existing content for a specific region and language style."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='regional/v1/prompts.yaml',
            key='localise_content',
            context={
                'region': payload.region,
                'language_style': payload.language_style,
                'content': payload.content,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    record = RegionalContent(
        region=payload.region,
        industry='general',
        language_style=payload.language_style,
        original_content=payload.content,
        localised_content=raw.strip(),
        request_type='localise',
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return LocaliseResponse(
        id=record.id,
        region=record.region,
        language_style=record.language_style,
        original_content=record.original_content or '',
        localised_content=record.localised_content or '',
        created_at=record.created_at,
    )


@router.post('/trending-topics', response_model=TrendingTopicsResponse)
async def get_regional_trending_topics(
    payload: TrendingTopicsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> TrendingTopicsResponse:
    """Get trending content topics for a specific region and industry."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='regional/v1/prompts.yaml',
            key='regional_trending_topics',
            context={
                'region': payload.region,
                'industry': payload.industry,
                'time_frame': payload.time_frame,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)
    parsed_topics: list[dict] = []
    try:
        parsed_topics = json.loads(_strip_fences(raw))
        if not isinstance(parsed_topics, list):
            parsed_topics = []
    except (json.JSONDecodeError, TypeError, ValueError):
        parsed_topics = [{'topic': raw[:100], 'relevance_reason': '', 'content_angle': '', 'urgency': 'medium'}]

    record = RegionalContent(
        region=payload.region,
        industry=payload.industry,
        language_style='english',
        trending_topics=parsed_topics,
        request_type='trending_topics',
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return TrendingTopicsResponse(
        id=record.id,
        region=record.region,
        industry=record.industry,
        trending_topics=[RegionalTrendingTopic(**t) for t in parsed_topics],
        created_at=record.created_at,
    )


@router.post('/hashtags', response_model=HashtagResponse)
async def get_regional_hashtags(
    payload: HashtagRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> HashtagResponse:
    """Get region-specific hashtag strategy for a topic."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='regional/v1/prompts.yaml',
            key='regional_hashtags',
            context={
                'region': payload.region,
                'topic': payload.topic,
                'platform': payload.platform,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)
    parsed_hashtags: dict = {'primary': [], 'secondary': [], 'trending': []}
    try:
        data = json.loads(_strip_fences(raw))
        if isinstance(data, dict):
            parsed_hashtags = data
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    record = RegionalContent(
        region=payload.region,
        industry='general',
        language_style='english',
        platform=payload.platform,
        hashtags=parsed_hashtags,
        request_type='hashtags',
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return HashtagResponse(
        id=record.id,
        region=record.region,
        platform=payload.platform,
        hashtags=RegionalHashtags(**parsed_hashtags),
        created_at=record.created_at,
    )


@router.get('/history', response_model=list[RegionalHistoryOut])
async def get_regional_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[RegionalHistoryOut]:
    """Get history of regional content generations."""
    result = await db.execute(
        select(RegionalContent)
        .where(RegionalContent.created_by == current_user.id)
        .order_by(RegionalContent.created_at.desc())
        .limit(50)
    )
    return [RegionalHistoryOut.model_validate(r) for r in result.scalars().all()]
