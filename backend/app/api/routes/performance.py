import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

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

class PerformanceMetric(BaseModel):
    metric: str
    value: float | int | str
    change_pct: float | None = None


class PerformanceResponse(BaseModel):
    platform: str | None
    days: int
    metrics: list[PerformanceMetric]


class PerformanceInsightsResponse(BaseModel):
    insights: str
    recommendations: list[str] = []


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get('', response_model=PerformanceResponse)
async def get_performance(
    platform: str | None = Query(default=None),
    days: int = Query(default=30, le=365),
    current_user: User = Depends(get_current_reviewer),
) -> PerformanceResponse:
    """Get performance data for the specified platform and time window.

    Note: In a production deployment this would query an analytics store or
    third-party API.  The current implementation returns placeholder data so
    the route contract is established.
    """
    metrics = _get_placeholder_metrics(platform, days)
    return PerformanceResponse(platform=platform, days=days, metrics=metrics)


@router.get('/insights', response_model=PerformanceInsightsResponse)
async def get_performance_insights(
    platform: str | None = Query(default=None),
    days: int = Query(default=30, le=365),
    current_user: User = Depends(get_current_reviewer),
) -> PerformanceInsightsResponse:
    """Generate AI-powered performance insights."""
    metrics_summary = _build_metrics_summary(platform, days)

    try:
        system_prompt, user_prompt = _prompts.get_prompt(
            bundle='daily_posts/v1/prompts.yaml',
            key='performance_insights',
            context={
                'platform': platform or 'all platforms',
                'days': str(days),
                'metrics_summary': metrics_summary,
            },
        )
    except (KeyError, FileNotFoundError) as exc:
        raise HTTPException(status_code=500, detail=f'Prompt configuration error: {exc}') from exc

    raw = await _llm.generate(prompt=user_prompt, system_prompt=system_prompt)

    return PerformanceInsightsResponse(
        insights=raw,
        recommendations=_extract_recommendations(raw),
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_placeholder_metrics(platform: str | None, days: int) -> list[PerformanceMetric]:
    """Return placeholder metrics until analytics integration is wired up."""
    return [
        PerformanceMetric(metric='impressions', value=0, change_pct=0.0),
        PerformanceMetric(metric='engagement_rate', value='0%', change_pct=0.0),
        PerformanceMetric(metric='followers', value=0, change_pct=0.0),
        PerformanceMetric(metric='posts_published', value=0, change_pct=0.0),
    ]


def _build_metrics_summary(platform: str | None, days: int) -> str:
    """Build a human-readable metrics summary for the LLM prompt."""
    return (
        f'Platform: {platform or "all platforms"}. '
        f'Time window: {days} days. '
        'Metrics data is not yet available (analytics integration pending). '
        'Provide actionable insights and recommendations based on best practices '
        'for social media content strategy, engagement, and growth.'
    )


def _extract_recommendations(raw: str) -> list[str]:
    """Extract recommendations from ## Recommendations section only. Must contain action keywords."""
    lines = raw.split('\n')
    recommendations = []
    in_recommendations = False
    rec_keywords = ('recommend', 'suggest', 'should', 'try', 'consider', 'focus', 'prioritise', 'prioritize')

    for line in lines:
        line_lower = line.lower()
        if 'recommendation' in line_lower and '##' in line_lower:
            in_recommendations = True
            continue
        if in_recommendations and line.strip().startswith('##'):
            break
        if not in_recommendations:
            continue
        stripped = line.strip().lstrip('0123456789.-•*) ')
        if not stripped or len(stripped) < 15:
            continue
        if any(kw in line_lower for kw in rec_keywords):
            recommendations.append(stripped)
    return recommendations[:10]
