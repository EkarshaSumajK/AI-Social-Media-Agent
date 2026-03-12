import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.hook_template import HookTemplate
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

class HookTemplateOut(BaseModel):
    id: int
    hook_text: str
    category: str
    platform: str
    industry: str | None = None
    use_count: int
    created_by: int | None = None

    model_config = {'from_attributes': True}


class HookCreateRequest(BaseModel):
    hook_text: str
    category: str
    platform: str
    industry: str | None = None


class HookSuggestRequest(BaseModel):
    topic: str
    platform: str | None = None
    count: int = 5


class HookSuggestion(BaseModel):
    hook_text: str
    reasoning: str | None = None


class HookSuggestResponse(BaseModel):
    suggestions: list[HookSuggestion]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get('', response_model=list[HookTemplateOut])
async def list_hooks(
    category: str | None = None,
    platform: str | None = None,
    industry: str | None = None,
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[HookTemplateOut]:
    """List hook templates with optional filtering. Shows global hooks plus user's own."""
    stmt = select(HookTemplate).where(
        or_(HookTemplate.created_by.is_(None), HookTemplate.created_by == current_user.id)
    )
    if category:
        stmt = stmt.where(HookTemplate.category == category)
    if platform:
        stmt = stmt.where(HookTemplate.platform == platform)
    if industry:
        stmt = stmt.where(HookTemplate.industry == industry)
    stmt = stmt.order_by(HookTemplate.use_count.desc()).limit(limit)

    result = await db.execute(stmt)
    hooks = result.scalars().all()
    return [HookTemplateOut.model_validate(h) for h in hooks]


@router.post('', response_model=HookTemplateOut)
async def add_hook(
    payload: HookCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> HookTemplateOut:
    """Add a custom hook template."""
    hook = HookTemplate(
        hook_text=payload.hook_text,
        category=payload.category,
        platform=payload.platform,
        industry=payload.industry,
        created_by=current_user.id,
    )
    db.add(hook)
    await db.commit()
    await db.refresh(hook)
    return HookTemplateOut.model_validate(hook)


@router.get('/suggest', response_model=HookSuggestResponse)
async def suggest_hooks(
    topic: str = Query(...),
    platform: str | None = Query(default=None),
    count: int = Query(default=5, le=20),
    _: User = Depends(get_current_reviewer),
) -> HookSuggestResponse:
    """Suggest hooks for a topic using LLM."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='daily_posts/v1/prompts.yaml',
            key='suggest_hooks',
            context={
                'topic': topic,
                'platform': platform or 'any',
                'count': str(count),
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    suggestions = _parse_hook_suggestions(raw)
    return HookSuggestResponse(suggestions=suggestions[:count])


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


def _parse_hook_suggestions(raw: str) -> list[HookSuggestion]:
    """Best-effort parse of LLM output into hook suggestions."""
    try:
        data = json.loads(_strip_fences(raw))
        if isinstance(data, list):
            return [HookSuggestion(**item) if isinstance(item, dict) else HookSuggestion(hook_text=str(item)) for item in data]
        if isinstance(data, dict) and 'suggestions' in data:
            return [HookSuggestion(**item) for item in data['suggestions']]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Fallback: split by newline and treat each non-empty line as a hook
    lines = [line.strip().lstrip('0123456789.-) ') for line in raw.split('\n') if line.strip()]
    return [HookSuggestion(hook_text=line) for line in lines if line]
