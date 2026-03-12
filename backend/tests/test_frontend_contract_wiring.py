import asyncio

from app.api.routes import audience_content, daily_posts, hooks, performance, platform_content, repurpose, thought_leadership


class FakePrompts:
    def get_prompt(self, *, bundle: str, key: str, context: dict):
        return f'system:{bundle}:{key}', f'user:{context}'


class FakeLLM:
    def __init__(self, response_text: str) -> None:
        self.response_text = response_text

    async def generate(self, *, prompt: str, system_prompt: str):
        assert prompt
        assert system_prompt
        return self.response_text


def test_daily_posts_contract(monkeypatch) -> None:
    monkeypatch.setattr(daily_posts, '_prompts', FakePrompts())
    monkeypatch.setattr(
        daily_posts,
        '_llm',
        FakeLLM('[{"post_type":"trending_topic","content":"Use a contrarian hook.","platform_hint":"linkedin"}]'),
    )

    payload = daily_posts.DailyPostsRequest(
        industry='SaaS',
        region='usa',
        target_audience='Founders',
        business_goal='leads',
    )

    response = asyncio.run(daily_posts.generate_daily_posts(payload=payload, current_user=object()))

    assert isinstance(response, daily_posts.DailyPostsResponse)
    assert len(response.suggestions) == 1
    assert response.suggestions[0].post_type == 'trending_topic'


def test_thought_leadership_contract(monkeypatch) -> None:
    monkeypatch.setattr(thought_leadership, '_prompts', FakePrompts())
    monkeypatch.setattr(thought_leadership, '_llm', FakeLLM('Deep insight content output.'))

    payload = thought_leadership.ThoughtLeadershipRequest(
        topic='AI GTM',
        content_type='deep_insight',
        industry='SaaS',
    )

    response = asyncio.run(
        thought_leadership.generate_thought_leadership(payload=payload, current_user=object())
    )

    assert response.content_type == 'deep_insight'
    assert 'insight' in response.content.lower()


def test_audience_content_contract(monkeypatch) -> None:
    monkeypatch.setattr(audience_content, '_prompts', FakePrompts())
    monkeypatch.setattr(
        audience_content,
        '_llm',
        FakeLLM('{"problem_aware":"Pain-first post.","conversion":"Clear CTA."}'),
    )

    payload = audience_content.AudienceContentRequest(
        audience_type='founders',
        region='global',
        income_bracket='middle',
        awareness_stage='warm',
        pain_points=['low engagement', 'unclear offer'],
    )

    response = asyncio.run(
        audience_content.generate_audience_content(payload=payload, current_user=object())
    )

    assert 'problem_aware' in response.results
    assert 'conversion' in response.results


def test_platform_content_contract(monkeypatch) -> None:
    monkeypatch.setattr(platform_content, '_prompts', FakePrompts())
    monkeypatch.setattr(
        platform_content,
        '_llm',
        FakeLLM('{"content":"LinkedIn-ready copy","tone":"professional","length":"short"}'),
    )

    payload = platform_content.PlatformContentRequest(
        topic='AI product launch',
        platform='linkedin',
        content_type='authority_post',
    )

    response = asyncio.run(
        platform_content.generate_platform_content(payload=payload, current_user=object())
    )

    assert response.content == 'LinkedIn-ready copy'
    assert response.metadata.get('tone') == 'professional'


def test_repurpose_contract(monkeypatch) -> None:
    monkeypatch.setattr(repurpose, '_prompts', FakePrompts())
    monkeypatch.setattr(
        repurpose,
        '_llm',
        FakeLLM('{"linkedin_post":["Post A"],"thread":["Tweet 1","Tweet 2"]}'),
    )

    payload = repurpose.RepurposeRequest(
        content='Long-form source text',
        source_type='article',
        target_formats=['linkedin_post', 'thread'],
    )

    response = asyncio.run(repurpose.repurpose_content(payload=payload, current_user=object()))

    assert list(response.results.keys()) == ['linkedin_post', 'thread']
    assert response.results['thread'][0] == 'Tweet 1'


def test_hooks_suggest_contract(monkeypatch) -> None:
    monkeypatch.setattr(hooks, '_prompts', FakePrompts())
    monkeypatch.setattr(
        hooks,
        '_llm',
        FakeLLM('[{"hook_text":"Stop posting random updates","reasoning":"Creates curiosity"}]'),
    )

    response = asyncio.run(
        hooks.suggest_hooks(topic='ai growth', platform='linkedin', count=5, _=object())
    )

    assert len(response.suggestions) == 1
    assert response.suggestions[0].hook_text.startswith('Stop posting')


def test_performance_insights_contract(monkeypatch) -> None:
    monkeypatch.setattr(performance, '_prompts', FakePrompts())
    monkeypatch.setattr(
        performance,
        '_llm',
        FakeLLM('1. Focus on consistent publishing cadence.\n2. Consider tighter hooks.'),
    )

    insights = asyncio.run(
        performance.get_performance_insights(platform='linkedin', days=30, current_user=object())
    )

    assert isinstance(insights.insights, str)
    assert isinstance(insights.recommendations, list)


def test_performance_metrics_contract() -> None:
    metrics = asyncio.run(performance.get_performance(platform=None, days=14, current_user=object()))

    assert metrics.days == 14
    assert isinstance(metrics.metrics, list)
    assert len(metrics.metrics) >= 1
