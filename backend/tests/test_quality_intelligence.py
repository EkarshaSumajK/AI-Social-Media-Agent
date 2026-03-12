import asyncio

from app.services.article_quality_guard import ArticleQualityGuard
from app.services.content_screening_service import ContentScreeningService
from app.services.trend_enrichment_service import TrendEnrichmentService
from app.workflows.types import GeneratedDraft


def _sample_structured_html() -> str:
    sections = [
        'Parent-Relatable Opening Scenario',
        'What the Child Is Experiencing',
        'Why It Happens (Science Simplified)',
        'Real Life Effects (School, Home, Friends)',
        'What Parents Usually Misunderstand',
        'Professional Guidance Steps',
        'When to Seek Help',
        'How Our Services Help',
        'Reassuring Closing Message',
    ]
    body = ['<h1>Draft title</h1>']
    for heading in sections:
        body.append(f'<section><h2>{heading}</h2><p>Parents see these patterns and we explain what to do next.</p></section>')
    return ''.join(body)


def test_content_screening_accepts_high_relevance_child_topic() -> None:
    service = ContentScreeningService()
    decision = asyncio.run(
        service.screen(
            title='WHO warns about school anxiety among children before exams',
            summary='Children and adolescents report stress, sleep issues, and emotional overwhelm in school settings.',
            source_name='WHO',
            source_url='https://www.who.int/news-room/example',
        )
    )
    assert decision.allowed is True
    assert decision.relevance == 'high'
    assert decision.mental_health_specific is True
    assert decision.age_group in {'child', 'teen'}
    assert decision.trust_score >= 60


def test_content_screening_rejects_low_trust_or_unrelated_topic() -> None:
    service = ContentScreeningService()
    decision = asyncio.run(
        service.screen(
            title='Global smartphone shipments rose in Q4',
            summary='Adult consumers upgraded devices and premium segment grew sharply.',
            source_name='Unknown Outlet',
            source_url='https://example.com/business/smartphones',
        )
    )
    assert decision.allowed is False
    assert decision.trust_score < 60


class StubTrendEnrichmentService(TrendEnrichmentService):
    async def _collect_discussion_snippets(self, *, topic_title: str, topic_summary: str) -> list[str]:
        return [
            'Parents in India are worried about exam stress and sleep loss.',
            'US teachers are discussing anxiety spikes before tests.',
            topic_summary,
        ]

    async def _collect_research_snippets(self, *, topic_title: str) -> list[str]:
        return [
            '1 in 7 adolescents experience mental disorders globally.',
            'About 14% of 10-19-year-olds live with a diagnosable mental health condition.',
        ]


def test_trend_enrichment_returns_context_and_statistics() -> None:
    service = StubTrendEnrichmentService()
    enriched = asyncio.run(
        service.enrich(
            topic_title='Exam stress in adolescents',
            topic_summary='Families report anxiety and sleep disruption during exam season.',
        )
    )
    assert enriched.sentiment in {'concern', 'debate', 'awareness'}
    assert len(enriched.regions) > 0
    assert len(enriched.public_concerns) > 0
    assert len(enriched.statistics) > 0


def test_article_quality_guard_auto_fixes_seo_fields() -> None:
    guard = ArticleQualityGuard()
    draft = GeneratedDraft(
        seo_title='Practical Parent Guide',
        meta_description='Short meta',
        keywords=['school stress'],
        issue_summary='Issue summary',
        why_it_matters='Why it matters',
        mental_health_implications='Implications',
        professional_insight='Insight',
        how_services_help='Services',
        call_to_action='CTA',
        content_html=_sample_structured_html(),
        social_posts={'instagram': 'x', 'linkedin': 'x', 'twitter': 'x', 'facebook': 'x'},
    )
    result = asyncio.run(
        guard.validate_and_fix(
            draft=draft,
            source_text='Completely different source wording.',
            focus_keyword='school stress',
        )
    )
    assert 'school stress' in result.draft.seo_title.lower()
    assert 140 <= len(result.draft.meta_description) <= 160
    assert result.structure_valid is True
    assert 5 <= len(result.draft.keywords) <= 8


def test_article_quality_guard_flags_high_plagiarism_similarity() -> None:
    guard = ArticleQualityGuard()
    content_html = _sample_structured_html()
    repetitive_source = ' '.join(
        [
            'Parents see these patterns and we explain what to do next.'
            for _ in range(220)
        ]
    )
    draft = GeneratedDraft(
        seo_title='Exam stress and parent support strategies for children',
        meta_description='Exam stress and parent support strategies for children: practical child mental health guidance for warning signs and timely support at home.',
        keywords=['exam stress', 'child mental health', 'parent guidance', 'school anxiety', 'teen stress'],
        issue_summary='Issue summary',
        why_it_matters='Why it matters',
        mental_health_implications='Implications',
        professional_insight='Insight',
        how_services_help='Services',
        call_to_action='CTA',
        content_html=content_html,
        social_posts={'instagram': 'x', 'linkedin': 'x', 'twitter': 'x', 'facebook': 'x'},
    )

    result = asyncio.run(
        guard.validate_and_fix(
            draft=draft,
            source_text=repetitive_source,
            focus_keyword='exam stress',
        )
    )

    assert result.passed is True
    assert result.source_similarity_score > 0.18
    assert any('plagiarism' in note.lower() or 'overlap' in note.lower() for note in result.quality_notes or [])
