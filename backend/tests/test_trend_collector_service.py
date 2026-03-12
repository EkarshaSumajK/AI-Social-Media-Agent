import asyncio

from app.services.trend_collector_service import (
    TRUSTED_DOMAIN_ORDER,
    TRUSTED_RSS_SOURCES,
    TrendCollector,
    _build_candidate_pool_for_heading,
    _extract_feed_source_url,
    _apply_llm_headings_to_trending_tweets,
    _compose_x_discovery_query,
    _domain_matches_allowed,
    _engagement_score,
    _extract_topic_from_tweet,
    _heading_relevance_score,
    _healthcare_scoped_query,
    _is_child_mental_health_related,
    _is_healthcare_related,
    _is_x_or_twitter_url,
    _relax_x_discovery_query,
    _heading_title_fast_score,
    _prefilter_rows_by_heading_title,
    _query_terms,
    _select_top_recent_engaging_tweets,
)


def test_healthcare_scoped_query_wraps_user_query() -> None:
    result = _healthcare_scoped_query('child nutrition')
    assert '(child nutrition)' in result
    assert 'AND' in result
    assert 'mental health' in result.lower()


def test_healthcare_scoped_query_handles_empty_input() -> None:
    result = _healthcare_scoped_query('   ')
    assert result.startswith('(')
    assert 'mental health' in result.lower()


def test_is_healthcare_related_accepts_medical_topic() -> None:
    assert _is_healthcare_related('New clinical treatment guidance for pediatric anxiety') is True


def test_is_healthcare_related_rejects_non_health_topic() -> None:
    assert _is_healthcare_related('New smartphone launch and gaming benchmark updates') is False


def test_is_child_mental_health_related_requires_both_signals() -> None:
    assert _is_child_mental_health_related('teen anxiety and school stress') is True
    assert _is_child_mental_health_related('teen education outcomes in math') is False
    assert _is_child_mental_health_related('adult depression treatment options') is False


def test_engagement_score_weights_replies_and_quotes() -> None:
    score = _engagement_score(
        {
            'like_count': 10,
            'reply_count': 5,
            'retweet_count': 4,
            'quote_count': 3,
        }
    )
    assert score == 32.0


def test_extract_topic_from_tweet_prefers_relevant_hashtag() -> None:
    topic = _extract_topic_from_tweet(
        text='Parents discussing support options this week.',
        entities={'hashtags': [{'tag': 'TeenAnxiety'}, {'tag': 'SchoolStress'}]},
    )
    assert topic == 'teenanxiety'


def test_is_x_or_twitter_url_detects_social_links() -> None:
    assert _is_x_or_twitter_url('https://x.com/someuser/status/123') is True
    assert _is_x_or_twitter_url('https://twitter.com/someuser/status/123') is True
    assert _is_x_or_twitter_url('https://www.who.int/news-room') is False


def test_trusted_rss_sources_include_core_domains() -> None:
    domains = {str(row['domain']) for row in TRUSTED_RSS_SOURCES}
    assert {'who.int', 'cdc.gov', 'nih.gov'}.issubset(domains)
    assert len(TRUSTED_RSS_SOURCES) >= 3


def test_domain_matches_allowed_allows_subdomains_only_for_trusted_host() -> None:
    assert _domain_matches_allowed('https://www.who.int/news-room', 'who.int') is True
    assert _domain_matches_allowed('https://news.pib.gov.in/pressrelease', 'pib.gov.in') is True
    assert _domain_matches_allowed('https://example.com/article', 'who.int') is False


def test_extract_feed_source_url_prefers_article_link_over_source_href() -> None:
    entry = {
        'link': 'https://www.cdc.gov/media/releases/2026/example.html',
        'source': {'href': 'https://tools.cdc.gov/api/v2/resources/media/132608.rss'},
    }

    assert _extract_feed_source_url(entry) == 'https://www.cdc.gov/media/releases/2026/example.html'


def test_heading_relevance_score_requires_heading_term_overlap() -> None:
    item = {
        'title': 'WHO issues new advisory on teen anxiety in schools',
        'summary': 'Guidance for parents and teachers on student stress and mental health support.',
    }

    high = _heading_relevance_score(item=item, heading='teen anxiety in schools')
    low = _heading_relevance_score(item=item, heading='smartphone camera launch event')

    assert high >= 2
    assert low == 0


def test_apply_llm_headings_to_trending_tweets_replaces_topic_when_heading_exists() -> None:
    trending_tweets = [
        {
            'topic': 'children anxiety',
            'sample_text': 'Parents worried about teen anxiety and school stress spikes this month',
            'engagement_score': 124.0,
        }
    ]
    heading_queries = [
        {
            'query': 'Teen Anxiety and School Stress Concerns Rise Among Parents',
            'sample_text': 'Parents worried about teen anxiety and school stress spikes this month',
        }
    ]

    normalized = _apply_llm_headings_to_trending_tweets(trending_tweets, heading_queries)

    assert normalized[0]['topic'] == 'Teen Anxiety and School Stress Concerns Rise Among Parents'


