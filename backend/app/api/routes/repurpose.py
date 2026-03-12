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

ALLOWED_SOURCE_TYPES = {'article', 'blog', 'webinar'}
ALLOWED_TARGET_FORMATS = {
    'linkedin_post',
    'thread',
    'reel_script',
    'tweet',
    'blog_summary',
    'quote_card',
    'email_series',
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class RepurposeRequest(BaseModel):
    content: str
    source_type: Literal['article', 'blog', 'webinar']
    target_formats: list[str] = Field(
        ...,
        description='Target output formats, e.g. linkedin_post, thread, reel_script, tweet, blog_summary, quote_card, email_series',
    )


class RepurposeResponse(BaseModel):
    results: dict[str, list[str]]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post('', response_model=RepurposeResponse)
async def repurpose_content(
    payload: RepurposeRequest,
    current_user: User = Depends(get_current_reviewer),
) -> RepurposeResponse:
    """Repurpose source content into multiple target formats using LLM."""
    invalid_formats = set(payload.target_formats) - ALLOWED_TARGET_FORMATS
    if invalid_formats:
        raise HTTPException(
            status_code=400,
            detail=f'Invalid target formats: {", ".join(sorted(invalid_formats))}. '
            f'Allowed: {", ".join(sorted(ALLOWED_TARGET_FORMATS))}',
        )

    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='repurpose/v1/prompts.yaml',
            key='repurpose_content',
            context={
                'content': payload.content,
                'source_type': payload.source_type,
                'target_formats': ', '.join(payload.target_formats),
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    results = _parse_repurpose_results(raw, payload.target_formats)
    return RepurposeResponse(results=results)


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


def _parse_repurpose_results(raw: str, target_formats: list[str]) -> dict[str, list[str]]:
    """Best-effort parse of LLM output into format -> content list mapping."""
    try:
        data = json.loads(_strip_fences(raw))
        if isinstance(data, dict):
            return {fmt: (data[fmt] if isinstance(data.get(fmt), list) else [str(data[fmt])]) for fmt in target_formats if fmt in data}
    except (json.JSONDecodeError, TypeError, ValueError):
        pass

    # Fallback: assign the entire response to all requested formats
    return {fmt: [raw] for fmt in target_formats}
