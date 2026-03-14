from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.config import get_settings
from app.services.llm_service import LLMClient
from app.services.prompt_service import PromptCatalog, get_prompt_catalog

settings = get_settings()

WHO_FACTSHEET_URL = 'https://www.who.int/news-room/fact-sheets/detail/adolescent-mental-health'
UNICEF_MENTAL_HEALTH_URL = 'https://www.unicef.org/mental-health'


@dataclass
class TrendEnrichmentResult:
    is_trending: bool
    regions: list[str]
    public_concerns: list[str]
    statements: list[str]
    sentiment: str
    statistics: list[str]


class TrendEnrichmentService:
    def __init__(
        self,
        llm_client: LLMClient | None = None,
        prompt_catalog: PromptCatalog | None = None,
    ) -> None:
        self.llm = llm_client or LLMClient()
        self.prompts = prompt_catalog or get_prompt_catalog()

    async def enrich(self, *, topic_title: str, topic_summary: str | None) -> TrendEnrichmentResult:
        discussion_snippets = await self._collect_discussion_snippets(topic_title=topic_title, topic_summary=topic_summary or '')
        trend_payload = await self._analyze_discussions(
            topic_title=topic_title,
            topic_summary=topic_summary or '',
            discussion_snippets=discussion_snippets,
        )

        research_snippets = await self._collect_research_snippets(topic_title=topic_title)
        statistics = await self._extract_statistics(topic_title=topic_title, research_snippets=research_snippets)

        return TrendEnrichmentResult(
            is_trending=bool(trend_payload.get('is_trending', False)),
            regions=_normalize_list(trend_payload.get('regions'))[:8],
            public_concerns=_normalize_list(trend_payload.get('public_concerns'))[:8],
            statements=_normalize_list(trend_payload.get('statements'))[:8],
            sentiment=_normalize_sentiment(trend_payload.get('sentiment')),
            statistics=statistics[:8],
        )

    async def _collect_discussion_snippets(self, *, topic_title: str, topic_summary: str) -> list[str]:
        snippets: list[str] = []
        snippets.extend(await self._fetch_x_discussions(topic_title=topic_title))
        if topic_summary.strip():
            snippets.append(topic_summary.strip())
        return [snippet for snippet in snippets if snippet][:25]

    async def _fetch_x_discussions(self, *, topic_title: str) -> list[str]:
        if not settings.x_bearer_token:
            return []

        params = {
            'query': f'"{topic_title}" lang:en -is:retweet',
            'max_results': 20,
            'tweet.fields': 'created_at,lang,text',
        }
        headers = {'Authorization': f'Bearer {settings.x_bearer_token}'}
        url = 'https://api.twitter.com/2/tweets/search/recent'
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params, headers=headers)
                response.raise_for_status()
                payload = response.json()
        except Exception:
            return []

        rows = payload.get('data') or []
        snippets = [str(item.get('text', '')).strip() for item in rows if isinstance(item, dict)]
        return [snippet for snippet in snippets if snippet]

    async def _analyze_discussions(
        self,
        *,
        topic_title: str,
        topic_summary: str,
        discussion_snippets: list[str],
    ) -> dict[str, Any]:
        snippet_block = '\n'.join(f'- {snippet}' for snippet in discussion_snippets[:15]) or '- No discussion snippets available.'
        system_prompt, user_prompt = self.prompts.get_prompt(
            bundle='trend_enrichment/v1/prompts.yaml',
            key='trend_signal_analysis',
            context={
                'topic_title': topic_title,
                'topic_summary': topic_summary,
                'discussion_snippets': snippet_block,
            },
        )
        payload = await self.llm.generate_json(
            system_prompt=system_prompt,
            prompt=user_prompt,
            model=settings.llm_screening_model,
            temperature=0.1,
        )
        if payload:
            return payload
        return _heuristic_trend_payload(topic_title=topic_title, snippets=discussion_snippets, topic_summary=topic_summary)

    async def _collect_research_snippets(self, *, topic_title: str) -> list[str]:
        snippets: list[str] = []
        snippets.extend(await self._fetch_pubmed_snippets(topic_title=topic_title))
        snippets.extend(await self._fetch_reference_page_snippets())
        return snippets[:50]

    async def _fetch_pubmed_snippets(self, *, topic_title: str) -> list[str]:
        search_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi'
        summary_url = 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi'
        term = f'({topic_title}) AND (child OR adolescent) AND mental health'

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                search_resp = await client.get(
                    search_url,
                    params={
                        'db': 'pubmed',
                        'term': term,
                        'retmode': 'json',
                        'retmax': 6,
                        'sort': 'relevance',
                    },
                )
                search_resp.raise_for_status()
                search_payload = search_resp.json()
                ids = ((search_payload.get('esearchresult') or {}).get('idlist') or [])[:6]
                if not ids:
                    return []

                summary_resp = await client.get(
                    summary_url,
                    params={
                        'db': 'pubmed',
                        'id': ','.join(ids),
                        'retmode': 'json',
                    },
                )
                summary_resp.raise_for_status()
                summary_payload = summary_resp.json()
        except Exception:
            return []

        snippets: list[str] = []
        for item_id in ids:
            row = (summary_payload.get('result') or {}).get(item_id) or {}
            title = str(row.get('title', '')).strip()
            if title:
                snippets.append(title)
        return snippets

    async def _fetch_reference_page_snippets(self) -> list[str]:
        urls = [WHO_FACTSHEET_URL, UNICEF_MENTAL_HEALTH_URL]
        snippets: list[str] = []
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                responses = await asyncio_gather_with_limit(client, urls)
        except Exception:
            return []

        for text in responses:
            if not text:
                continue
            cleaned = _clean_text(text)
            if cleaned:
                snippets.extend(_extract_numeric_sentences(cleaned))
        return snippets[:20]

    async def _extract_statistics(self, *, topic_title: str, research_snippets: list[str]) -> list[str]:
        if not research_snippets:
            return []

        snippet_block = '\n'.join(f'- {snippet}' for snippet in research_snippets[:25])
        system_prompt, user_prompt = self.prompts.get_prompt(
            bundle='trend_enrichment/v1/prompts.yaml',
            key='numeric_statistics_extraction',
            context={
                'topic_title': topic_title,
                'research_snippets': snippet_block,
            },
        )
        payload = await self.llm.generate_json(
            system_prompt=system_prompt,
            prompt=user_prompt,
            model=settings.llm_screening_model,
            temperature=0.0,
        )
        extracted = _normalize_list(payload.get('statistics') if payload else None)
        if extracted:
            return extracted
        fallback = _extract_numeric_sentences(' '.join(research_snippets))
        return fallback[:8]


