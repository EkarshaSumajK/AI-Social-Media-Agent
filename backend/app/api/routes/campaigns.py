import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.campaign import Campaign, CampaignPiece
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

class CampaignCreateRequest(BaseModel):
    title: str
    event_date: datetime | None = None
    goal: str | None = None
    audience: str | None = None
    platforms: list[str] | None = None
    platform_entity: str


class CampaignPieceOut(BaseModel):
    id: int
    campaign_id: int
    phase: str
    content_type: str
    platform: str | None = None
    content: str
    scheduled_for: datetime | None = None
    status: str

    model_config = {'from_attributes': True}


class CampaignOut(BaseModel):
    id: int
    title: str
    event_date: datetime | None = None
    goal: str | None = None
    audience_description: str | None = None
    platforms: list[str] | None = None
    platform_entity: str
    status: str
    created_by: int
    created_at: datetime
    pieces: list[CampaignPieceOut] = Field(default_factory=list)

    model_config = {'from_attributes': True}


class CampaignListOut(BaseModel):
    id: int
    title: str
    event_date: datetime | None = None
    goal: str | None = None
    platform_entity: str
    status: str
    created_at: datetime

    model_config = {'from_attributes': True}


class CampaignGenerateResponse(BaseModel):
    campaign_id: int
    pieces_created: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('', response_model=CampaignOut)
async def create_campaign(
    payload: CampaignCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CampaignOut:
    """Create a new campaign."""
    campaign = Campaign(
        title=payload.title,
        event_date=payload.event_date,
        goal=payload.goal,
        audience_description=payload.audience,
        platforms=payload.platforms,
        platform_entity=payload.platform_entity,
        created_by=current_user.id,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign, attribute_names=['pieces'])
    return CampaignOut.model_validate(campaign)


@router.get('', response_model=list[CampaignListOut])
async def list_campaigns(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[CampaignListOut]:
    """List campaigns for the current user."""
    result = await db.execute(
        select(Campaign)
        .where(Campaign.created_by == current_user.id)
        .order_by(Campaign.created_at.desc()),
    )
    campaigns = result.scalars().all()
    return [CampaignListOut.model_validate(c) for c in campaigns]


@router.get('/{campaign_id}', response_model=CampaignOut)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CampaignOut:
    """Get a campaign with its content pieces."""
    result = await db.execute(
        select(Campaign)
        .options(selectinload(Campaign.pieces))
        .where(Campaign.id == campaign_id, Campaign.created_by == current_user.id),
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail='Campaign not found')
    return CampaignOut.model_validate(campaign)


@router.post('/{campaign_id}/generate', response_model=CampaignGenerateResponse)
async def generate_campaign_content(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CampaignGenerateResponse:
    """Generate pre/during/post event content pieces for a campaign using LLM."""
    result = await db.execute(
        select(Campaign).where(Campaign.id == campaign_id, Campaign.created_by == current_user.id),
    )
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail='Campaign not found')

    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='campaign_builder/v1/prompts.yaml',
            key='generate_campaign_content',
            context={
                'title': campaign.title,
                'goal': campaign.goal or 'brand awareness',
                'audience': campaign.audience_description or 'general audience',
                'platforms': ', '.join(campaign.platforms) if campaign.platforms else 'all',
                'event_date': str(campaign.event_date) if campaign.event_date else 'not specified',
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    pieces = _parse_campaign_pieces(raw, campaign_id)
    for piece in pieces:
        db.add(piece)
    await db.commit()

    return CampaignGenerateResponse(campaign_id=campaign_id, pieces_created=len(pieces))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_fences(raw: str) -> str:
    """Strip markdown code fences from LLM output."""
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0].strip()
    return cleaned


def _parse_campaign_pieces(raw: str, campaign_id: int) -> list[CampaignPiece]:
    """Parse LLM output into CampaignPiece model instances."""
    pieces: list[CampaignPiece] = []
    try:
        data = json.loads(_strip_fences(raw))
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            for phase_key in ('pre', 'during', 'post'):
                phase_items = data.get(phase_key, [])
                if isinstance(phase_items, list):
                    for item in phase_items:
                        if isinstance(item, dict):
                            item.setdefault('phase', phase_key)
                            items.append(item)
                elif isinstance(phase_items, dict):
                    phase_items.setdefault('phase', phase_key)
                    items.append(phase_items)

        for item in items:
            if not isinstance(item, dict):
                continue
            pieces.append(
                CampaignPiece(
                    campaign_id=campaign_id,
                    phase=item.get('phase', 'pre'),
                    content_type=item.get('content_type', 'social'),
                    platform=item.get('platform'),
                    content=item.get('content', ''),
                ),
            )
    except (json.JSONDecodeError, TypeError, ValueError):
        # Fallback: wrap the raw output as a single pre-event piece
        pieces.append(
            CampaignPiece(
                campaign_id=campaign_id,
                phase='pre',
                content_type='social',
                content=raw,
            ),
        )

    return pieces
