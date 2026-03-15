from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import html
import logging
import math
from pathlib import Path
import re
from typing import Any
from urllib.parse import urlparse

import feedparser
import httpx
import yaml
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.topic import Topic
from app.models.enums import TopicStatus
from app.services.content_screening_service import ContentScreeningService
from app.services.duplicate_service import DuplicateChecker
from app.services.llm_service import LLMClient
from app.services.trend_enrichment_service import TrendEnrichmentService

settings = get_settings()

X_DISCOVERY_MAX_PAGES = 2
X_DISCOVERY_RELAXED_PAGES = 1
X_DISCOVERY_MIN_CHILD_MATCHES = 10
PIPELINE_TOP_TWEETS = 5
PIPELINE_ARTICLES_PER_HEADING = 3
PER_SOURCE_MATCH_LIMIT = 5
PER_SOURCE_LLM_PREFILTER_LIMIT = 20
PER_TWEET_CANDIDATE_POOL_LIMIT = 50
FALLBACK_HEADING_QUERIES = (
    'Child anxiety signs parents are discussing this week',
    'Teen depression and school pressure concerns among families',
    'Student stress and sleep disruption in exam season',
    'Parent concerns about ADHD support for school children',
    'Adolescent mental health support strategies for families',
)

HEALTHCARE_TOPIC_TERMS = (
    'mental health',
    'anxiety',
    'depression',
    'stress',
    'adhd',
    'autism',
    'trauma',
    'therapy',
    'counseling',
    'counselling',
    'wellbeing',
    'well-being',
    'psychiatry',
    'psychology',
    'behavioral health',
    'behavioural health',
    'suicide',
    'self-harm',
    'eating disorder',
    'bullying',
    'child welfare',
    'pediatric',
    'adolescent health',
)

CHILD_TOPIC_TERMS = (
    'child',
    'children',
    'kid',
    'kids',
    'teen',
    'teens',
    'adolescent',
    'adolescents',
    'youth',
    'student',
    'students',
    'school',
    'parent',
    'parenting',
    'pediatric',
)

MENTAL_HEALTH_TERMS = (
    'mental health',
    'anxiety',
    'depression',
    'stress',
    'therapy',
    'counseling',
    'counselling',
    'adhd',
    'autism',
    'trauma',
    'wellbeing',
    'well-being',
)

LEGACY_TRUSTED_RSS_SOURCES = (
    {
        'name': 'World Health Organization',
        'domain': 'who.int',
        'feed_url': 'https://www.who.int/rss-feeds/news-english.xml',
    },
    {
        'name': 'Centers for Disease Control and Prevention',
        'domain': 'cdc.gov',
        'feed_url': 'https://tools.cdc.gov/api/v2/resources/media/132608.rss',
    },
    {
        'name': 'National Institutes of Health (NIH News)',
        'domain': 'nih.gov',
        'feed_url': 'https://www.nih.gov/rss.xml',
    },
)
GENERIC_HEADING_TERMS = {
    'child',
    'children',
    'teen',
    'teens',
    'adolescent',
    'adolescents',
    'student',
    'students',
    'school',
    'schools',
    'mental',
    'health',
    'anxiety',
    'depression',
    'stress',
    'therapy',
    'support',
    'parents',
    'parent',
    'families',
    'family',
    'guidance',
    'update',
    'latest',
    'news',
}


def _normalized_host(value: str | None) -> str:
    host = urlparse(str(value or '')).netloc.lower().strip()
    if host.startswith('www.'):
        host = host[4:]
    return host


def _load_trusted_domain_name_map() -> dict[str, str]:
    path = Path(settings.trusted_sources_file)
    if not path.exists():
        return {}

    try:
        with path.open('r', encoding='utf-8') as handle:
            payload = yaml.safe_load(handle) or {}
    except Exception:
        return {}

    if not isinstance(payload, dict):
        return {}

    sources = payload.get('sources') or {}
    if not isinstance(sources, dict):
        return {}

    domain_names: dict[str, str] = {}
    for source_name, source_payload in sources.items():
        if not isinstance(source_payload, dict):
            continue
        normalized_name = str(source_name or '').strip()
        for domain in source_payload.get('domains') or []:
            normalized_domain = str(domain or '').strip().lower()
            if not normalized_domain:
                continue
            if normalized_domain not in domain_names:
                domain_names[normalized_domain] = normalized_name or normalized_domain

    return domain_names


def _best_matching_domain(host: str, trusted_domains: set[str]) -> str:
    if not host:
        return ''
    for domain in sorted(trusted_domains, key=len, reverse=True):
        if host == domain or host.endswith(f'.{domain}'):
            return domain
    return host


def _build_trusted_rss_sources() -> tuple[dict[str, str], ...]:
    trusted_domain_name_map = _load_trusted_domain_name_map()
    trusted_domains = set(trusted_domain_name_map.keys())
    if not trusted_domains:
        return tuple(dict(row) for row in LEGACY_TRUSTED_RSS_SOURCES)

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for feed_url in settings.rss_feeds or []:
        normalized_feed_url = str(feed_url or '').strip()
        if not normalized_feed_url:
            continue
        host = _normalized_host(normalized_feed_url)
        if not host:
            continue

        matched_domain = _best_matching_domain(host, trusted_domains)
        if not matched_domain:
            continue
        source_name = trusted_domain_name_map.get(matched_domain, host)
        key = (matched_domain, normalized_feed_url)
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                'name': source_name,
                'domain': matched_domain,
                'feed_url': normalized_feed_url,
            }
        )

    if rows:
        return tuple(rows)
    return tuple(dict(row) for row in LEGACY_TRUSTED_RSS_SOURCES)


TRUSTED_RSS_SOURCES = _build_trusted_rss_sources()
TRUSTED_DOMAIN_ORDER = tuple(
    dict.fromkeys(
        str(source.get('domain') or '').strip()
        for source in TRUSTED_RSS_SOURCES
        if str(source.get('domain') or '').strip()
    )
)

