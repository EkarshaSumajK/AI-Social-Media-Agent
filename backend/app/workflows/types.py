from dataclasses import dataclass
from typing import TypedDict


class ContentState(TypedDict, total=False):
    topic_title: str
    topic_summary: str
    focus_keyword: str
    regions: list[str]
    public_concerns: list[str]
    trend_statements: list[str]
    trend_sentiment: str
    statistics: list[str]
    service_links: dict[str, str]
    services_reference: str
    humanization_guidance: str
    trend_context: str

    opening_scenario: str
    child_experience: str
    science_explanation: str
    real_life_effects: str
    parent_misunderstandings: str
    guidance_steps: str
    when_to_seek_help: str
    services_help: str
    reassuring_close: str

    issue_summary: str
    why_it_matters: str
    mental_health_implications: str
    professional_insight: str
    how_services_help: str
    call_to_action: str

    seo_title: str
    meta_description: str
    keywords: list[str]
    content_html: str
    social_posts: dict[str, str]


@dataclass
class GeneratedDraft:
    seo_title: str
    meta_description: str
    keywords: list[str]
    issue_summary: str
    why_it_matters: str
    mental_health_implications: str
    professional_insight: str
    how_services_help: str
    call_to_action: str
    content_html: str
    social_posts: dict[str, str]
    opening_scenario: str = ''
    child_experience: str = ''
    science_explanation: str = ''
    real_life_effects: str = ''
    parent_misunderstandings: str = ''
    guidance_steps: str = ''
    when_to_seek_help: str = ''
    reassuring_close: str = ''
