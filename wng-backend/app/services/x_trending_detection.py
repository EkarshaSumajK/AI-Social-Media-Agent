from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from typing import Any

import requests

X_RECENT_SEARCH_URL = 'https://api.twitter.com/2/tweets/search/recent'
DEFAULT_QUERY = """
(
    "child mental health"
    OR "teen mental health"
    OR "student mental health"
    OR (
        (child OR teen OR adolescent OR student)
        AND
        ("anxiety" OR "depression" OR "ADHD" OR "autism" OR "trauma")
    )
)
AND (place_country:IN OR place_country:US)
AND lang:en
AND -is:retweet
AND min_faves:25
"""
DEFAULT_TWEET_FIELDS = 'created_at,public_metrics,text'
DEFAULT_TARGET_TWEETS = 100
MAX_RESULTS_PER_PAGE = 100
MAX_RETRIES = 3
REQUEST_TIMEOUT_SECONDS = 20

URL_PATTERN = re.compile(r'https?://\S+', flags=re.IGNORECASE)
HASHTAG_PATTERN = re.compile(r'#[\w_]+', flags=re.IGNORECASE)
USERNAME_PATTERN = re.compile(r'@[\w_]+', flags=re.IGNORECASE)
TRAILING_PUNCT_PATTERN = re.compile(r'[.!?;:,\-\s]+$')
NON_WORD_PATTERN = re.compile(r"[^a-zA-Z\s']+")


class XTrendingError(Exception):
    pass


@dataclass(frozen=True)
class ScoredTweet:
    text: str
    score: float
    likes: int
    retweets: int
    replies: int


def _get_bearer_token() -> str:
    token = (os.getenv('X_BEARER_TOKEN') or '').strip()
    if not token:
        raise XTrendingError('Missing X_BEARER_TOKEN environment variable.')
    return token


def _is_links_only(text: str) -> bool:
    without_urls = URL_PATTERN.sub(' ', text or '')
    return not re.search(r'\w', without_urls)


def _word_count(text: str) -> int:
    no_urls = URL_PATTERN.sub(' ', text or '')
    return len(re.findall(r"[A-Za-z']+", no_urls))


def _normalize_text_for_dedupe(text: str) -> str:
    lowered = (text or '').strip().lower()
    lowered = URL_PATTERN.sub(' ', lowered)
    lowered = re.sub(r'\s+', ' ', lowered)
    return lowered.strip()


def _extract_metrics(tweet: dict[str, Any]) -> tuple[int, int, int]:
    metrics = tweet.get('public_metrics') or {}
    likes = int(metrics.get('like_count', 0) or 0)
    retweets = int(metrics.get('retweet_count', 0) or 0)
    replies = int(metrics.get('reply_count', 0) or 0)
    return likes, retweets, replies


def _engagement_score(likes: int, retweets: int, replies: int) -> float:
    return likes + (2 * retweets) + (1.5 * replies)