def test_compose_x_discovery_query_normalizes_multiline_query() -> None:
    query = '\n  child mental health  \n  in schools \n'
    composed = _compose_x_discovery_query(query)

    assert '\n' not in composed
    assert '(child mental health in schools)' in composed
    assert 'lang:en -is:retweet' in composed


def test_relax_x_discovery_query_removes_country_and_min_faves_cleanly() -> None:
    query = '("child mental health") AND (place_country:IN OR place_country:US) AND lang:en AND -is:retweet AND min_faves:25'
    relaxed = _relax_x_discovery_query(query)

    assert 'place_country' not in relaxed
    assert 'min_faves' not in relaxed
    assert 'AND AND' not in relaxed
    assert relaxed.endswith('-is:retweet')


def test_select_top_recent_engaging_tweets_prefers_engagement_over_recency() -> None:
    rows = [
        {
            'id': 'older-high-engagement',
            'created_at': '2026-02-20T10:00:00.000Z',
            'engagement_score': 9999.0,
            'like_count': 9000,
            'reply_count': 50,
            'retweet_count': 30,
            'quote_count': 10,
        },
        {
            'id': 'newer-lower-engagement',
            'created_at': '2026-02-23T12:00:00.000Z',
            'engagement_score': 600.0,
            'like_count': 500,
            'reply_count': 40,
            'retweet_count': 20,
            'quote_count': 5,
        },
    ]

    selected = _select_top_recent_engaging_tweets(rows, limit=2)
    assert [row['id'] for row in selected] == ['older-high-engagement', 'newer-lower-engagement']


def test_select_top_recent_engaging_tweets_filters_very_low_engagement_when_possible() -> None:
    rows = [
        {
            'id': 'very-low-engagement',
            'created_at': '2026-02-23T12:00:00.000Z',
            'engagement_score': 0.0,
            'like_count': 0,
            'reply_count': 0,
            'retweet_count': 0,
            'quote_count': 0,
        },
        {
            'id': 'qualified-engagement',
            'created_at': '2026-02-20T10:00:00.000Z',
            'engagement_score': 12.0,
            'like_count': 8,
            'reply_count': 1,
            'retweet_count': 2,
            'quote_count': 0,
        },
    ]

    selected = _select_top_recent_engaging_tweets(rows, limit=2)
    assert [row['id'] for row in selected] == ['qualified-engagement']


def test_select_top_recent_engaging_tweets_uses_all_stats_for_ties() -> None:
    rows = [
        {
            'id': 'same-time-lower-metrics',
            'created_at': '2026-02-23T12:00:00.000Z',
            'engagement_score': 200.0,
            'like_count': 100,
            'reply_count': 10,
            'retweet_count': 5,
            'quote_count': 1,
        },
        {
            'id': 'same-time-higher-metrics',
            'created_at': '2026-02-23T12:00:00.000Z',
            'engagement_score': 220.0,
            'like_count': 120,
            'reply_count': 11,
            'retweet_count': 6,
            'quote_count': 2,
        },
    ]

    selected = _select_top_recent_engaging_tweets(rows, limit=2)
    assert [row['id'] for row in selected] == ['same-time-higher-metrics', 'same-time-lower-metrics']


def test_heading_title_fast_score_prefers_strong_title_overlap() -> None:
    high = _heading_title_fast_score(
        heading='Teen anxiety support in schools',
        article_title='WHO guidance on teen anxiety support in schools',
    )
    low = _heading_title_fast_score(
        heading='Teen anxiety support in schools',
        article_title='Global update on vaccine cold-chain logistics',
    )

    assert high > low
    assert high > 0
    assert low == 0


def test_query_terms_strips_punctuation_and_stopwords() -> None:
    terms = _query_terms('Teen anxiety, in schools: support for parents!')
    assert terms == ['teen', 'anxiety', 'schools', 'support', 'parents']


def test_prefilter_rows_by_heading_title_limits_to_single_domain() -> None:
    rows = [
        {
            'title': 'WHO guidance on teen anxiety support in schools',
            'source_url': 'https://www.who.int/news/1',
        },
        {
            'title': 'CDC update on school mental health programs',
            'source_url': 'https://www.cdc.gov/media/1',
        },
        {
            'title': 'WHO school stress and teen depression advisory',
            'source_url': 'https://www.who.int/news/2',
        },
    ]

    selected = _prefilter_rows_by_heading_title(
        rows=rows,
        heading='Teen anxiety support in schools',
        source_domain='who.int',
        limit=5,
    )

    assert len(selected) == 2
    assert all(_domain_matches_allowed(item['source_url'], 'who.int') for item in selected)


