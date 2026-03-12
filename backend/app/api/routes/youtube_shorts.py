import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.user import User
from app.models.youtube_short import YoutubeShort
from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog

router = APIRouter()
_llm = LLMClient()
_prompts = get_prompt_catalog()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class YoutubeShortRequest(BaseModel):
    topic: str
    target_audience: str | None = None
    duration: int = 60  # seconds: 60 or 90


class ScriptSection(BaseModel):
    intro: str
    main_points: list[dict]
    cta: str


class YoutubeShortResponse(BaseModel):
    id: int
    topic: str
    target_audience: str | None
    duration: int
    hook: str
    script: dict
    titles: list[str]
    description: str
    tags: list[str]
    created_at: datetime


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/generate', response_model=YoutubeShortResponse)
async def generate_youtube_short(
    payload: YoutubeShortRequest,
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> YoutubeShortResponse:
    """Generate a complete YouTube Shorts package (hook, script, titles, tags, description)."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='youtube_shorts/v1/prompts.yaml',
            key='generate_youtube_short',
            context={
                'topic': payload.topic,
                'target_audience': payload.target_audience or 'general audience',
                'duration': payload.duration,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)
    parsed = _parse_short(raw, payload.topic)

    record = YoutubeShort(
        topic=payload.topic,
        target_audience=payload.target_audience,
        duration=payload.duration,
        hook=parsed['hook'],
        script=parsed['script'],
        titles=parsed['titles'],
        description=parsed['description'],
        tags=parsed['tags'],
        created_by=current_user.id,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)

    return _to_response(record)


@router.get('/history', response_model=list[YoutubeShortResponse])
async def get_youtube_shorts_history(
    current_user: User = Depends(get_current_reviewer),
    db: AsyncSession = Depends(get_db),
) -> list[YoutubeShortResponse]:
    """Return past YouTube Shorts for the current user, newest first."""
    result = await db.execute(
        select(YoutubeShort)
        .where(YoutubeShort.created_by == current_user.id)
        .order_by(YoutubeShort.created_at.desc())
        .limit(50)
    )
    return [_to_response(r) for r in result.scalars().all()]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _to_response(record: YoutubeShort) -> YoutubeShortResponse:
    return YoutubeShortResponse(
        id=record.id,
        topic=record.topic,
        target_audience=record.target_audience,
        duration=record.duration,
        hook=record.hook,
        script=record.script,
        titles=record.titles,
        description=record.description,
        tags=record.tags,
        created_at=record.created_at,
    )


def _parse_short(raw: str, topic: str) -> dict:
    """Parse LLM JSON output into structured YouTube Short data."""
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0].strip()

    try:
        data = json.loads(cleaned)
        return {
            'hook': data.get('hook', ''),
            'script': data.get('script', {'intro': '', 'main_points': [], 'cta': ''}),
            'titles': data.get('titles', [topic]),
            'description': data.get('description', ''),
            'tags': data.get('tags', []),
        }
    except (json.JSONDecodeError, TypeError, ValueError):
        return {
            'hook': raw[:200],
            'script': {'intro': raw, 'main_points': [], 'cta': 'Follow for more!'},
            'titles': [topic],
            'description': raw,
            'tags': [],
        }
