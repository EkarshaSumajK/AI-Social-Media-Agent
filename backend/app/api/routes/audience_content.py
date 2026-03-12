import json
import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.api.deps import get_current_reviewer
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

class AudienceContentRequest(BaseModel):
    audience_type: str
    region: str
    income_bracket: str
    awareness_stage: Literal['cold', 'warm', 'hot']
    pain_points: list[str] = Field(..., min_length=1)


class AudienceContentResponse(BaseModel):
    results: dict[str, str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('/generate', response_model=AudienceContentResponse)
async def generate_audience_content(
    payload: AudienceContentRequest,
    current_user: User = Depends(get_current_reviewer),
) -> AudienceContentResponse:
    """Generate audience-targeted content: problem-aware, solution-aware,
    objection-handling, value, and conversion posts."""
    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='audience_content/v1/prompts.yaml',
            key='generate_audience_content',
            context={
                'audience_type': payload.audience_type,
                'region': payload.region,
                'income_bracket': payload.income_bracket,
                'awareness_stage': payload.awareness_stage,
                'pain_points': ', '.join(payload.pain_points),
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    results = _parse_audience_results(raw)
    return AudienceContentResponse(results=results)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

POST_TYPES = [
    'problem_aware',
    'solution_aware',
    'objection_handling',
    'value',
    'conversion',
]


def _strip_fences(raw: str) -> str:
    cleaned = raw.strip()
    if cleaned.startswith('```'):
        cleaned = cleaned.split('\n', 1)[-1]
        if cleaned.endswith('```'):
            cleaned = cleaned.rsplit('```', 1)[0].strip()
    return cleaned


def _parse_audience_results(raw: str) -> dict[str, str]:
    """Best-effort parse of LLM output into post_type -> content."""
    try:
        data = json.loads(_strip_fences(raw))
        if isinstance(data, dict):
            return {k: str(v) for k, v in data.items() if k in POST_TYPES}
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Fallback: return the entire response under a generic key
    return {'mixed': raw}