async def asyncio_gather_with_limit(client: httpx.AsyncClient, urls: list[str]) -> list[str]:
    import asyncio

    async def fetch(url: str) -> str:
        try:
            response = await client.get(url)
            response.raise_for_status()
            return response.text[:12000]
        except Exception:
            return ''

    return list(await asyncio.gather(*(fetch(url) for url in urls)))


def _heuristic_trend_payload(*, topic_title: str, snippets: list[str], topic_summary: str) -> dict[str, Any]:
    text = ' '.join(snippets + [topic_summary]).lower()
    regions = _detect_regions(text)

    concerns = []
    concern_map = {
        'school stress': ['exam', 'school', 'grade', 'academic'],
        'screen addiction': ['screen', 'social media', 'phone', 'gaming'],
        'sleep disruption': ['sleep', 'insomnia', 'late night'],
        'anxiety spikes': ['anxiety', 'panic', 'worry'],
        'parent-child conflict': ['parent', 'family conflict', 'arguments'],
    }
    for label, markers in concern_map.items():
        if any(marker in text for marker in markers):
            concerns.append(label)

    sentiment = 'awareness'
    if any(token in text for token in {'worry', 'worried', 'concern', 'fear', 'stress'}):
        sentiment = 'concern'
    elif any(token in text for token in {'debate', 'controversy', 'disagree'}):
        sentiment = 'debate'

    statements = []
    for snippet in snippets[:6]:
        compact = _clean_text(snippet)
        if compact:
            statements.append(compact[:140])

    return {
        'is_trending': len(snippets) >= 3 or any(word in text for word in {'trending', 'viral', 'breaking'}),
        'regions': regions or ['International'],
        'public_concerns': concerns or ['parent uncertainty'],
        'statements': statements[:5] or [f'Families are actively discussing "{topic_title}".'],
        'sentiment': sentiment,
    }


def _normalize_list(value: Any) -> list[str]:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return _dedupe(cleaned)
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return [value.strip()]
        return _normalize_list(parsed)
    return []


def _normalize_sentiment(value: Any) -> str:
    normalized = str(value or '').strip().lower()
    if normalized in {'concern', 'debate', 'awareness'}:
        return normalized
    return 'awareness'


def _dedupe(rows: list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for row in rows:
        key = row.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def _clean_text(value: str) -> str:
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', value, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _detect_regions(text: str) -> list[str]:
    regions: list[str] = []
    matches = {
        'India': ['india', 'indian', 'delhi', 'mumbai', 'bangalore'],
        'US': ['united states', 'u.s.', 'usa', 'america'],
        'UK': ['united kingdom', 'uk', 'england', 'london'],
        'Australia': ['australia', 'sydney', 'melbourne'],
        'Canada': ['canada', 'toronto', 'ontario'],
    }
    for label, tokens in matches.items():
        if any(token in text for token in tokens):
            regions.append(label)
    if not regions:
        regions.append('International')
    return regions


def _extract_numeric_sentences(text: str) -> list[str]:
    pattern = re.compile(r'[^.?!\n]*\b(?:\d+(?:\.\d+)?%?|\d+\s*in\s*\d+)\b[^.?!\n]*[.?!]?', flags=re.IGNORECASE)
    rows: list[str] = []
    for match in pattern.findall(text):
        cleaned = _clean_text(match)
        if len(cleaned) < 10:
            continue
        if _is_noisy_statistic(cleaned):
            continue
        if _word_count(cleaned) < 6:
            continue
        if len(cleaned) > 220:
            cleaned = cleaned[:217] + '...'
        rows.append(cleaned)
    return _dedupe(rows)


def _is_noisy_statistic(text: str) -> bool:
    lowered = str(text or '').lower()
    if not lowered.strip():
        return True

    # Filter CSS/JS/layout fragments that leak from scraped pages.
    noise_tokens = (
        '@media',
        'padding',
        'margin',
        'font-size',
        'px',
        '!important',
        'queryselector',
        'getelementsby',
        'function(',
        'var ',
        '{',
        '}',
        ';',
    )
    if any(token in lowered for token in noise_tokens):
        return True

    # Keep only sentence-like snippets with enough alphabetic words.
    alpha_words = re.findall(r"[a-zA-Z']+", lowered)
    if len(alpha_words) < 6:
        return True
    return False


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9']+", str(text or '')))
