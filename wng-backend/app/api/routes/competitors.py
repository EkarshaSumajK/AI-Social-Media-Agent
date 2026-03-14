import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.competitor import Competitor
from app.models.competitor_analysis import CompetitorAnalysis
from app.models.user import User
from app.services.llm_service import LLMClient
from app.services.prompt_service import get_prompt_catalog
from app.services.scraper_service import scrape_url

router = APIRouter()
_llm = LLMClient()
_prompts = get_prompt_catalog()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CompetitorCreateRequest(BaseModel):
    name: str
    platform: str
    profile_url: str
    platform_entity: str


class CompetitorOut(BaseModel):
    id: int
    name: str
    platform: str
    profile_url: str
    platform_entity: str
    created_by: int

    model_config = {'from_attributes': True}


class CompetitorAnalysisResponse(BaseModel):
    id: int
    competitor_id: int
    name: str
    analysis: str
    created_at: str

    model_config = {'from_attributes': True}


class CompetitorAnalysisStored(BaseModel):
    id: int
    competitor_id: int
    analysis: str
    created_at: str

    model_config = {'from_attributes': True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('', response_model=CompetitorOut)
async def add_competitor(
    payload: CompetitorCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CompetitorOut:
    """Add a competitor to track."""
    competitor = Competitor(
        name=payload.name,
        platform=payload.platform,
        profile_url=payload.profile_url,
        platform_entity=payload.platform_entity,
        created_by=current_user.id,
    )
    db.add(competitor)
    await db.commit()
    await db.refresh(competitor)
    return CompetitorOut.model_validate(competitor)


@router.get('', response_model=list[CompetitorOut])
async def list_competitors(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[CompetitorOut]:
    """List competitors tracked by the current user."""
    result = await db.execute(
        select(Competitor)
        .where(Competitor.created_by == current_user.id)
        .order_by(Competitor.created_at.desc()),
    )
    competitors = result.scalars().all()
    return [CompetitorOut.model_validate(c) for c in competitors]


@router.get('/{competitor_id}/analyses', response_model=list[CompetitorAnalysisStored])
async def list_competitor_analyses(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[CompetitorAnalysisStored]:
    """List stored analyses for a competitor."""
    result = await db.execute(
        select(Competitor).where(
            Competitor.id == competitor_id,
            Competitor.created_by == current_user.id,
        ),
    )
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail='Competitor not found')

    analyses_result = await db.execute(
        select(CompetitorAnalysis)
        .where(CompetitorAnalysis.competitor_id == competitor_id)
        .order_by(CompetitorAnalysis.created_at.desc())
        .limit(1),
    )
    analysis = analyses_result.scalar_one_or_none()
    if not analysis:
        return []
    return [
        CompetitorAnalysisStored(
            id=analysis.id,
            competitor_id=analysis.competitor_id,
            analysis=analysis.analysis,
            created_at=analysis.created_at.isoformat() if analysis.created_at else '',
        )
    ]


@router.post('/{competitor_id}/analyze', response_model=CompetitorAnalysisResponse)
async def analyze_competitor(
    competitor_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CompetitorAnalysisResponse:
    """Run an LLM-powered analysis on a tracked competitor."""
    result = await db.execute(
        select(Competitor).where(
            Competitor.id == competitor_id,
            Competitor.created_by == current_user.id,
        ),
    )
    competitor = result.scalar_one_or_none()
    if not competitor:
        raise HTTPException(status_code=404, detail='Competitor not found')

    profile_content: str | None = None
    if competitor.profile_url:
        profile_content = await scrape_url(competitor.profile_url, wait_for_ms=8000)

    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='competitor_analysis/v1/prompts.yaml',
            key='analyze_competitor',
            context={
                'name': competitor.name,
                'platform': competitor.platform,
                'profile_url': competitor.profile_url,
                'platform_entity': competitor.platform_entity,
                'profile_content': profile_content or '',
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    analysis_dict = await _llm.generate_json(prompt=user_prompt, system_prompt=system_prompt)
    analysis_str = json.dumps(analysis_dict)

    existing = await db.execute(
        select(CompetitorAnalysis)
        .where(CompetitorAnalysis.competitor_id == competitor.id)
        .order_by(CompetitorAnalysis.created_at.desc())
        .limit(1),
    )
    record = existing.scalar_one_or_none()
    if record:
        record.analysis = analysis_str
        record.created_at = datetime.now(timezone.utc)
    else:
        record = CompetitorAnalysis(competitor_id=competitor.id, analysis=analysis_str)
        db.add(record)
    await db.commit()
    await db.refresh(record)

    return CompetitorAnalysisResponse(
        id=record.id,
        competitor_id=competitor.id,
        name=competitor.name,
        analysis=record.analysis,
        created_at=record.created_at.isoformat() if record.created_at else '',
    )
