import json
from functools import lru_cache
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / '.env'),
        env_file_encoding='utf-8',
        extra='ignore',
    )

    # ── App ─────────────────────────────────────────────────────────────
    project_name: str = 'WNG Content Platform'
    environment: str = 'development'
    api_v1_prefix: str = '/api/v1'

    # ── Database & Redis (from .env) ───────────────────────────────────
    database_url_dashboard: str
    database_schema: str = 'wng_content'
    redis_url: str

    # ── JWT ────────────────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = 'HS256'
    access_token_expire_minutes: int = 720
    jwt_cookie_name: str = 'wng_access_token'
    jwt_cookie_secure: bool = False
    jwt_cookie_samesite: str = 'lax'

    # ── Admin (from .env) ────────────────────────────────────────────
    admin_email: str
    admin_password: str
    admin_full_name: str = 'Platform Reviewer'

    clinic_name: str = 'Horizon Therapy Centre'

    # ── LLM (secrets in .env) ─────────────────────────────────────────
    llm_api_key: str | None = None
    firecrawl_api_key: str | None = None
    llm_model: str = 'gpt-4o-mini'
    llm_screening_model: str = 'gpt-4o-mini'
    llm_quality_model: str = 'gpt-4o-mini'
    embeddings_model: str = 'text-embedding-3-small'
    prompts_dir: str = str(PROJECT_ROOT / 'prompts')
    trusted_sources_file: str = str(PROJECT_ROOT / 'trusted_sources.yaml')

    # ── News & RSS ────────────────────────────────────────────────────
    news_api_key: str | None = None
    newsapi_key: str | None = None
    news_api_sources: str = 'reuters,associated-press,bbc-news,the-guardian-uk,medical-news-today'
    serpapi_key: str | None = None
    news_api_india_domains: str = 'thehindu.com,indianexpress.com,hindustantimes.com,timesofindia.indiatimes.com,livemint.com'
    rss_feeds: list[str] = [
        'https://www.who.int/rss-feeds/news-english.xml',
        'https://tools.cdc.gov/api/v2/resources/media/132608.rss',
        'https://www.nih.gov/news-releases/feed.xml',
        'https://www.mohfw.gov.in/rssfeed.php',
    ]

    duplicate_similarity_threshold: float = 0.85
    duplicate_generation_similarity_threshold: float = 0.9

    # ── Social tokens (secrets in .env) ───────────────────────────────
    facebook_page_id: str | None = None
    instagram_business_id: str | None = None
    instagram_image_url: str | None = None
    meta_access_token: str | None = None
    linkedin_organization_id: str | None = None
    linkedin_access_token: str | None = None
    x_bearer_token: str | None = None

    # ── OAuth 2.0 credentials (secrets in .env) ──────────────────────
    linkedin_client_id: str | None = None
    linkedin_client_secret: str | None = None
    twitter_client_id: str | None = None
    twitter_client_secret: str | None = None
    facebook_app_id: str | None = None
    facebook_app_secret: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    token_encryption_key: str | None = None

    # ── X / Twitter topic detection ───────────────────────────────────
    x_topic_seed_query: str = '("child mental health" OR "teen mental health" OR "student mental health" OR (children anxiety) OR (teen depression) OR (adolescent ADHD) OR (student trauma) OR (kids "mental health") OR (India "mental health") OR (CBSE students anxiety) OR (India teen depression) OR (school mental health India)) lang:en -is:retweet'
    x_topic_max_results: int = 25
    x_topic_min_engagement_score: float = 5.0
    x_topic_min_raw_engagement_score: float = 5.0
    x_topic_min_velocity_per_hour: float = 0.5
    x_topic_india_rank_boost: float = 1.5
    x_topic_india_min_tweets: int = 0
    x_topic_limit: int = 5
    x_articles_per_topic: int = 3
    x_heading_min_relevance_score: int = 1
    x_topic_min_posts_per_topic: int = 1

    # ── Notifications (secrets in .env) ───────────────────────────────
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    reviewer_notification_email: str | None = None

    # ── Cloudinary (secrets in .env) ──────────────────────────────────
    cloudinary_cloud_name: str | None = None
    cloudinary_api_key: str | None = None
    cloudinary_api_secret: str | None = None

    # ── Frontend & Monitoring ─────────────────────────────────────────
    frontend_url: str = 'http://localhost:3000'
    oauth_callback_base_url: str = 'http://127.0.0.1:8000'
    sentry_dsn: str | None = None

    service_links: dict[str, str] = {
        'Therapy Services': 'https://example.com/services/therapy',
        'Counseling Programs': 'https://example.com/services/counseling',
        'Corporate Wellness': 'https://example.com/services/corporate-wellness',
        'Book Consultation': 'https://example.com/contact',
    }

    @field_validator('rss_feeds', mode='before')
    @classmethod
    def parse_rss_feeds(cls, value: object) -> list[str]:
        if isinstance(value, str):
            return [v.strip() for v in value.split(',') if v.strip()]
        if isinstance(value, list):
            return [str(v) for v in value]
        return []

    @field_validator('service_links', mode='before')
    @classmethod
    def parse_service_links(cls, value: object) -> dict[str, str]:
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return {str(k): str(v) for k, v in parsed.items()}
            except json.JSONDecodeError:
                return {}
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        return {}

    @field_validator('jwt_cookie_samesite', mode='before')
    @classmethod
    def normalize_cookie_samesite(cls, value: object) -> str:
        normalized = str(value or 'lax').strip().lower()
        if normalized not in {'lax', 'strict', 'none'}:
            return 'lax'
        return normalized


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
