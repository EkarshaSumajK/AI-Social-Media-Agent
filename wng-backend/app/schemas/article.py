from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SocialPostOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: str
    caption: str
    edited_caption: str | None = None
    status: str
    external_post_id: str | None = None
    error_message: str | None = None
    image_url: str | None = None
    posted_at: datetime | None = None


class TopicMiniOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    source_url: str
    source_name: str | None = None
    relevance_score: int | None = None
    trust_score: int | None = None
    is_trending: bool | None = None
    x_engagement_score: float | None = None
    x_tweet_count: int | None = None
    x_trend_phrase: str | None = None
    trend_regions: list[str] | None = None
    statistics: list[str] | None = None


class ArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    status: str
    seo_title: str
    meta_description: str
    keywords: list[str] | None = None
    content_html: str
    issue_summary: str
    why_it_matters: str
    mental_health_implications: str
    professional_insight: str
    how_services_help: str
    call_to_action: str
    disclaimer_text: str
    readability_score: float | None = None
    ai_generated_probability: float | None = None
    source_similarity_score: float | None = None
    structure_valid: bool
    quality_notes: list[str] | None = None
    source_url: str
    platform: str
    slug: str | None = None
    virality_score: float | None = None
    clarity_score: float | None = None
    hook_strength_score: float | None = None
    conversion_score: float | None = None
    created_by: int | None = None
    approved_by: int | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None
    published_url: str | None = None
    requires_review: bool = True
    created_at: datetime
    updated_at: datetime
    topic: TopicMiniOut | None = None
    social_posts: list[SocialPostOut] = Field(default_factory=list)


class DraftUpdateRequest(BaseModel):
    content_html: str
    seo_title: str
    meta_description: str
    keywords: list[str]
    issue_summary: str
    why_it_matters: str
    mental_health_implications: str
    professional_insight: str
    how_services_help: str
    call_to_action: str
    social_posts: dict[str, str]


class SocialPublishResponse(BaseModel):
    article_id: int
    outcomes: dict[str, str]


class MessageResponse(BaseModel):
    message: str


class PublishedArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    slug: str | None = None
    seo_title: str
    meta_description: str
    keywords: list[str] | None = None
    content_html: str
    platform: str
    published_at: datetime | None = None
    published_url: str | None = None


class ParaphraseRequest(BaseModel):
    content: str
    style: str = 'professional'
    tone: str = 'supportive and clear'


class ParaphraseResponse(BaseModel):
    original: str
    paraphrased: str


class ContentScoreResponse(BaseModel):
    article_id: int
    virality_score: float
    clarity_score: float
    hook_strength_score: float
    conversion_score: float
    breakdown: dict[str, str | list[str]] = {}
