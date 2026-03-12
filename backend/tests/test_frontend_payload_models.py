import pytest
from pydantic import ValidationError

from app.api.routes import audience_content, campaigns, competitors, daily_posts, hooks, platform_content, repurpose, swipe_files, thought_leadership


def test_daily_posts_payload_matches_backend_model() -> None:
    payload = {
        'industry': 'SaaS',
        'region': 'usa',
        'target_audience': 'Founders',
        'business_goal': 'leads',
    }
    model = daily_posts.DailyPostsRequest.model_validate(payload)
    assert model.industry == 'SaaS'


def test_daily_posts_legacy_payload_rejected() -> None:
    with pytest.raises(ValidationError):
        daily_posts.DailyPostsRequest.model_validate(
            {
                'topic': 'old payload shape',
                'post_types': ['storytelling'],
            }
        )


def test_thought_leadership_payload_matches_backend_model() -> None:
    payload = {
        'topic': 'AI GTM',
        'content_type': 'deep_insight',
        'industry': 'SaaS',
    }
    model = thought_leadership.ThoughtLeadershipRequest.model_validate(payload)
    assert model.content_type == 'deep_insight'


def test_audience_payload_matches_backend_model() -> None:
    payload = {
        'audience_type': 'founders',
        'region': 'global',
        'income_bracket': 'middle',
        'awareness_stage': 'warm',
        'pain_points': ['low engagement', 'poor clarity'],
    }
    model = audience_content.AudienceContentRequest.model_validate(payload)
    assert len(model.pain_points) == 2


def test_platform_content_payload_matches_backend_model() -> None:
    payload = {
        'topic': 'AI launch playbook',
        'platform': 'linkedin',
        'content_type': 'authority_post',
    }
    model = platform_content.PlatformContentRequest.model_validate(payload)
    assert model.platform == 'linkedin'


def test_repurpose_payload_matches_backend_model() -> None:
    payload = {
        'content': 'Long text',
        'source_type': 'article',
        'target_formats': ['linkedin_post', 'thread'],
    }
    model = repurpose.RepurposeRequest.model_validate(payload)
    assert model.source_type == 'article'


def test_campaign_payload_matches_backend_model() -> None:
    payload = {
        'title': 'Webinar Campaign',
        'event_date': '2026-03-28T10:00:00Z',
        'goal': 'lead generation',
        'audience': 'Founders',
        'platforms': ['linkedin', 'twitter'],
        'platform_entity': 'horizon',
    }
    model = campaigns.CampaignCreateRequest.model_validate(payload)
    assert model.platform_entity == 'horizon'


def test_competitor_payload_matches_backend_model() -> None:
    payload = {
        'name': 'Acme Competitor',
        'platform': 'linkedin',
        'profile_url': 'https://example.com/company/acme',
        'platform_entity': 'horizon',
    }
    model = competitors.CompetitorCreateRequest.model_validate(payload)
    assert model.profile_url.startswith('https://')


def test_hook_payload_matches_backend_model() -> None:
    payload = {
        'hook_text': 'Stop posting random updates.',
        'category': 'contrarian',
        'platform': 'linkedin',
        'industry': 'saas',
    }
    model = hooks.HookCreateRequest.model_validate(payload)
    assert model.category == 'contrarian'


def test_swipe_file_payload_matches_backend_model() -> None:
    payload = {
        'platform': 'linkedin',
        'title': 'Strong founder hook',
        'content': 'The post body',
        'source_url': 'https://example.com/post',
        'performance_notes': 'High save rate',
        'tags': ['hook', 'founder'],
    }
    model = swipe_files.SwipeFileCreateRequest.model_validate(payload)
    assert model.performance_notes == 'High save rate'