def _parse_published_at(value: Any) -> datetime | None:
    """Convert a published_at string to a timezone-aware datetime, or return None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value
    raw = str(value).strip()
    if not raw:
        return None
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S.%f%z'):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    try:
        from email.utils import parsedate_to_datetime
        return parsedate_to_datetime(raw)
    except Exception:
        return None


class TrendCollector:
    def __init__(self) -> None:
        self.duplicate_checker = DuplicateChecker()
        self.screening = ContentScreeningService()
        self.enrichment = TrendEnrichmentService()
        self.llm = LLMClient()
        self._trusted_feed_cache: list[dict] | None = None

    async def collect_and_store(self, db: AsyncSession, query: str | None = None) -> dict[str, int | list[dict]]:
        fetched_candidates = 0
        max_heading_queries = PIPELINE_TOP_TWEETS
        articles_per_heading_target = PIPELINE_ARTICLES_PER_HEADING
        normalized_query = query.strip() if query else None
        x_discovery = await self._fetch_x_ranked_topics(query=normalized_query)
        ranked_topics = x_discovery.get('ranked_topics', [])
        trending_tweets = x_discovery.get('trending_tweets', [])
        preferred_country = str(x_discovery.get('preferred_country') or 'US').upper()
        heading_queries = await self._build_article_queries_from_top_tweets(trending_tweets)
        heading_queries = self._ensure_heading_queries(
            heading_queries=heading_queries,
            trending_tweets=trending_tweets,
            ranked_topics=ranked_topics,
            max_items=max_heading_queries,
        )
        trending_tweets = _apply_llm_headings_to_trending_tweets(trending_tweets, heading_queries)

        phrase_list = self._build_phrase_list(
            heading_queries=heading_queries,
            ranked_topics=ranked_topics,
            normalized_query=normalized_query,
            max_items=max_heading_queries,
        )

        per_heading_selection: list[dict[str, Any]] = []

        stored = 0
        skipped = 0
        duplicate_rejected = 0
        screened_out = 0
        trust_rejected = 0
        replaced_existing = 0
        selected_urls_global: set[str] = set()
        trusted_feed_rows = await self._load_trusted_feed_rows()
        heading_candidate_batches: list[tuple[str, dict, list[dict]]] = []
        candidate_urls: set[str] = set()

        for phrase, item_x_stats in phrase_list:
            tweet_context = ''
            if isinstance(item_x_stats, dict):
                tweet_context = str(item_x_stats.get('sample_text') or '').strip()
            heading_candidates = await self._fetch_trusted_rss_entries_for_heading(
                phrase,
                desired_count=articles_per_heading_target,
                preloaded_rows=trusted_feed_rows,
                tweet_text=tweet_context or None,
            )
            heading_candidate_batches.append((phrase, item_x_stats, heading_candidates))
            for row in heading_candidates:
                source_url = str(row.get('source_url') or '').strip()
                if source_url:
                    candidate_urls.add(source_url)

        existing_topics_by_url = await self._load_existing_topics_by_urls(db, candidate_urls)

        for phrase, item_x_stats, heading_candidates in heading_candidate_batches:
            selected_for_heading = 0
            considered_for_heading = 0
            seen_urls_for_heading: set[str] = set()
            skipped_for_heading = 0
            duplicate_rejected_for_heading = 0
            screened_out_for_heading = 0
            trust_rejected_for_heading = 0
            replaced_existing_for_heading = 0

            for item in heading_candidates:
                source_url = str(item.get('source_url') or '').strip()
                if not source_url or source_url in seen_urls_for_heading or source_url in selected_urls_global:
                    continue
                seen_urls_for_heading.add(source_url)
                considered_for_heading += 1
                fetched_candidates += 1

                item['_x_source_phrase'] = phrase
                outcome = await self._screen_enrich_and_store(
                    db,
                    item=item,
                    x_engagement_score=item_x_stats['engagement_score'] if item_x_stats else None,
                    x_tweet_count=item_x_stats['tweet_count'] if item_x_stats else None,
                    x_trend_phrase=item_x_stats['topic'] if item_x_stats else None,
                    x_top_tweet_raw=item_x_stats.get('raw_tweet') if item_x_stats else None,
                    skip_enrichment=True,
                    skip_semantic_duplicate_check=True,
                    existing_topics_by_url=existing_topics_by_url,
                )
                if outcome == 'stored':
                    stored += 1
                    selected_for_heading += 1
                    selected_urls_global.add(source_url)
                elif outcome == 'skipped':
                    skipped += 1
                    skipped_for_heading += 1
                elif outcome == 'duplicate_rejected':
                    duplicate_rejected += 1
                    duplicate_rejected_for_heading += 1
                elif outcome == 'screened_out':
                    screened_out += 1
                    screened_out_for_heading += 1
                elif outcome == 'trust_rejected':
                    trust_rejected += 1
                    trust_rejected_for_heading += 1
                elif outcome == 'replaced_existing':
                    replaced_existing += 1
                    replaced_existing_for_heading += 1
                    selected_for_heading += 1
                    selected_urls_global.add(source_url)

                if selected_for_heading >= articles_per_heading_target:
                    break

            per_heading_selection.append(
                {
                    'heading': phrase,
                    'matched_candidates': len(heading_candidates),
                    'selected_articles': selected_for_heading,
                    'considered_candidates': considered_for_heading,
                    'skipped': skipped_for_heading,
                    'duplicate_rejected': duplicate_rejected_for_heading,
                    'screened_out': screened_out_for_heading,
                    'trust_rejected': trust_rejected_for_heading,
                    'replaced_existing': replaced_existing_for_heading,
                }
            )

        # Fetch from NewsAPI and SerpAPI (verified APIs — trust check bypassed)
        api_articles = await self._fetch_newsapi_articles(query=normalized_query)
        api_articles += await self._fetch_serpapi_articles(query=normalized_query)
        api_stored = 0
        if api_articles:
            api_urls = {str(a.get('source_url') or '').strip() for a in api_articles if a.get('source_url')}
            existing_api_topics = await self._load_existing_topics_by_urls(db, api_urls)
            for article in api_articles:
                source_url = str(article.get('source_url') or '').strip()
                if not source_url or source_url in selected_urls_global:
                    continue
                outcome = await self._screen_enrich_and_store(
                    db,
                    item=article,
                    skip_enrichment=True,
                    skip_semantic_duplicate_check=True,
                    skip_trust_check=True,
                    existing_topics_by_url=existing_api_topics,
                )
                if outcome in ('stored', 'replaced_existing'):
                    api_stored += 1
                    selected_urls_global.add(source_url)

        await db.commit()
        return {
            'fetched': fetched_candidates,
            'x_topics_found': len(ranked_topics),
            'x_preferred_country': preferred_country,
            'x_india_tweets': int(x_discovery.get('india_tweet_count', 0) or 0),
            'x_us_tweets': int(x_discovery.get('us_tweet_count', 0) or 0),
            'article_heading_queries': [row['query'] for row in heading_queries],
            'articles_per_heading_target': articles_per_heading_target,
            'heading_selection': per_heading_selection,
            'stored': stored + api_stored,
            'api_stored': api_stored,
            'skipped': skipped,
            'duplicate_rejected': duplicate_rejected,
            'screened_out': screened_out,
            'trust_rejected': trust_rejected,
            'replaced_existing': replaced_existing,
            'trending_tweets': trending_tweets,
        }

    async def _load_existing_topics_by_urls(self, db: AsyncSession, urls: set[str]) -> dict[str, Topic]:
        cleaned_urls = [url for url in urls if str(url).strip()]
        if not cleaned_urls:
            return {}

        result = await db.execute(select(Topic).where(Topic.source_url.in_(cleaned_urls)))
        topics = result.scalars().all()
        return {
            str(topic.source_url).strip(): topic
            for topic in topics
            if str(topic.source_url).strip()
        }

    def _build_phrase_list(
        self,
        *,
        heading_queries: list[dict],
        ranked_topics: list[dict],
        normalized_query: str | None,
        max_items: int,
    ) -> list[tuple[str, dict]]:
        phrases: list[tuple[str, dict]] = []
        seen_phrases: set[str] = set()

        def add_phrase(raw_phrase: str | None, stats: dict) -> None:
            phrase = str(raw_phrase or '').strip()
            if not phrase:
                return
            key = re.sub(r'\s+', ' ', phrase).strip().lower()
            if not key or key in seen_phrases:
                return
            seen_phrases.add(key)
            phrases.append((phrase, stats))

        # Required flow: when LLM headings are available, use them in order only.
        for row in heading_queries:
            if not isinstance(row, dict):
                continue
            add_phrase(row.get('query'), row)
            if len(phrases) >= max_items:
                return phrases

        if phrases:
            return phrases[:max_items]

        for row in ranked_topics:
            if not isinstance(row, dict):
                continue
            add_phrase(row.get('topic'), row)
            if len(phrases) >= max_items:
                return phrases

        if normalized_query:
            add_phrase(
                normalized_query,
                {'topic': normalized_query, 'engagement_score': 0.0, 'tweet_count': 0},
            )

        return phrases[:max_items]

    def _ensure_heading_queries(
        self,
        *,
        heading_queries: list[dict],
        trending_tweets: list[dict],
        ranked_topics: list[dict],
        max_items: int,
    ) -> list[dict]:
        normalized: list[dict] = []
        seen: set[str] = set()

        def add_row(row: dict) -> None:
            query = str(row.get('query') or '').strip()
            if not query:
                return
            key = re.sub(r'\s+', ' ', query).strip().lower()
            if not key or key in seen:
                return
            seen.add(key)
            normalized.append(row)

        for row in heading_queries:
            if isinstance(row, dict):
                add_row(row)
            if len(normalized) >= max_items:
                return normalized[:max_items]

        for tweet in trending_tweets:
            if not isinstance(tweet, dict):
                continue
            tweet_text = str(tweet.get('text') or tweet.get('sample_text') or '').strip()
            if not tweet_text:
                continue
            fallback_heading = _fallback_heading_from_tweet_text(tweet_text)
            add_row(
                {
                    'query': fallback_heading,
                    'engagement_score': float(tweet.get('engagement_score', 0.0) or 0.0),
                    'tweet_count': int(tweet.get('tweet_count', 1) or 1),
                    'like_count': int(tweet.get('like_count', 0) or 0),
                    'reply_count': int(tweet.get('reply_count', 0) or 0),
                    'retweet_count': int(tweet.get('retweet_count', 0) or 0),
                    'quote_count': int(tweet.get('quote_count', 0) or 0),
                    'sample_text': tweet_text,
                    'raw_tweet': tweet.get('raw_tweet') if isinstance(tweet.get('raw_tweet'), dict) else None,
                    'topic': fallback_heading,
                }
            )
            if len(normalized) >= max_items:
                return normalized[:max_items]

        for row in ranked_topics:
            if not isinstance(row, dict):
                continue
            fallback_heading = _sanitize_heading(str(row.get('topic') or ''))
            if not fallback_heading:
                continue
            add_row(
                {
                    'query': fallback_heading,
                    'engagement_score': float(row.get('engagement_score', 0.0) or 0.0),
                    'tweet_count': int(row.get('tweet_count', 0) or 0),
                    'like_count': int(row.get('like_count', 0) or 0),
                    'reply_count': int(row.get('reply_count', 0) or 0),
                    'retweet_count': int(row.get('retweet_count', 0) or 0),
                    'quote_count': int(row.get('quote_count', 0) or 0),
                    'sample_text': str(row.get('sample_text') or ''),
                    'raw_tweet': row.get('raw_tweet') if isinstance(row.get('raw_tweet'), dict) else None,
                    'topic': fallback_heading,
                }
            )
            if len(normalized) >= max_items:
                break

        if len(normalized) < max_items:
            for heading in FALLBACK_HEADING_QUERIES:
                add_row(
                    {
                        'query': heading,
                        'engagement_score': 0.0,
                        'tweet_count': 0,
                        'like_count': 0,
                        'reply_count': 0,
                        'retweet_count': 0,
                        'quote_count': 0,
                        'sample_text': heading,
                        'raw_tweet': None,
                        'topic': heading,
                    }
                )
                if len(normalized) >= max_items:
                    break

        return normalized[:max_items]

    async def _build_article_queries_from_top_tweets(self, trending_tweets: list[dict]) -> list[dict]:
        if not trending_tweets:
            return []

        selected_queries: list[dict] = []
        selected_tweets: list[dict] = []
        heading_tasks: list[asyncio.Task[str]] = []

        for tweet in trending_tweets[:PIPELINE_TOP_TWEETS]:
            if not isinstance(tweet, dict):
                continue
            tweet_text = str(tweet.get('text') or tweet.get('sample_text') or '').strip()
            if not tweet_text:
                continue

            selected_tweets.append(tweet)
            heading_tasks.append(asyncio.create_task(self._generate_article_heading_from_tweet_text(tweet_text)))

        if not heading_tasks:
            return []

        generated_headings = await asyncio.gather(*heading_tasks, return_exceptions=True)
        for tweet, generated in zip(selected_tweets, generated_headings):
            tweet_text = str(tweet.get('text') or tweet.get('sample_text') or '').strip()
            if isinstance(generated, Exception):
                heading = _fallback_heading_from_tweet_text(tweet_text)
            else:
                heading = str(generated or '').strip() or _fallback_heading_from_tweet_text(tweet_text)

            selected_queries.append(
                {
                    'query': heading,
                    'engagement_score': float(tweet.get('engagement_score', 0.0) or 0.0),
                    'tweet_count': int(tweet.get('tweet_count', 1) or 1),
                    'like_count': int(tweet.get('like_count', 0) or 0),
                    'reply_count': int(tweet.get('reply_count', 0) or 0),
                    'retweet_count': int(tweet.get('retweet_count', 0) or 0),
                    'quote_count': int(tweet.get('quote_count', 0) or 0),
                    'sample_text': tweet_text,
                    'raw_tweet': tweet.get('raw_tweet') if isinstance(tweet.get('raw_tweet'), dict) else None,
                    'topic': heading,
                }
            )

        return selected_queries

    async def _generate_article_heading_from_tweet_text(self, tweet_text: str) -> str:
        system_prompt = (
            'You rewrite tweet text into one factual, highly relevant article heading. Return exactly one heading only.'
        )
        prompt = (
            'Convert this tweet text into one precise article heading.\n'
            'Requirements:\n'
            '- Preserve original meaning exactly\n'
            '- Include key entities and mental-health context\n'
            '- 8 to 14 words\n'
            '- No hashtags, no emojis, no quotes, no trailing punctuation\n'
            '- Output only the heading text\n\n'
            f'Tweet text: {tweet_text}'
        )
        try:
            generated = await asyncio.wait_for(
                self.llm.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=settings.llm_quality_model,
                    temperature=0.0,
                ),
                timeout=6.0,
            )
        except Exception:
            generated = ''

        heading = _sanitize_heading(generated)
        if heading:
            return heading
        return _fallback_heading_from_tweet_text(tweet_text)

    async def _fetch_x_ranked_topics(self, query: str | None = None) -> dict[str, list[dict]]:
        if not settings.x_bearer_token:
            return {
                'ranked_topics': [],
                'trending_tweets': [],
                'preferred_country': 'US',
                'india_tweet_count': 0,
                'us_tweet_count': 0,
            }

        effective_query = _strip_pro_only_operators(_compose_x_discovery_query(query))
        logging.info('X API discovery query: %s', effective_query)
        headers = {'Authorization': f'Bearer {settings.x_bearer_token}'}
        url = 'https://api.twitter.com/2/tweets/search/recent'

        async def fetch_pages(*, search_query: str, max_pages: int) -> tuple[list[dict], dict[str, dict], dict[str, dict]]:
            rows: list[dict] = []
            users_by_id: dict[str, dict] = {}
            places_by_id: dict[str, dict] = {}
            next_token: str | None = None
            per_page_max_results = max(10, min(100, int(settings.x_topic_max_results or 25)))
            async with httpx.AsyncClient(timeout=15.0) as client:
                for _ in range(max_pages):
                    params = {
                        'query': search_query,
                        'max_results': per_page_max_results,
                        'tweet.fields': 'author_id,created_at,entities,geo,lang,public_metrics,text',
                        'expansions': 'author_id,geo.place_id',
                        'user.fields': 'created_at,public_metrics,verified',
                        'place.fields': 'country_code',
                    }
                    if next_token:
                        params['next_token'] = next_token

                    response = await client.get(url, params=params, headers=headers)
                    response.raise_for_status()
                    payload = response.json()

                    page_rows = payload.get('data') or []
                    if not isinstance(page_rows, list) or not page_rows:
                        break

                    rows.extend(row for row in page_rows if isinstance(row, dict))
                    includes = payload.get('includes') or {}
                    for user_row in includes.get('users') or []:
                        if not isinstance(user_row, dict):
                            continue
                        user_id = str(user_row.get('id') or '').strip()
                        if user_id:
                            users_by_id[user_id] = user_row
                    for place_row in includes.get('places') or []:
                        if not isinstance(place_row, dict):
                            continue
                        place_id = str(place_row.get('id') or '').strip()
                        if place_id:
                            places_by_id[place_id] = place_row
                    next_token = str((payload.get('meta') or {}).get('next_token') or '').strip() or None
                    if not next_token:
                        break
            return rows, users_by_id, places_by_id

        try:
            tweets, users_by_id, places_by_id = await fetch_pages(search_query=effective_query, max_pages=X_DISCOVERY_MAX_PAGES)
        except httpx.HTTPStatusError as exc:
            try:
                error_body = exc.response.text
            except Exception:
                error_body = '(could not read response body)'
            logging.error('X API fetch failed [%s]: %s | response body: %s', exc.response.status_code, exc, error_body)
            fallback_query = _relax_x_discovery_query(effective_query)
            if fallback_query and fallback_query != effective_query:
                try:
                    tweets, users_by_id, places_by_id = await fetch_pages(
                        search_query=fallback_query,
                        max_pages=X_DISCOVERY_RELAXED_PAGES,
                    )
                    logging.info('X API fallback query succeeded.')
                except Exception as fallback_exc:
                    logging.error('X API fallback query failed: %s', fallback_exc)
                    return {
                        'ranked_topics': [],
                        'trending_tweets': [],
                        'preferred_country': 'US',
                        'india_tweet_count': 0,
                        'us_tweet_count': 0,
                    }
            else:
                return {
                    'ranked_topics': [],
                    'trending_tweets': [],
                    'preferred_country': 'US',
                    'india_tweet_count': 0,
                    'us_tweet_count': 0,
                }
        except Exception as exc:
            logging.error('X API fetch failed: %s', exc)
            return {
                'ranked_topics': [],
                'trending_tweets': [],
                'preferred_country': 'US',
                'india_tweet_count': 0,
                'us_tweet_count': 0,
            }

        child_matches = [
            row for row in tweets
            if _is_child_mental_health_related(str(row.get('text', '')).strip())
        ]
        if len(child_matches) < X_DISCOVERY_MIN_CHILD_MATCHES:
            relaxed_query = _relax_x_discovery_query(effective_query)
            if relaxed_query != effective_query:
                try:
                    relaxed_rows, relaxed_users, relaxed_places = await fetch_pages(search_query=relaxed_query, max_pages=X_DISCOVERY_RELAXED_PAGES)
                    tweets = _dedupe_tweets_by_id_and_text(tweets + relaxed_rows)
                    users_by_id.update(relaxed_users)
                    places_by_id.update(relaxed_places)
                except Exception as exc:
                    logging.warning('X API relaxed query fallback failed: %s', exc)

        candidate_tweets: list[dict] = []
        topic_scores: dict[str, float] = {}
        topic_counts: dict[str, int] = {}
        topic_recent_hits: dict[str, int] = {}
        topic_metrics: dict[str, dict] = {}  # best raw metrics per topic
        topic_best_text: dict[str, str] = {}  # best tweet text per topic
        topic_best_created_at: dict[str, str] = {}
        topic_best_rank_score: dict[str, float] = {}

        india_tweet_count = 0
        us_tweet_count = 0
        for row in tweets:
            if not isinstance(row, dict):
                continue
            text = str(row.get('text', '')).strip()
            if not text or not _is_child_mental_health_related(text):
                continue
            country = _extract_tweet_place_country(tweet=row, places_by_id=places_by_id)
            if country == 'IN':
                india_tweet_count += 1
            elif country == 'US':
                us_tweet_count += 1
        india_priority_active = india_tweet_count >= settings.x_topic_india_min_tweets

        logging.info('X API returned %d tweets', len(tweets))
        child_mh_count = 0
        for tweet in tweets:
            if not isinstance(tweet, dict):
                continue
            text = str(tweet.get('text', '')).strip()
            if not text:
                continue
            if not _is_child_mental_health_related(text):
                continue
            child_mh_count += 1
            place_country = _extract_tweet_place_country(tweet=tweet, places_by_id=places_by_id)
            metrics = tweet.get('public_metrics') or {}
            score = _engagement_score(metrics)
            created_at = _parse_twitter_datetime(tweet.get('created_at'))
            author_id = str(tweet.get('author_id') or '').strip()
            author = users_by_id.get(author_id, {}) if author_id else {}
            followers_count = _extract_followers_count(author)
            account_age_days = _extract_account_age_days(author)
            tweet_count_total = _extract_author_tweet_count(author)
            hashtag_count = _extract_hashtag_count(tweet)
            velocity = _engagement_velocity(score, created_at)
            normalized_score = _normalize_engagement_score(score, followers_count)
            quality_penalty = _quality_penalty_multiplier(
                account_age_days=account_age_days,
                followers_count=followers_count,
                tweet_count_total=tweet_count_total,
                hashtag_count=hashtag_count,
            )
            recency_weight = _recency_weight(created_at)
            rank_score = normalized_score * quality_penalty * recency_weight
            if india_priority_active and place_country == 'IN':
                rank_score *= settings.x_topic_india_rank_boost
            topic = _extract_topic_from_tweet(text=text, entities=tweet.get('entities'))
            candidate_tweets.append({
                'id': str(tweet.get('id') or ''),
                'author_id': author_id,
                'topic': topic or 'general child mental health',
                'engagement_score': round(score, 1),
                'rank_score': round(rank_score, 1),
                'raw_engagement_score': round(score, 1),
                'normalized_engagement_score': round(normalized_score, 4),
                'quality_penalty': round(quality_penalty, 3),
                'engagement_velocity': round(velocity, 3),
                'tweet_count': 1,
                'like_count': int(metrics.get('like_count', 0) or 0),
                'reply_count': int(metrics.get('reply_count', 0) or 0),
                'retweet_count': int(metrics.get('retweet_count', 0) or 0),
                'quote_count': int(metrics.get('quote_count', 0) or 0),
                'text': text,
                'sample_text': text,
                'created_at': str(tweet.get('created_at') or ''),
                'public_metrics': {
                    'retweet_count': int(metrics.get('retweet_count', 0) or 0),
                    'reply_count': int(metrics.get('reply_count', 0) or 0),
                    'like_count': int(metrics.get('like_count', 0) or 0),
                    'quote_count': int(metrics.get('quote_count', 0) or 0),
                },
                'place_country': place_country,
                'followers_count': followers_count,
                'account_age_days': round(account_age_days, 1),
                'hashtag_count': hashtag_count,
                'raw_tweet': tweet,
            })
            if score < settings.x_topic_min_raw_engagement_score:
                continue
            if velocity < settings.x_topic_min_velocity_per_hour:
                continue
            if not topic:
                continue
            topic_scores[topic] = topic_scores.get(topic, 0.0) + rank_score
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            if created_at and (datetime.now(timezone.utc) - created_at).total_seconds() <= 86400:
                topic_recent_hits[topic] = topic_recent_hits.get(topic, 0) + 1
            # Keep the highest-engagement tweet's metrics and text per topic
            if topic not in topic_best_rank_score or rank_score > topic_best_rank_score[topic]:
                topic_metrics[topic] = {
                    'like_count': int(metrics.get('like_count', 0) or 0),
                    'reply_count': int(metrics.get('reply_count', 0) or 0),
                    'retweet_count': int(metrics.get('retweet_count', 0) or 0),
                    'quote_count': int(metrics.get('quote_count', 0) or 0),
                }
                topic_best_text[topic] = text
                topic_best_created_at[topic] = str(tweet.get('created_at') or '')
                topic_best_rank_score[topic] = rank_score

        logging.info('Tweets passing child mental health filter: %d/%d', child_mh_count, len(tweets))
        logging.info('Extracted trending topics: %s', list(topic_scores.keys()))

        composite_scores: dict[str, float] = {}
        for topic, score in topic_scores.items():
            volume_bonus = 5.0 * float(topic_counts.get(topic, 0))
            recency_bonus = 8.0 * float(topic_recent_hits.get(topic, 0))
            composite_scores[topic] = score + volume_bonus + recency_bonus

        ranked = sorted(
            composite_scores.items(),
            key=lambda pair: (pair[1], topic_counts.get(pair[0], 0)),
            reverse=True,
        )

        selected: list[dict] = []
        for topic, score in ranked:
            count = topic_counts.get(topic, 0)
            if count < settings.x_topic_min_posts_per_topic:
                continue
            raw = topic_metrics.get(topic, {})
            selected.append({
                'topic': topic,
                'engagement_score': round(score, 1),
                'tweet_count': count,
                'like_count': raw.get('like_count', 0),
                'reply_count': raw.get('reply_count', 0),
                'retweet_count': raw.get('retweet_count', 0),
                'quote_count': raw.get('quote_count', 0),
                'sample_text': topic_best_text.get(topic, ''),
                'created_at': topic_best_created_at.get(topic, ''),
            })
            if len(selected) >= settings.x_topic_limit:
                break

        top_tweets = _select_top_recent_engaging_tweets(candidate_tweets, limit=PIPELINE_TOP_TWEETS)

        preferred_country = 'IN' if india_priority_active else 'US'

        return {
            'ranked_topics': selected,
            'trending_tweets': top_tweets,
            'preferred_country': preferred_country,
            'india_tweet_count': india_tweet_count,
            'us_tweet_count': us_tweet_count,
        }

    async def _screen_enrich_and_store(
        self,
        db: AsyncSession,
        *,
        item: dict,
        x_engagement_score: float | None = None,
        x_tweet_count: int | None = None,
        x_trend_phrase: str | None = None,
        x_top_tweet_raw: dict | None = None,
        skip_enrichment: bool = False,
        skip_semantic_duplicate_check: bool = False,
        skip_trust_check: bool = False,
        existing_topics_by_url: dict[str, Topic] | None = None,
    ) -> str:
        title = str(item.get('title') or '').strip()
        source_url = str(item.get('source_url') or '').strip()
        if not title or not source_url:
            return 'skipped'

        existing_topic = existing_topics_by_url.get(source_url) if existing_topics_by_url is not None else None
        if existing_topic is None and existing_topics_by_url is None:
            exists = await db.execute(select(Topic).where(Topic.source_url == source_url).limit(1))
            existing_topic = exists.scalar_one_or_none()
        if existing_topic is not None:
            existing_topic.title = title
            existing_topic.source_name = item.get('source_name')
            existing_topic.summary = item.get('summary')
            existing_topic.original_published_at = _parse_published_at(item.get('published_at'))
            existing_topic.related_keywords = item.get('keywords')
            existing_topic.x_engagement_score = x_engagement_score
            existing_topic.x_tweet_count = x_tweet_count
            existing_topic.x_trend_phrase = x_trend_phrase
            existing_topic.x_top_tweet_raw = x_top_tweet_raw
            existing_topic.created_at = datetime.now(timezone.utc)
            if existing_topic.status != TopicStatus.PROCESSED:
                existing_topic.status = TopicStatus.NEW
            if existing_topics_by_url is not None:
                existing_topics_by_url[source_url] = existing_topic
            return 'replaced_existing'

        decision = await self.screening.screen(
            title=title,
            summary=item.get('summary'),
            source_name=item.get('source_name'),
            source_url=source_url,
            use_llm=False,
        )
        minimum_trust = int(self.screening.trusted_sources.get('minimum_allowed_score', 40))
        heading_relevance = int(item.get('_heading_relevance_score', 0) or 0)
        fallback_allowed = (
            decision.trust_score >= minimum_trust
            and heading_relevance >= 1
        )

        if not skip_trust_check and not decision.allowed and not fallback_allowed:
            if decision.trust_score < minimum_trust:
                return 'trust_rejected'
            else:
                return 'screened_out'
        # For skip_trust_check (NewsAPI/SerpAPI verified sources), use a fixed trust score
        if skip_trust_check and decision.trust_score < minimum_trust:
            decision.trust_score = 80

        if skip_enrichment:
            is_trending = bool((x_tweet_count or 0) > 0 or (x_engagement_score or 0.0) > 0.0)
            trend_regions = _merge_regions([], title, item.get('summary'), x_trend_phrase)
            public_concerns: list[str] = []
            trend_statements: list[str] = []
            trend_sentiment = 'awareness'
            statistics: list[str] = []
        else:
            enrichment = await self.enrichment.enrich(topic_title=title, topic_summary=item.get('summary'))
            is_trending = enrichment.is_trending
            trend_regions = _merge_regions(enrichment.regions, title, item.get('summary'), x_trend_phrase)
            public_concerns = enrichment.public_concerns
            trend_statements = enrichment.statements
            trend_sentiment = enrichment.sentiment
            statistics = enrichment.statistics

        is_duplicate = False
        matched_topic_id: int | None = None
        embedding: list[float] | None = None
        if not skip_semantic_duplicate_check:
            is_duplicate, _score, matched_topic_id, embedding = await self.duplicate_checker.check_topic(
                db,
                title=title,
                summary=item.get('summary'),
                threshold=settings.duplicate_similarity_threshold,
            )

        if is_duplicate and matched_topic_id:
            matched_result = await db.execute(select(Topic).where(Topic.id == matched_topic_id).limit(1))
            matched_topic = matched_result.scalar_one_or_none()
            if (
                matched_topic is not None
                and matched_topic.status == TopicStatus.NEW
                and decision.trust_score > int(matched_topic.trust_score or 0)
                and matched_topic.source_url != source_url
            ):
                matched_topic.title = title
                matched_topic.source_url = source_url
                matched_topic.source_name = item.get('source_name')
                matched_topic.summary = item.get('summary')
                matched_topic.original_published_at = _parse_published_at(item.get('published_at'))
                matched_topic.related_keywords = item.get('keywords')
                matched_topic.embedding = embedding
                matched_topic.relevance_label = decision.relevance
                matched_topic.relevance_score = decision.relevance_score
                matched_topic.age_group = decision.age_group
                matched_topic.topic_type = decision.topic_type
                matched_topic.mental_health_specific = decision.mental_health_specific
                matched_topic.screening_reason = decision.reason
                matched_topic.trust_score = decision.trust_score
                matched_topic.is_trending = is_trending
                matched_topic.trend_regions = trend_regions
                matched_topic.public_concerns = public_concerns
                matched_topic.trend_statements = trend_statements
                matched_topic.trend_sentiment = trend_sentiment
                matched_topic.statistics = statistics
                matched_topic.x_engagement_score = x_engagement_score
                matched_topic.x_tweet_count = x_tweet_count
                matched_topic.x_trend_phrase = x_trend_phrase
                matched_topic.x_top_tweet_raw = x_top_tweet_raw
                return 'replaced_existing'
            return 'duplicate_rejected'

        topic = Topic(
            title=title,
            source_url=source_url,
            source_name=item.get('source_name'),
            summary=item.get('summary'),
            original_published_at=_parse_published_at(item.get('published_at')),
            related_keywords=item.get('keywords'),
            embedding=embedding,
            status=TopicStatus.NEW,
            relevance_label=decision.relevance,
            relevance_score=decision.relevance_score,
            age_group=decision.age_group,
            topic_type=decision.topic_type,
            mental_health_specific=decision.mental_health_specific,
            screening_reason=decision.reason,
            trust_score=decision.trust_score,
            is_trending=is_trending,
            trend_regions=trend_regions,
            public_concerns=public_concerns,
            trend_statements=trend_statements,
            trend_sentiment=trend_sentiment,
            statistics=statistics,
            x_engagement_score=x_engagement_score,
            x_tweet_count=x_tweet_count,
            x_trend_phrase=x_trend_phrase,
            x_top_tweet_raw=x_top_tweet_raw,
        )
        db.add(topic)
        await db.flush()
        if existing_topics_by_url is not None:
            existing_topics_by_url[source_url] = topic
        return 'stored'

    async def _fetch_newsapi_articles(self, query: str | None = None) -> list[dict]:
        q = query or 'mental health anxiety depression therapy children'
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    'https://newsapi.org/v2/everything',
                    params={
                        'q': q,
                        'language': 'en',
                        'sortBy': 'publishedAt',
                        'pageSize': 15,
                        'apiKey': settings.news_api_key,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            logger.warning('NewsAPI request failed for query=%s', q, exc_info=True)
            return []
        articles = []
        for article in data.get('articles', []):
            source_url = str(article.get('url') or '').strip()
            title = str(article.get('title') or '').strip()
            if not source_url or not title or '[Removed]' in title:
                continue
            articles.append({
                'title': title,
                'source_url': source_url,
                'source_name': str((article.get('source') or {}).get('name') or '').strip(),
                'summary': str(article.get('description') or article.get('content') or '').strip()[:1000],
                'published_at': article.get('publishedAt'),
                '_api_source': 'newsapi',
            })
        return articles

    async def _fetch_serpapi_articles(self, query: str | None = None) -> list[dict]:
        q = query or 'mental health news'
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    'https://serpapi.com/search',
                    params={
                        'engine': 'google_news',
                        'q': q,
                        'api_key': settings.serpapi_key,
                        'gl': 'us',
                        'hl': 'en',
                    },
                )
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            logger.warning('SerpAPI request failed for query=%s', q, exc_info=True)
            return []
        articles = []
        for result in data.get('news_results', [])[:15]:
            source_url = str(result.get('link') or '').strip()
            title = str(result.get('title') or '').strip()
            if not source_url or not title:
                continue
            source = result.get('source')
            source_name = ''
            if isinstance(source, dict):
                source_name = str(source.get('name') or '').strip()
            elif isinstance(source, str):
                source_name = source.strip()
            articles.append({
                'title': title,
                'source_url': source_url,
                'source_name': source_name,
                'summary': str(result.get('snippet') or '').strip(),
                'published_at': result.get('date'),
                '_api_source': 'serpapi',
            })
        return articles

    async def _load_trusted_feed_rows(self) -> list[dict]:
        if self._trusted_feed_cache is not None:
            return [dict(row) for row in self._trusted_feed_cache]

        async def load_source_rows(client: httpx.AsyncClient, source: dict[str, str]) -> list[dict]:
            source_name = str(source.get('name') or '').strip()
            source_domain = str(source.get('domain') or '').strip()
            source_feed_url = str(source.get('feed_url') or '').strip()
            if not source_domain or not source_feed_url:
                return []

            try:
                response = await client.get(
                    source_feed_url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    follow_redirects=True,
                )
                response.raise_for_status()
            except Exception as exc:
                logging.warning('Skipping feed %s after request failure: %s', source_feed_url, exc)
                return []

            parsed_rows = _parse_feed_content(str(response.text or ''), fallback_feed_url=source_feed_url)
            normalized: list[dict] = []
            for item in parsed_rows:
                source_url = str(item.get('source_url') or '').strip()
                if not source_url:
                    continue
                if _is_x_or_twitter_url(source_url):
                    continue
                if not _domain_matches_allowed(source_url, source_domain):
                    continue

                cloned = dict(item)
                if not cloned.get('source_name'):
                    cloned['source_name'] = source_name
                normalized.append(cloned)
            return normalized

        async with httpx.AsyncClient(timeout=10.0) as client:
            rows_by_source = await asyncio.gather(
                *(load_source_rows(client, source) for source in TRUSTED_RSS_SOURCES)
            )
        merged_rows = [row for source_rows in rows_by_source for row in source_rows]
        self._trusted_feed_cache = _dedupe_entries(merged_rows)
        return [dict(row) for row in self._trusted_feed_cache]

    # ── Per-source article fetching ──────────────────────────────────────

    async def _fetch_trusted_rss_entries_for_heading(
        self,
        heading: str,
        *,
        desired_count: int = 3,
        preloaded_rows: list[dict] | None = None,
        tweet_text: str | None = None,
    ) -> list[dict]:
        heading_text = str(heading or '').strip()
        tweet_context = str(tweet_text or '').strip()
        if not heading_text:
            return []
        final_limit = max(int(desired_count), 0)
        if final_limit == 0:
            return []

        all_rows = preloaded_rows if preloaded_rows is not None else await self._load_trusted_feed_rows()
        if not all_rows:
            return []

        candidate_pool = _build_candidate_pool_for_heading(
            rows=all_rows,
            heading=heading_text,
            tweet_text=tweet_context or None,
            limit=PER_TWEET_CANDIDATE_POOL_LIMIT,
        )
        if not candidate_pool:
            return []

        per_source_prefilter: list[tuple[str, list[dict]]] = []
        for domain in TRUSTED_DOMAIN_ORDER:
            source_rows = _prefilter_rows_by_heading_title(
                rows=candidate_pool,
                heading=heading_text,
                source_domain=domain,
                limit=PER_SOURCE_LLM_PREFILTER_LIMIT,
                tweet_text=tweet_context or None,
            )
            per_source_prefilter.append((domain, source_rows))

        domain_rank_tasks = [
            asyncio.create_task(
                self._rank_article_titles_with_llm(
                    heading=heading_text,
                    rows=source_rows,
                    top_k=PER_SOURCE_MATCH_LIMIT,
                    tweet_text=tweet_context or None,
                )
            )
            for _domain, source_rows in per_source_prefilter
        ]
        domain_rank_results = await asyncio.gather(*domain_rank_tasks, return_exceptions=True)

        top_rows_by_source: list[dict] = []
        for (domain, source_rows), ranked_rows in zip(per_source_prefilter, domain_rank_results):
            if isinstance(ranked_rows, Exception):
                ranked = _fallback_rank_rows_by_heading_title(
                    rows=source_rows,
                    heading=heading_text,
                    limit=PER_SOURCE_MATCH_LIMIT,
                    tweet_text=tweet_context or None,
                )
            else:
                ranked = ranked_rows

            for row in ranked[:PER_SOURCE_MATCH_LIMIT]:
                candidate = dict(row)
                fast_score = int(candidate.get('_heading_title_fast_score', 0) or 0)
                llm_score = int(candidate.get('_heading_title_llm_score', 0) or 0)
                candidate['_heading_relevance_score'] = max(fast_score, llm_score)
                candidate['_source_domain'] = domain
                candidate['_child_related'] = _is_child_mental_health_related(str(candidate.get('title') or ''))
                top_rows_by_source.append(candidate)

        if not top_rows_by_source:
            return []

        final_ranked = await self._rank_article_titles_with_llm(
            heading=heading_text,
            rows=top_rows_by_source,
            top_k=final_limit,
            tweet_text=tweet_context or None,
        )
        if not final_ranked:
            final_ranked = _fallback_rank_rows_by_heading_title(
                rows=top_rows_by_source,
                heading=heading_text,
                limit=final_limit,
                tweet_text=tweet_context or None,
            )

        deduped = _dedupe_rows_by_source_url(final_ranked)
        filtered = [
            row for row in deduped
            if _passes_heading_relevance_gate(
                item=row,
                heading=heading_text,
                tweet_text=tweet_context or None,
            )
        ]
        return [dict(row) for row in filtered[:final_limit]]

    async def _rank_article_titles_with_llm(
        self,
        *,
        heading: str,
        rows: list[dict],
        top_k: int,
        tweet_text: str | None = None,
    ) -> list[dict]:
        limit = max(int(top_k), 0)
        if limit == 0:
            return []

        prepared: list[dict] = []
        seen_urls: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            source_url = str(row.get('source_url') or '').strip()
            title = str(row.get('title') or '').strip()
            if not source_url or not title or source_url in seen_urls:
                continue
            seen_urls.add(source_url)

            candidate = dict(row)
            fast_score = _heading_article_match_score(
                heading=heading,
                article_title=title,
                article_summary=str(row.get('summary') or ''),
                tweet_text=tweet_text,
            )
            candidate['_heading_title_fast_score'] = int(candidate.get('_heading_title_fast_score', 0) or fast_score or 0)
            prepared.append(candidate)

        if not prepared:
            return []

        numbered_titles = '\n'.join(
            f"{index}. {str(row.get('title') or '').strip()}"
            for index, row in enumerate(prepared, start=1)
        )
        system_prompt = (
            'You are a precise relevance scorer. Compare one tweet heading and tweet context against candidate article headings.'
        )
        tweet_context_block = ''
        if tweet_text:
            tweet_context_block = f'Original tweet context: {tweet_text}\n\n'
        prompt = (
            'Rank candidate article headings by relevance to the tweet heading.\n'
            'Hard rules:\n'
            '- Compare heading text and tweet context only.\n'
            '- Do not use article body assumptions.\n'
            '- Reward strong semantic and keyword overlap.\n'
            '- Penalize weak or generic matches.\n'
            f'- Return at most {limit} items.\n'
            'Return JSON only in this exact shape:\n'
            '{"ranked":[{"index":1,"score":97}]}\n\n'
            f'Tweet heading: {heading}\n\n'
            f'{tweet_context_block}'
            'Candidate article headings:\n'
            f'{numbered_titles}'
        )

        payload: dict[str, Any] = {}
        try:
            payload = await asyncio.wait_for(
                self.llm.generate_json(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=settings.llm_quality_model,
                    temperature=0.0,
                ),
                timeout=8.0,
            )
        except Exception:
            payload = {}

        ranked: list[dict] = []
        used_indexes: set[int] = set()
        ranked_payload = payload.get('ranked') if isinstance(payload, dict) else None
        if isinstance(ranked_payload, list):
            for entry in ranked_payload:
                if not isinstance(entry, dict):
                    continue
                try:
                    index = int(entry.get('index', 0) or 0)
                except (TypeError, ValueError):
                    continue
                if index < 1 or index > len(prepared) or index in used_indexes:
                    continue
                used_indexes.add(index)
                try:
                    raw_score = float(entry.get('score', 0) or 0)
                except (TypeError, ValueError):
                    raw_score = 0.0
                llm_score = max(0, min(int(round(raw_score)), 100))
                candidate = dict(prepared[index - 1])
                fast_score = int(candidate.get('_heading_title_fast_score', 0) or 0)
                candidate['_heading_title_llm_score'] = llm_score
                candidate['_heading_relevance_score'] = max(llm_score, fast_score)
                ranked.append(candidate)
                if len(ranked) >= limit:
                    break

        if len(ranked) >= limit:
            return ranked[:limit]

        used_urls = {str(row.get('source_url') or '').strip() for row in ranked}
        fallback_pool = [
            row for row in prepared
            if str(row.get('source_url') or '').strip() and str(row.get('source_url') or '').strip() not in used_urls
        ]
        fallback = _fallback_rank_rows_by_heading_title(
            rows=fallback_pool,
            heading=heading,
            limit=limit - len(ranked),
            tweet_text=tweet_text,
        )
        for row in fallback:
            candidate = dict(row)
            fast_score = int(candidate.get('_heading_title_fast_score', 0) or 0)
            candidate['_heading_title_llm_score'] = int(candidate.get('_heading_title_llm_score', 0) or fast_score)
            candidate['_heading_relevance_score'] = max(
                int(candidate.get('_heading_title_llm_score', 0) or 0),
                fast_score,
            )
            ranked.append(candidate)

        return ranked[:limit]


def _merge_regions(
    enrichment_regions: list[str] | None,
    title: str,
    summary: str | None,
    x_trend_phrase: str | None,
) -> list[str]:
    """Detect India/USA from content keywords and merge with enrichment regions."""
    text = f'{title} {summary or ""} {x_trend_phrase or ""}'.lower()

    india_markers = (
        'india', 'indian', 'delhi', 'mumbai', 'bangalore', 'bengaluru', 'chennai',
        'hyderabad', 'kolkata', 'pune', 'cbse', 'icse', 'nimhans', 'aiims',
    )
    usa_markers = (
        'united states', 'usa', 'u.s.', 'american', 'cdc', 'samhsa', 'nih',
        'new york', 'california', 'texas', 'florida', 'washington',
    )

    regions = set(enrichment_regions or [])
    if any(m in text for m in india_markers):
        regions.add('India')
    if any(m in text for m in usa_markers):
        regions.add('USA')

    # Default to International if no specific region detected
    if not regions:
        regions.add('International')

    return sorted(regions)


def _parse_feed(url: str) -> list[dict]:
    try:
        try:
            parsed = feedparser.parse(url, request_headers={'User-Agent': 'Mozilla/5.0'})
        except TypeError:
            parsed = feedparser.parse(url)
    except Exception as exc:
        logging.warning('Feed parse failed for %s: %s', url, exc)
        return []
    return _build_feed_rows(parsed, fallback_feed_url=url)


def _parse_feed_content(content: str, *, fallback_feed_url: str) -> list[dict]:
    try:
        parsed = feedparser.parse(content or '')
    except Exception as exc:
        logging.warning('Feed content parse failed for %s: %s', fallback_feed_url, exc)
        return []
    return _build_feed_rows(parsed, fallback_feed_url=fallback_feed_url)


def _build_feed_rows(parsed: object, *, fallback_feed_url: str) -> list[dict]:
    rows: list[dict] = []
    fallback_source_name = urlparse(fallback_feed_url).netloc
    entries = getattr(parsed, 'entries', []) or []
    for entry in entries[:150]:
        title = _clean_summary(entry.get('title', ''), limit=300)
        summary = _clean_summary(entry.get('summary', ''), limit=1500)
        combined = f'{title} {summary}'.lower()
        if not _is_healthcare_related(combined):
            continue
        source_name = _extract_feed_source_name(entry, fallback=fallback_source_name)
        source_url = _extract_feed_source_url(entry)
        rows.append(
            {
                'title': title,
                'source_url': source_url,
                'summary': summary,
                'source_name': source_name,
                'published_at': _parse_feed_datetime(entry),
                'keywords': [tag['term'] for tag in entry.get('tags', []) if isinstance(tag, dict) and tag.get('term')],
            }
        )
    return rows


def _extract_feed_source_name(entry: dict, *, fallback: str) -> str:
    source = entry.get('source') if isinstance(entry, dict) else None
    if isinstance(source, dict):
        title = str(source.get('title') or '').strip()
        if title:
            return title
    return fallback


def _extract_feed_source_url(entry: dict) -> str:
    if isinstance(entry, dict):
        link = str(entry.get('link') or '').strip()
        if link:
            return link
    source = entry.get('source') if isinstance(entry, dict) else None
    if isinstance(source, dict):
        href = str(source.get('href') or '').strip()
        if href:
            return href
    return str((entry.get('link') if isinstance(entry, dict) else '') or '').strip()


def _build_candidate_pool_for_heading(
    *,
    rows: list[dict],
    heading: str,
    tweet_text: str | None,
    limit: int,
) -> list[dict]:
    max_items = max(int(limit), 0)
    if max_items == 0:
        return []

    retrieval_terms = _retrieval_terms(
        heading=heading,
        tweet_text=tweet_text,
        max_terms=12,
    )
    retrieval_term_set = set(retrieval_terms)
    scored: list[dict] = []
    for item in rows:
        if not isinstance(item, dict):
            continue

        source_url = str(item.get('source_url') or '').strip()
        title = str(item.get('title') or '').strip()
        summary = str(item.get('summary') or '').strip()
        if not source_url or not title:
            continue

        heading_score = _heading_article_match_score(
            heading=heading,
            article_title=title,
            article_summary=summary,
            tweet_text=tweet_text,
        )
        combined_terms = set(_query_terms(f'{title} {summary}'))
        keyword_overlap = len(retrieval_term_set & combined_terms) if retrieval_term_set else 0
        if heading_score <= 0 and keyword_overlap <= 0:
            continue

        candidate = dict(item)
        keyword_score = keyword_overlap * 6
        focus_overlap = len(set(_focus_terms(f'{title} {summary}')) & retrieval_term_set) if retrieval_term_set else 0
        retrieval_score = heading_score + keyword_score + (focus_overlap * 3)
        candidate['_keyword_overlap'] = keyword_overlap
        candidate['_keyword_retrieval_score'] = retrieval_score
        candidate['_heading_title_fast_score'] = max(
            int(candidate.get('_heading_title_fast_score', 0) or 0),
            int(heading_score),
        )
        candidate['_heading_relevance_score'] = max(
            int(candidate.get('_heading_relevance_score', 0) or 0),
            int(candidate.get('_heading_title_fast_score', 0) or 0),
        )
        candidate['_child_related'] = bool(
            candidate.get('_child_related')
            or _is_child_mental_health_related(f'{title} {summary}')
        )
        scored.append(candidate)

    if not scored:
        return _fallback_rank_rows_by_heading_title(
            rows=rows,
            heading=heading,
            limit=max_items,
            tweet_text=tweet_text,
        )

    scored.sort(
        key=lambda row: (
            int(row.get('_keyword_retrieval_score', 0) or 0),
            int(row.get('_heading_title_fast_score', 0) or 0),
            _published_timestamp(row.get('published_at')),
            bool(row.get('_child_related')),
        ),
        reverse=True,
    )
    deduped = _dedupe_rows_by_source_url(scored)
    return [dict(row) for row in deduped[:max_items]]


def _retrieval_terms(*, heading: str, tweet_text: str | None, max_terms: int) -> list[str]:
    raw_terms: list[str] = []
    raw_terms.extend(_focus_terms(tweet_text))
    raw_terms.extend(_focus_terms(heading))
    if len(raw_terms) < 4:
        raw_terms.extend([term for term in _query_terms(tweet_text) if len(term) >= 4])
        raw_terms.extend([term for term in _query_terms(heading) if len(term) >= 4])

    deduped: list[str] = []
    seen: set[str] = set()
    for term in raw_terms:
        normalized = str(term or '').strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped.append(normalized)
        if len(deduped) >= max_terms:
            break
    return deduped


def _prefilter_rows_by_heading_title(
    *,
    rows: list[dict],
    heading: str,
    source_domain: str,
    limit: int,
    tweet_text: str | None = None,
) -> list[dict]:
    max_items = max(int(limit), 0)
    if max_items == 0:
        return []

    ranked: list[dict] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        source_url = str(item.get('source_url') or '').strip()
        title = str(item.get('title') or '').strip()
        if not source_url or not title:
            continue
        if not _domain_matches_allowed(source_url, source_domain):
            continue

        candidate = dict(item)
        fast_score = _heading_article_match_score(
            heading=heading,
            article_title=title,
            article_summary=str(item.get('summary') or ''),
            tweet_text=tweet_text,
        )
        candidate['_heading_title_fast_score'] = fast_score
        candidate['_heading_relevance_score'] = max(int(candidate.get('_heading_relevance_score', 0) or 0), fast_score)
        candidate['_child_related'] = _is_child_mental_health_related(f"{title} {str(item.get('summary') or '')}")
        ranked.append(candidate)

    ranked.sort(
        key=lambda row: (
            int(row.get('_heading_title_fast_score', 0) or 0),
            _published_timestamp(row.get('published_at')),
            bool(row.get('_child_related')),
        ),
        reverse=True,
    )
    return [dict(row) for row in ranked[:max_items]]


def _fallback_rank_rows_by_heading_title(
    *,
    rows: list[dict],
    heading: str,
    limit: int,
    tweet_text: str | None = None,
) -> list[dict]:
    max_items = max(int(limit), 0)
    if max_items == 0:
        return []

    scored: list[dict] = []
    seen_urls: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            continue
        source_url = str(item.get('source_url') or '').strip()
        title = str(item.get('title') or '').strip()
        if not source_url or not title or source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        candidate = dict(item)
        fast_score = _heading_article_match_score(
            heading=heading,
            article_title=title,
            article_summary=str(item.get('summary') or ''),
            tweet_text=tweet_text,
        )
        candidate['_heading_title_fast_score'] = int(candidate.get('_heading_title_fast_score', 0) or fast_score)
        candidate['_heading_relevance_score'] = max(
            int(candidate.get('_heading_relevance_score', 0) or 0),
            int(candidate.get('_heading_title_fast_score', 0) or 0),
        )
        candidate['_child_related'] = bool(
            candidate.get('_child_related')
            or _is_child_mental_health_related(f"{title} {str(item.get('summary') or '')}")
        )
        scored.append(candidate)

    scored.sort(
        key=lambda row: (
            int(row.get('_heading_title_fast_score', 0) or 0),
            _published_timestamp(row.get('published_at')),
            bool(row.get('_child_related')),
        ),
        reverse=True,
    )
    return [dict(row) for row in scored[:max_items]]


def _dedupe_rows_by_source_url(rows: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen_urls: set[str] = set()
    for item in rows:
        if not isinstance(item, dict):
            continue
        source_url = str(item.get('source_url') or '').strip()
        if not source_url or source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        deduped.append(dict(item))
    return deduped


def _heading_title_fast_score(*, heading: str, article_title: str) -> int:
    return _heading_article_match_score(
        heading=heading,
        article_title=article_title,
        article_summary='',
        tweet_text=None,
    )


def _heading_article_match_score(
    *,
    heading: str,
    article_title: str,
    article_summary: str | None = None,
    tweet_text: str | None = None,
) -> int:
    heading_text = str(heading or '').strip().lower()
    title_text = str(article_title or '').strip().lower()
    summary_text = str(article_summary or '').strip().lower()
    tweet_context = str(tweet_text or '').strip().lower()
    if not heading_text or not title_text:
        return 0

    heading_terms = set(_query_terms(heading_text))
    title_terms = set(_query_terms(title_text))
    summary_terms = set(_query_terms(summary_text))
    if not heading_terms or not title_terms:
        return 0

    overlap_title = heading_terms & title_terms
    overlap_summary = heading_terms & summary_terms
    if not overlap_title and not overlap_summary:
        return 0

    score = (len(overlap_title) * 8) + (len(overlap_summary) * 2)
    if heading_text in title_text:
        score += 12
    if title_text in heading_text:
        score += 8

    heading_focus_terms = set(_focus_terms(heading_text))
    summary_focus_terms = set(_focus_terms(summary_text))
    score += len((heading_focus_terms & title_terms)) * 4
    score += len((heading_focus_terms & summary_focus_terms)) * 2

    if tweet_context:
        tweet_terms = set(_query_terms(tweet_context))
        tweet_focus_terms = set(_focus_terms(tweet_context))
        score += len((tweet_terms & title_terms)) * 2
        score += len((tweet_terms & summary_terms))
        anchor_terms = heading_focus_terms | tweet_focus_terms
        if anchor_terms:
            anchor_overlap = (title_terms | summary_terms) & anchor_terms
            if anchor_overlap:
                score += len(anchor_overlap) * 4
            else:
                score = max(score - 10, 0)

    if _is_child_mental_health_related(f'{heading_text} {title_text} {summary_text}'):
        score += 4

    return max(score, 0)


def _passes_heading_relevance_gate(*, item: dict, heading: str, tweet_text: str | None) -> bool:
    minimum_score = max(int(settings.x_heading_min_relevance_score or 0), 1)
    relevance_score = int(item.get('_heading_relevance_score', 0) or 0)
    if relevance_score < minimum_score:
        return False

    anchor_terms = set(_focus_terms(heading))
    if tweet_text:
        anchor_terms.update(_focus_terms(tweet_text))
    if not anchor_terms:
        return True

    article_text = f"{str(item.get('title') or '').lower()} {str(item.get('summary') or '').lower()}"
    return any(term in article_text for term in anchor_terms)


def _focus_terms(text: str | None) -> list[str]:
    terms = _query_terms(text)
    return [term for term in terms if term not in GENERIC_HEADING_TERMS and len(term) >= 4]


def _rank_by_relevance(rows: list[dict], query: str | None, limit: int) -> list[dict]:
    if not query or not rows:
        return rows[:limit]
    terms = _query_terms(query)
    if not terms:
        return rows[:limit]
    scored = sorted(rows, key=lambda r: _relevance_score(r, terms), reverse=True)
    return scored[:limit]


def _relevance_score(item: dict, terms: list[str]) -> int:
    title = str(item.get('title') or '').lower()
    summary = str(item.get('summary') or '').lower()
    score = 0
    for term in terms:
        if term in title:
            score += 3  # title match worth more
        if term in summary:
            score += 1
    return score


def _parse_feed_datetime(entry: dict) -> datetime | None:
    published = entry.get('published_parsed') or entry.get('updated_parsed')
    if not published:
        return None
    return datetime(*published[:6], tzinfo=timezone.utc)


def _published_timestamp(value: object) -> float:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = _parse_iso_datetime(value)
        if not parsed:
            return 0.0
    else:
        return 0.0

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None


def _keywords_from_title(title: str) -> list[str]:
    terms = [token.strip(',.!?').lower() for token in title.split()]
    return [token for token in terms if len(token) > 4][:6]


def _query_terms(query: str | None) -> list[str]:
    if not query:
        return []
    terms = [token.lower().strip('\'"()[]{}.,!?;:') for token in re.split(r'[\s,]+', query) if token.strip()]
    stopwords = {
        'or',
        'and',
        'the',
        'a',
        'an',
        'of',
        'for',
        'to',
        'in',
        'on',
        'with',
        'at',
        'by',
        'from',
    }
    return [term for term in terms if term and term not in stopwords]


def _healthcare_scoped_query(query: str) -> str:
    health_scope = '("mental health" OR anxiety OR depression OR stress OR ADHD OR autism OR therapy OR counseling OR "child psychology" OR "behavioral health" OR wellbeing OR trauma OR suicide OR bullying OR "eating disorder")'
    raw_query = query.strip()
    if not raw_query:
        return health_scope
    return f'({raw_query}) AND {health_scope}'


def _compose_x_discovery_query(query: str | None) -> str:
    raw_query = _normalize_x_query_whitespace(query)
    if not raw_query:
        return _normalize_x_query_whitespace(settings.x_topic_seed_query)
    # X API v2 uses spaces for implicit AND — no AND keyword allowed
    child_mental_scope = '((child OR children OR teen OR adolescent OR youth OR school OR parenting) ("mental health" OR anxiety OR depression OR stress OR therapy OR ADHD OR autism OR trauma))'
    return f'({raw_query}) {child_mental_scope} lang:en -is:retweet'


def _strip_pro_only_operators(query: str) -> str:
    """Remove operators that require X Pro API tier (min_faves, min_retweets, place_country, has:geo)."""
    cleaned = str(query or '').strip()
    # Remove min_faves / min_retweets / min_replies
    cleaned = re.sub(r'\bmin_faves:\d+\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bmin_retweets:\d+\b', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bmin_replies:\d+\b', '', cleaned, flags=re.IGNORECASE)
    # Remove place_country and has:geo operators (standalone or inside parens)
    cleaned = re.sub(r'\(\s*place_country:[^)]+\)', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bplace_country:\S+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\bhas:geo\b', '', cleaned, flags=re.IGNORECASE)
    # Tidy up dangling ANDs and whitespace
    cleaned = re.sub(r'AND\s+AND', 'AND', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'^\s*AND\s+', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+AND\s*$', '', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'\(\s*\)', '', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _relax_x_discovery_query(query: str) -> str:
    relaxed = _strip_pro_only_operators(query)
    return relaxed


def _normalize_x_query_whitespace(query: str | None) -> str:
    normalized = re.sub(r'\s+', ' ', str(query or ''))
    return normalized.strip()


def _dedupe_tweets_by_id_and_text(rows: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen_ids: set[str] = set()
    seen_texts: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        tweet_id = str(row.get('id') or '').strip()
        text = str(row.get('text') or '').strip().lower()
        if tweet_id and tweet_id in seen_ids:
            continue
        if text and text in seen_texts:
            continue
        if tweet_id:
            seen_ids.add(tweet_id)
        if text:
            seen_texts.add(text)
        deduped.append(row)
    return deduped


def _tweet_created_timestamp(value: object) -> float:
    parsed = _parse_twitter_datetime(value)
    if not parsed:
        return 0.0
    return parsed.timestamp()


def _select_top_recent_engaging_tweets(candidate_tweets: list[dict], limit: int = 5) -> list[dict]:
    minimum_score = max(float(settings.x_topic_min_raw_engagement_score or 0.0), 0.0)
    qualified = [
        row for row in candidate_tweets
        if isinstance(row, dict)
        and float(row.get('engagement_score', 0.0) or 0.0) >= minimum_score
    ]
    if not qualified:
        return []

    ranked = sorted(
        qualified,
        key=lambda tweet: (
            float(tweet.get('engagement_score', 0.0) or 0.0),
            int(tweet.get('like_count', 0) or 0),
            int(tweet.get('reply_count', 0) or 0),
            int(tweet.get('retweet_count', 0) or 0),
            int(tweet.get('quote_count', 0) or 0),
            _tweet_created_timestamp(tweet.get('created_at')),
        ),
        reverse=True,
    )
    return ranked[: max(limit, 0)]


def _parse_twitter_datetime(value: object) -> datetime | None:
    raw = str(value or '').strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def _extract_tweet_place_country(*, tweet: dict, places_by_id: dict[str, dict]) -> str:
    if not isinstance(tweet, dict):
        return ''
    geo = tweet.get('geo')
    if not isinstance(geo, dict):
        return ''
    place_id = str(geo.get('place_id') or '').strip()
    if not place_id:
        return ''
    place = places_by_id.get(place_id) or {}
    country_code = str(place.get('country_code') or '').strip().upper()
    if country_code in {'IN', 'US'}:
        return country_code
    return country_code


def _recency_weight(created_at: datetime | None) -> float:
    if not created_at:
        return 1.0
    age_hours = max((datetime.now(timezone.utc) - created_at).total_seconds() / 3600.0, 0.0)
    # Decay gradually: newer tweets score higher, but older high-engagement tweets still contribute.
    return 1.0 + math.exp(-age_hours / 18.0)


def _matches_query(*, text: str, query: str) -> bool:
    terms = _query_terms(query)
    if not terms:
        return False
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _is_healthcare_related(text: str) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in HEALTHCARE_TOPIC_TERMS)


def _is_child_mental_health_related(text: str) -> bool:
    normalized = text.lower()
    has_child = any(term in normalized for term in CHILD_TOPIC_TERMS)
    has_mental = any(term in normalized for term in MENTAL_HEALTH_TERMS)
    return has_child and has_mental


def _engagement_score(metrics: dict) -> float:
    like_count = int(metrics.get('like_count', 0) or 0)
    reply_count = int(metrics.get('reply_count', 0) or 0)
    retweet_count = int(metrics.get('retweet_count', 0) or 0)
    quote_count = int(metrics.get('quote_count', 0) or 0)
    return like_count + (2.0 * reply_count) + (1.5 * retweet_count) + (2.0 * quote_count)


def _extract_followers_count(user: dict) -> int:
    metrics = (user.get('public_metrics') if isinstance(user, dict) else None) or {}
    return int(metrics.get('followers_count', 0) or 0)


def _extract_author_tweet_count(user: dict) -> int:
    metrics = (user.get('public_metrics') if isinstance(user, dict) else None) or {}
    return int(metrics.get('tweet_count', 0) or 0)


def _extract_account_age_days(user: dict) -> float:
    created_at = _parse_twitter_datetime((user or {}).get('created_at'))
    if not created_at:
        return 365.0
    return max((datetime.now(timezone.utc) - created_at).total_seconds() / 86400.0, 0.0)


def _extract_hashtag_count(tweet: dict) -> int:
    entities = tweet.get('entities') if isinstance(tweet, dict) else None
    if isinstance(entities, dict):
        hashtags = entities.get('hashtags') or []
        if isinstance(hashtags, list):
            return len(hashtags)
    text = str((tweet or {}).get('text') or '')
    return len(re.findall(r'#\w+', text))


def _normalize_engagement_score(raw_engagement: float, followers_count: int) -> float:
    # Dampens large-account dominance while preserving signal.
    follower_baseline = max(float(followers_count), 50.0)
    return raw_engagement / math.sqrt(follower_baseline)


def _engagement_velocity(raw_engagement: float, created_at: datetime | None) -> float:
    if not created_at:
        return raw_engagement / 24.0
    age_hours = max((datetime.now(timezone.utc) - created_at).total_seconds() / 3600.0, 1.0)
    return raw_engagement / age_hours


def _quality_penalty_multiplier(
    *,
    account_age_days: float,
    followers_count: int,
    tweet_count_total: int,
    hashtag_count: int,
) -> float:
    penalty = 1.0

    if account_age_days < 30.0:
        penalty *= 0.75

    posting_rate_per_day = tweet_count_total / max(account_age_days, 1.0)
    if followers_count < 50 and posting_rate_per_day > 40.0:
        penalty *= 0.7

    if hashtag_count > 6:
        penalty *= 0.8

    return max(penalty, 0.4)


def _extract_topic_from_tweet(*, text: str, entities: dict | None) -> str:
    # 1. Check hashtags for child mental health relevance
    hashtags = []
    if isinstance(entities, dict):
        for row in entities.get('hashtags') or []:
            if not isinstance(row, dict):
                continue
            tag = str(row.get('tag') or '').strip().lower().replace('_', ' ')
            if tag:
                hashtags.append(tag)

    for tag in hashtags:
        if _is_child_mental_health_related(tag):
            return tag

    # Combine relevant hashtags
    mental_tags = [t for t in hashtags if any(m in t for m in MENTAL_HEALTH_TERMS)]
    child_tags = [t for t in hashtags if any(c in t for c in CHILD_TOPIC_TERMS)]
    if mental_tags:
        return mental_tags[0]
    if child_tags:
        return child_tags[0]

    # 2. Extract meaningful phrases from tweet text
    cleaned = re.sub(r'https?://\S+', ' ', text.lower())
    cleaned = re.sub(r'[@#]\w+', ' ', cleaned)
    cleaned = re.sub(r'[^a-z\s\-]', ' ', cleaned)
    words = cleaned.split()

    # Build bigrams/trigrams and look for mental health + child phrases
    mental_keywords = set(MENTAL_HEALTH_TERMS) | {'mental', 'health', 'anxiety', 'depression', 'stress', 'adhd', 'autism', 'trauma', 'therapy', 'suicide', 'bullying'}
    child_keywords = set(CHILD_TOPIC_TERMS) | {'child', 'children', 'teen', 'teens', 'kids', 'youth', 'student', 'school', 'adolescent'}

    # Find the core mental health phrase in the tweet
    found_mental = [w for w in words if w in mental_keywords]
    found_child = [w for w in words if w in child_keywords]

    if found_child and found_mental:
        # Combine the most relevant child + mental health term
        return f'{found_child[0]} {found_mental[0]}'
    elif found_mental:
        return found_mental[0]

    return ''


def _dedupe_entries(entries: list[dict]) -> list[dict]:
    unique: list[dict] = []
    seen_urls: set[str] = set()
    for row in entries:
        source_url = str(row.get('source_url') or '').strip()
        if not source_url or source_url in seen_urls:
            continue
        seen_urls.add(source_url)
        unique.append(row)
    return unique


def _is_x_or_twitter_url(url: str) -> bool:
    host = urlparse(url).netloc.lower().strip()
    if host.startswith('www.'):
        host = host[4:]
    return host in {'x.com', 'twitter.com'} or host.endswith('.x.com') or host.endswith('.twitter.com')


def _clean_summary(value: str, *, limit: int) -> str:
    text = html.unescape(value or '')
    text = re.sub(r'<[^>]*>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text[:limit]


def _sanitize_heading(raw: str) -> str:
    text = str(raw or '').strip()
    if not text:
        return ''

    text = text.splitlines()[0].strip()
    text = re.sub(r'^[-*\d.)\s]+', '', text)
    text = text.strip('"\'` ')
    text = re.sub(r'https?://\S+', ' ', text)
    text = re.sub(r'[@#]\w+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.rstrip('.,;:!?')

    word_count = len(text.split())
    if word_count < 4:
        return ''
    if len(text) > 180:
        text = text[:180].rsplit(' ', 1)[0].strip()
    return text


def _fallback_heading_from_tweet_text(tweet_text: str) -> str:
    cleaned = re.sub(r'https?://\S+', ' ', tweet_text or '')
    cleaned = re.sub(r'[@#]\w+', ' ', cleaned)
    cleaned = re.sub(r'[^A-Za-z0-9\s\-]', ' ', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    if not cleaned:
        return 'Child and adolescent mental health trend signal from social media'

    words = cleaned.split()
    if len(words) > 14:
        words = words[:14]
    heading = ' '.join(words).strip()
    if len(heading.split()) < 4:
        return 'Child and adolescent mental health trend signal from social media'
    return heading


def _domain_matches_allowed(url: str, allowed_domain: str) -> bool:
    host = urlparse(url).netloc.lower().strip()
    if host.startswith('www.'):
        host = host[4:]
    expected = allowed_domain.lower().strip()
    return host == expected or host.endswith(f'.{expected}')


def _heading_relevance_score(*, item: dict, heading: str) -> int:
    terms = _query_terms(heading)
    if not terms:
        return 0
    title = str(item.get('title') or '').lower()
    summary = str(item.get('summary') or '').lower()

    score = 0
    for term in terms:
        if term in title:
            score += 2
        elif term in summary:
            score += 1
    return score


def _apply_llm_headings_to_trending_tweets(trending_tweets: list[dict], heading_queries: list[dict]) -> list[dict]:
    if not trending_tweets:
        return []

    by_sample_text: dict[str, str] = {}
    for row in heading_queries:
        if not isinstance(row, dict):
            continue
        heading = str(row.get('query') or '').strip()
        sample_text = str(row.get('sample_text') or '').strip()
        if heading and sample_text:
            by_sample_text[sample_text] = heading

    normalized: list[dict] = []
    for tweet in trending_tweets:
        if not isinstance(tweet, dict):
            continue
        cloned = dict(tweet)
        sample_text = str(cloned.get('sample_text') or '').strip()
        heading = by_sample_text.get(sample_text)
        if heading:
            cloned['topic'] = heading
        normalized.append(cloned)
    return normalized