def test_prefilter_rows_by_heading_title_uses_tweet_context_anchor_terms() -> None:
    rows = [
        {
            'title': 'WHO advisory on teen anxiety support for families',
            'summary': 'General guidance for households.',
            'source_url': 'https://www.who.int/news/1',
        },
        {
            'title': 'WHO advisory on CBSE exam stress and teen anxiety support',
            'summary': 'Exam-related stress guidance for students and parents.',
            'source_url': 'https://www.who.int/news/2',
        },
    ]

    selected = _prefilter_rows_by_heading_title(
        rows=rows,
        heading='CBSE exam stress and teen anxiety',
        source_domain='who.int',
        limit=1,
        tweet_text='Parents discussing CBSE exam pressure this week',
    )

    assert len(selected) == 1
    assert selected[0]['source_url'].endswith('/2')


def test_build_candidate_pool_for_heading_limits_to_50_and_prioritizes_anchor_terms() -> None:
    rows: list[dict] = []
    for idx in range(80):
        rows.append(
            {
                'title': f'WHO teen anxiety support update {idx}',
                'summary': 'Guidance for parents and schools on adolescent wellbeing.',
                'source_url': f'https://www.who.int/news/{idx}',
                'published_at': f'2026-02-{(idx % 27) + 1:02d}T00:00:00+00:00',
            }
        )

    rows.append(
        {
            'title': 'WHO advisory on CBSE exam stress and teen anxiety support',
            'summary': 'Focused guidance on CBSE exam stress for students and parents.',
            'source_url': 'https://www.who.int/news/best',
            'published_at': '2026-02-28T00:00:00+00:00',
        }
    )

    selected = _build_candidate_pool_for_heading(
        rows=rows,
        heading='CBSE exam stress and teen anxiety',
        tweet_text='Parents discussing CBSE exam stress this week',
        limit=50,
    )

    assert len(selected) == 50
    assert selected[0]['source_url'].endswith('/best')


def test_fetch_trusted_rss_entries_for_heading_uses_5_per_source_then_final_3(monkeypatch) -> None:
    collector = TrendCollector()
    calls: list[dict[str, int]] = []

    async def fake_rank(*, heading: str, rows: list[dict], top_k: int, tweet_text: str | None = None) -> list[dict]:
        calls.append({'rows': len(rows), 'top_k': top_k})
        ranked: list[dict] = []
        for row in rows[:top_k]:
            cloned = dict(row)
            cloned['_heading_title_llm_score'] = 90
            ranked.append(cloned)
        return ranked

    monkeypatch.setattr(collector, '_rank_article_titles_with_llm', fake_rank)

    preloaded_rows: list[dict] = []
    for domain in TRUSTED_DOMAIN_ORDER:
        for idx in range(6):
            preloaded_rows.append(
                {
                    'title': f'Teen anxiety support in schools update {idx} {domain}',
                    'source_url': f'https://www.{domain}/news/{idx}',
                    'summary': '',
                    'published_at': f'2026-02-{idx + 1:02d}T00:00:00+00:00',
                }
            )

    selected = asyncio.run(
        collector._fetch_trusted_rss_entries_for_heading(
            'Teen anxiety support in schools',
            desired_count=3,
            preloaded_rows=preloaded_rows,
        )
    )

    assert len(selected) == 3
    assert len(calls) == len(TRUSTED_DOMAIN_ORDER) + 1
    assert [call['top_k'] for call in calls[: len(TRUSTED_DOMAIN_ORDER)]] == [5] * len(TRUSTED_DOMAIN_ORDER)
    assert calls[-1]['top_k'] == 3
    assert [call['rows'] for call in calls[: len(TRUSTED_DOMAIN_ORDER)]] == [6] * len(TRUSTED_DOMAIN_ORDER)
    assert calls[-1]['rows'] == len(TRUSTED_DOMAIN_ORDER) * 5


def test_fetch_trusted_rss_entries_for_heading_filters_non_anchor_matches(monkeypatch) -> None:
    collector = TrendCollector()

    async def fake_rank(*, heading: str, rows: list[dict], top_k: int, tweet_text: str | None = None) -> list[dict]:
        ranked: list[dict] = []
        for row in rows[:top_k]:
            cloned = dict(row)
            cloned['_heading_title_llm_score'] = 95
            cloned['_heading_relevance_score'] = 95
            ranked.append(cloned)
        return ranked

    monkeypatch.setattr(collector, '_rank_article_titles_with_llm', fake_rank)

    preloaded_rows = [
        {
            'title': 'WHO advisory on teen anxiety support for families',
            'source_url': 'https://www.who.int/news/1',
            'summary': 'General guidance for families.',
            'published_at': '2026-02-01T00:00:00+00:00',
        },
        {
            'title': 'WHO advisory on CBSE exam stress and teen anxiety support',
            'source_url': 'https://www.who.int/news/2',
            'summary': 'Focused guidance on CBSE exam stress for students.',
            'published_at': '2026-02-02T00:00:00+00:00',
        },
    ]

    selected = asyncio.run(
        collector._fetch_trusted_rss_entries_for_heading(
            'CBSE exam stress and teen anxiety',
            desired_count=3,
            preloaded_rows=preloaded_rows,
            tweet_text='Parents discussing CBSE exam stress this week',
        )
    )

    assert len(selected) == 1
    assert selected[0]['source_url'].endswith('/2')
