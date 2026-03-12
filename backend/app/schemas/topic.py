from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_url: str
    source_name: str | None = None
    summary: str | None = None
    relevance_label: str
    relevance_score: int
    age_group: str
    topic_type: str
    mental_health_specific: bool
    screening_reason: str | None = None
    trust_score: int
    is_trending: bool
    x_engagement_score: float | None = None
    x_tweet_count: int | None = None
    x_trend_phrase: str | None = None
    trend_regions: list[str] | None = None
    public_concerns: list[str] | None = None
    trend_statements: list[str] | None = None
    trend_sentiment: str | None = None
    statistics: list[str] | None = None
    status: str
    platform: str
    topic_category: str | None = None
    region: str = 'global'
    created_at: datetime


class TrendingTweetItem(BaseModel):
    id: str = ''
    author_id: str = ''
    created_at: str = ''
    text: str = ''
    topic: str
    engagement_score: float
    tweet_count: int
    like_count: int = 0
    reply_count: int = 0
    retweet_count: int = 0
    quote_count: int = 0
    public_metrics: dict[str, int] | None = None
    raw_tweet: dict[str, Any] | None = None
    sample_text: str = ''


class CollectTopicsRequest(BaseModel):
    query: str | None = None


class CollectTopicsResponse(BaseModel):
    fetched: int
    x_topics_found: int = 0
    x_preferred_country: str = 'US'
    x_india_tweets: int = 0
    x_us_tweets: int = 0
    article_heading_queries: list[str] = []
    articles_per_heading_target: int = 3
    heading_selection: list[dict[str, Any]] = []
    stored: int
    skipped: int
    duplicate_rejected: int
    screened_out: int = 0
    trust_rejected: int = 0
    replaced_existing: int = 0
    trending_tweets: list[TrendingTweetItem] = []


class GenerateDraftRequest(BaseModel):
    run_async: bool = True


class GenerateDraftFromUrlRequest(BaseModel):
    url: str
    run_async: bool = True


class GenerateDraftResponse(BaseModel):
    status: str
    message: str
    article_id: int | None = None
    task_id: str | None = None


class DraftTaskStatusResponse(BaseModel):
    task_id: str
    state: str
    status: str
    message: str
    article_id: int | None = None
    progress: int | None = None
    stage: str | None = None