def _request_recent_page(
    session: requests.Session,
    *,
    bearer_token: str,
    query: str,
    next_token: str | None,
    max_results: int,
) -> dict[str, Any]:
    headers = {'Authorization': f'Bearer {bearer_token}'}
    params: dict[str, Any] = {
        'query': query,
        'max_results': max_results,
        'sort_order': 'recency',
        'tweet.fields': DEFAULT_TWEET_FIELDS,
    }
    if next_token:
        params['next_token'] = next_token

    for attempt in range(MAX_RETRIES):
        response = session.get(
            X_RECENT_SEARCH_URL,
            headers=headers,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code == 429:
            reset_ts = response.headers.get('x-rate-limit-reset')
            wait_seconds = 0
            if reset_ts and reset_ts.isdigit():
                wait_seconds = max(int(reset_ts) - int(time.time()), 1)
            else:
                wait_seconds = 2 ** (attempt + 1)
            time.sleep(wait_seconds)
            continue

        if 500 <= response.status_code < 600:
            time.sleep(2 ** (attempt + 1))
            continue

        if response.status_code >= 400:
            try:
                details = response.json()
            except ValueError:
                details = {'message': response.text}
            raise XTrendingError(f'X API request failed: {details}')

        try:
            return response.json()
        except ValueError as exc:
            raise XTrendingError('Invalid JSON received from X API.') from exc

    raise XTrendingError('X API request failed after retries due to rate limit or transient errors.')


def _fetch_recent_tweets(query: str, target_count: int = DEFAULT_TARGET_TWEETS) -> list[dict[str, Any]]:
    bearer_token = _get_bearer_token()
    tweets: list[dict[str, Any]] = []
    next_token: str | None = None

    with requests.Session() as session:
        while len(tweets) < target_count:
            page = _request_recent_page(
                session,
                bearer_token=bearer_token,
                query=query,
                next_token=next_token,
                max_results=min(MAX_RESULTS_PER_PAGE, target_count - len(tweets)),
            )
            rows = page.get('data') or []
            if not isinstance(rows, list):
                break
            tweets.extend(row for row in rows if isinstance(row, dict))

            meta = page.get('meta') or {}
            next_token = meta.get('next_token')
            if not next_token:
                break

    return tweets[:target_count]


def _clean_tweets(tweets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    cleaned: list[dict[str, Any]] = []

    for tweet in tweets:
        text = str(tweet.get('text') or '').strip()
        if not text:
            continue
        if _word_count(text) < 6:
            continue
        if _is_links_only(text):
            continue

        normalized = _normalize_text_for_dedupe(text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        cleaned.append(tweet)

    return cleaned


def _score_and_rank_tweets(cleaned_tweets: list[dict[str, Any]], top_n: int = 15) -> list[ScoredTweet]:
    ranked: list[ScoredTweet] = []

    for tweet in cleaned_tweets:
        text = str(tweet.get('text') or '').strip()
        likes, retweets, replies = _extract_metrics(tweet)
        score = _engagement_score(likes, retweets, replies)
        ranked.append(
            ScoredTweet(
                text=text,
                score=score,
                likes=likes,
                retweets=retweets,
                replies=replies,
            )
        )

    ranked.sort(key=lambda row: row.score, reverse=True)
    return ranked[:top_n]


def _prepare_text_for_phrase_generation(text: str) -> str:
    prepared = URL_PATTERN.sub(' ', text or '')
    prepared = USERNAME_PATTERN.sub(' ', prepared)
    prepared = HASHTAG_PATTERN.sub(' ', prepared)
    prepared = re.sub(r'\s+', ' ', prepared)
    return prepared.strip()


def _normalize_phrase(phrase: str) -> str:
    candidate = URL_PATTERN.sub(' ', phrase or '')
    candidate = USERNAME_PATTERN.sub(' ', candidate)
    candidate = HASHTAG_PATTERN.sub(' ', candidate)
    candidate = NON_WORD_PATTERN.sub(' ', candidate)
    candidate = re.sub(r'\s+', ' ', candidate).strip()
    candidate = TRAILING_PUNCT_PATTERN.sub('', candidate)

    words = candidate.split()
    if len(words) > 12:
        words = words[:12]
    if len(words) < 6:
        return ''
    return ' '.join(words)


def _fallback_phrase_from_text(text: str) -> str:
    candidate = NON_WORD_PATTERN.sub(' ', text or '')
    candidate = re.sub(r'\s+', ' ', candidate).strip()
    words = candidate.split()
    if len(words) < 6:
        return ''
    return ' '.join(words[:12])


def _generate_research_phrases(top_tweets: list[ScoredTweet]) -> list[str]:
    phrase_generator = globals().get('generate_phrase')
    if not callable(phrase_generator):
        raise XTrendingError('Missing external generate_phrase(text: str) function.')

    unique_phrases: list[str] = []
    seen: set[str] = set()

    for tweet in top_tweets:
        source_text = _prepare_text_for_phrase_generation(tweet.text)
        if not source_text:
            continue

        generated = phrase_generator(source_text)
        normalized = _normalize_phrase(str(generated or ''))
        if not normalized:
            normalized = _fallback_phrase_from_text(source_text)
        if not normalized:
            continue

        key = normalized.lower()
        if key in seen:
            continue

        seen.add(key)
        unique_phrases.append(normalized)

    return unique_phrases


def get_trending_topics(query: str) -> dict:
    effective_query = (query or '').strip() or DEFAULT_QUERY

    try:
        recent_tweets = _fetch_recent_tweets(effective_query, target_count=DEFAULT_TARGET_TWEETS)
        cleaned_tweets = _clean_tweets(recent_tweets)
        top_tweets = _score_and_rank_tweets(cleaned_tweets, top_n=15)
        topics = _generate_research_phrases(top_tweets)
    except XTrendingError:
        return {'topics': [], 'top_posts': []}
    except requests.RequestException:
        return {'topics': [], 'top_posts': []}

    top_posts = [
        {
            'text': tweet.text,
            'score': round(tweet.score, 2),
            'likes': tweet.likes,
            'retweets': tweet.retweets,
            'replies': tweet.replies,
        }
        for tweet in top_tweets
    ]

    return {
        'topics': topics,
        'top_posts': top_posts,
    }
