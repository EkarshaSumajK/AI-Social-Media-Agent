from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

from app.core.config import get_settings
from app.services.llm_service import LLMClient
from app.services.prompt_service import PromptCatalog, get_prompt_catalog

settings = get_settings()

ALLOWED_RELEVANCE = {'high', 'medium', 'low'}
ALLOWED_AGE_GROUP = {'child', 'teen', 'adult', 'unknown'}
ALLOWED_TOPIC_TYPE = {'clinical', 'parenting', 'school', 'general', 'unrelated'}
RELEVANCE_SCORE_MAP = {'high': 92, 'medium': 63, 'low': 24}


@dataclass
class ScreeningDecision:
    allowed: bool
    relevance: str
    relevance_score: int
    age_group: str
    topic_type: str
    mental_health_specific: bool
    reason: str
    trust_score: int
    rejection_reason: str | None = None


class ContentScreeningService:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_catalog: PromptCatalog | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_catalog or get_prompt_catalog()
        self.trusted_sources = _load_trusted_sources()

    async def screen(
        self,
        *,
        title: str,
        summary: str | None,
        source_name: str | None,
        source_url: str,
        use_llm: bool = True,
    ) -> ScreeningDecision:
        classification = await self._classify(
            title=title,
            summary=summary or '',
            source_name=source_name or '',
            source_url=source_url,
            use_llm=use_llm,
        )

        trust_score = self._score_source(source_name=source_name or '', source_url=source_url)
        minimum_trust = int(self.trusted_sources.get('minimum_allowed_score', 40))

        content_allowed = (
            classification['relevance'] == 'high'
            and classification['mental_health_specific'] is True
            and classification['age_group'] in {'child', 'teen'}
        )
        trust_allowed = trust_score >= minimum_trust
        is_allowed = content_allowed and trust_allowed

        trust_band = _trust_band(trust_score)
        reason_suffix = ''
        if trust_band == 'high':
            reason_suffix = ' Source trust is high (>=80) and receives a positive confidence boost.'
        elif trust_band == 'penalty':
            reason_suffix = ' Source trust is moderate-low (40-59); allowed with reduced confidence.'

        rejection_reason: str | None = None
        if not is_allowed:
            if trust_score < minimum_trust:
                rejection_reason = f'Trust score {trust_score} is below threshold {minimum_trust}'
            elif classification['relevance'] != 'high':
                rejection_reason = f'Relevance {classification["relevance"]} is below required high'
            elif classification['mental_health_specific'] is False:
                rejection_reason = 'Topic is not specific to mental health'
            elif classification['age_group'] not in {'child', 'teen'}:
                rejection_reason = f'Age group {classification["age_group"]} is outside child/teen scope'

        return ScreeningDecision(
            allowed=is_allowed,
            relevance=classification['relevance'],
            relevance_score=_adjusted_relevance_score(
                base_score=RELEVANCE_SCORE_MAP[classification['relevance']],
                trust_score=trust_score,
            ),
            age_group=classification['age_group'],
            topic_type=classification['topic_type'],
            mental_health_specific=classification['mental_health_specific'],
            reason=f"{classification['reason']}{reason_suffix}".strip(),
            trust_score=trust_score,
            rejection_reason=rejection_reason,
        )

    async def _classify(
        self,
        *,
        title: str,
        summary: str,
        source_name: str,
        source_url: str,
        use_llm: bool = True,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if use_llm:
            system_prompt, user_prompt = self.prompts.get_prompt(
                bundle='content_screening/v1/prompts.yaml',
                key='relevance_classification',
                context={
                    'title': title,
                    'summary': summary,
                    'source_name': source_name,
                    'source_url': source_url,
                },
            )
            payload = await self.llm.generate_json(
                system_prompt=system_prompt,
                prompt=user_prompt,
                model=settings.llm_screening_model,
                temperature=0.1,
            )
        if payload:
            normalized = {
                'relevance': _normalize_value(payload.get('relevance'), ALLOWED_RELEVANCE, 'low'),
                'age_group': _normalize_value(payload.get('age_group'), ALLOWED_AGE_GROUP, 'unknown'),
                'topic_type': _normalize_value(payload.get('topic_type'), ALLOWED_TOPIC_TYPE, 'general'),
                'mental_health_specific': bool(payload.get('mental_health_specific', False)),
                'reason': str(payload.get('reason', '')).strip()[:240] or 'LLM classification applied.',
            }
            return normalized
        return _heuristic_classification(title=title, summary=summary)

    def _score_source(self, *, source_name: str, source_url: str) -> int:
        normalized_name = source_name.strip().lower()
        host = urlparse(source_url).netloc.lower()

        best_score = int(self.trusted_sources.get('default_score', 40))
        for source in (self.trusted_sources.get('sources') or {}).values():
            if not isinstance(source, dict):
                continue
            score = int(source.get('score', best_score))
            aliases = [str(item).lower() for item in source.get('aliases', [])]
            domains = [str(item).lower() for item in source.get('domains', [])]
            alias_hit = any(alias and alias in normalized_name for alias in aliases)
            domain_hit = any(domain and (host == domain or host.endswith(f'.{domain}')) for domain in domains)
            if alias_hit or domain_hit:
                best_score = max(best_score, score)
        return best_score


def _heuristic_classification(*, title: str, summary: str) -> dict[str, Any]:
    text = f'{title}\n{summary}'.lower()

    mental_terms = {
        'mental health',
        'anxiety',
        'depression',
        'adhd',
        'autism',
        'stress',
        'trauma',
        'therapy',
        'counseling',
        'behaviour',
        'behavior',
        'suicide',
    }
    child_terms = {'child', 'children', 'teen', 'adolescent', 'youth', 'school', 'student', 'parent', 'pediatric'}

    has_mental = any(term in text for term in mental_terms)
    has_child = any(term in text for term in child_terms)

    age_group = 'unknown'
    if any(term in text for term in {'teen', 'adolescent', 'youth', 'student'}):
        age_group = 'teen'
    elif any(term in text for term in {'child', 'children', 'pediatric', 'parent'}):
        age_group = 'child'
    elif any(term in text for term in {'adult', 'workplace', 'employee'}):
        age_group = 'adult'

    topic_type = 'general'
    if any(term in text for term in {'diagnosis', 'symptom', 'treatment', 'clinical', 'disorder'}):
        topic_type = 'clinical'
    elif any(term in text for term in {'parent', 'family', 'caregiver'}):
        topic_type = 'parenting'
    elif any(term in text for term in {'school', 'classroom', 'exam', 'teacher'}):
        topic_type = 'school'
    elif not has_mental:
        topic_type = 'unrelated'

    relevance = 'low'
    if has_mental and has_child:
        relevance = 'high'
    elif has_mental:
        relevance = 'medium'

    return {
        'relevance': relevance,
        'age_group': age_group,
        'topic_type': topic_type,
        'mental_health_specific': has_mental,
        'reason': 'Heuristic fallback classification based on child mental-health signals.',
    }


def _normalize_value(value: Any, allowed: set[str], default: str) -> str:
    normalized = str(value or '').strip().lower()
    if normalized in allowed:
        return normalized
    return default


def _trust_band(trust_score: int) -> str:
    if trust_score >= 80:
        return 'high'
    if trust_score >= 60:
        return 'allowed'
    if trust_score >= 40:
        return 'penalty'
    return 'reject'


def _adjusted_relevance_score(*, base_score: int, trust_score: int) -> int:
    band = _trust_band(trust_score)
    if band == 'high':
        return min(base_score + 5, 100)
    if band == 'penalty':
        return max(base_score - 10, 0)
    return base_score


@lru_cache(maxsize=1)
def _load_trusted_sources() -> dict[str, Any]:
    path = Path(settings.trusted_sources_file)
    if not path.exists():
        return {'default_score': 40, 'minimum_allowed_score': 40, 'sources': {}}
    with path.open('r', encoding='utf-8') as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        return {'default_score': 40, 'minimum_allowed_score': 40, 'sources': {}}
    return payload
