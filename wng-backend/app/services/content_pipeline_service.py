from __future__ import annotations

import html
import inspect
import logging
import re
from collections.abc import Awaitable, Callable
from urllib.parse import urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.article import Article
from app.models.social_post import SocialPost
from app.models.topic import Topic
from app.services.audit_service import log_action
from app.services.compliance_service import (
    build_author_info,
    build_footer_disclaimer,
    build_meta_data_block,
    build_source_citation,
    ensure_disclaimer,
)
from app.services.article_quality_guard import ArticleQualityGuard
from app.services.duplicate_service import DuplicateChecker
from app.services.embeddings_service import EmbeddingsClient, cosine_similarity
from app.services.internal_link_service import build_internal_links_block
from app.services.lock_service import redis_lock
from app.services.notification_service import NotificationService
from app.services.social_service import upsert_social_posts
from app.services.trend_enrichment_service import TrendEnrichmentService
from app.workflows.content_graph import ContentGraphRunner

settings = get_settings()
logger = logging.getLogger(__name__)
ProgressCallback = Callable[[str, int, str], Awaitable[None] | None]
URL_MODE_BYPASS_REASON = 'URL mode policy: trust and relevance screening skipped.'
CROSS_ARTICLE_SIMILARITY_THRESHOLD = 0.92


async def check_cross_article_similarity(
    db: AsyncSession,
    *,
    article_text: str,
    current_topic_id: int,
    embeddings_client: EmbeddingsClient | None = None,
) -> tuple[bool, float, int | None]:
    """Compare new article content against existing published/draft articles via embeddings.

    Returns (is_too_similar, best_score, matched_article_id).
    Only flags when cosine similarity exceeds CROSS_ARTICLE_SIMILARITY_THRESHOLD,
    meaning the new article is nearly identical to a previously generated one.
    """
    client = embeddings_client or EmbeddingsClient()
    # Embed the plain text of the new article (first 3000 chars for speed).
    probe_embedding = await client.embed(article_text[:3000])

    # Fetch embeddings from recent topics that already have articles.
    result = await db.execute(
        select(Article.id, Topic.embedding)
        .join(Topic, Article.topic_id == Topic.id)
        .where(Topic.embedding.is_not(None), Topic.id != current_topic_id)
        .order_by(Article.created_at.desc())
        .limit(200)
    )

    best_score = 0.0
    best_article_id: int | None = None
    for article_id, embedding in result.all():
        if not embedding:
            continue
        score = cosine_similarity(probe_embedding, list(embedding))
        if score > best_score:
            best_score = score
            best_article_id = article_id

    is_too_similar = best_score >= CROSS_ARTICLE_SIMILARITY_THRESHOLD
    return is_too_similar, round(best_score, 4), best_article_id


class DuplicateTopicError(RuntimeError):
    def __init__(self, message: str, *, matched_topic_id: int | None = None, score: float = 0.0) -> None:
        super().__init__(message)
        self.matched_topic_id = matched_topic_id
        self.score = score


class ContentPipelineService:
    def __init__(self) -> None:
        self.graph = ContentGraphRunner()
        self.duplicate_checker = DuplicateChecker()
        self.enrichment = TrendEnrichmentService()
        self.notifier = NotificationService()
        self.quality_guard = ArticleQualityGuard()

    async def generate_draft_from_url(
        self,
        db: AsyncSession,
        *,
        source_url: str,
        actor_id: int | None,
        progress_callback: ProgressCallback | None = None,
    ) -> Article:
        await _report_progress(progress_callback, stage='validating_url', progress=10, message='Validating article URL.')
        normalized_url = source_url.strip()
        if not _is_valid_http_url(normalized_url):
            raise ValueError('A valid http/https article URL is required.')

        async with redis_lock(f'url:{normalized_url}:draft_generation', ttl_seconds=600):
            await _report_progress(progress_callback, stage='loading_url_topic', progress=20, message='Checking existing topic for this URL.')
            topic_result = await db.execute(select(Topic).where(Topic.source_url == normalized_url).limit(1))
            topic = topic_result.scalar_one_or_none()

            if topic is None:
                await _report_progress(progress_callback, stage='fetching_article', progress=30, message='Fetching article content from URL.')
                article_payload = await _fetch_article_payload(normalized_url)
                await _report_progress(
                    progress_callback,
                    stage='screening_article',
                    progress=40,
                    message='Skipping trust and relevance screening for URL mode.',
                )

                topic = Topic(
                    title=article_payload['title'],
                    source_url=normalized_url,
                    source_name=article_payload['source_name'],
                    summary=article_payload['summary'],
                    relevance_label='high',
                    relevance_score=100,
                    age_group='unknown',
                    topic_type='general',
                    mental_health_specific=True,
                    screening_reason=URL_MODE_BYPASS_REASON,
                    trust_score=100,
                    is_trending=False,
                    trend_regions=['International'],
                    trend_sentiment='awareness',
                    status='new',
                )
                db.add(topic)
                await db.flush()

        await _report_progress(progress_callback, stage='starting_draft_generation', progress=50, message='Starting draft generation workflow.')
        return await self.generate_draft_for_topic(
            db,
            topic_id=topic.id,
            actor_id=actor_id,
            progress_callback=progress_callback,
        )

    async def generate_draft_for_topic(
        self,
        db: AsyncSession,
        *,
        topic_id: int,
        actor_id: int | None,
        progress_callback: ProgressCallback | None = None,
    ) -> Article:
        await _report_progress(progress_callback, stage='loading_topic', progress=15, message='Loading topic details.')
        async with redis_lock(f'topic:{topic_id}:draft_generation', ttl_seconds=600):
            topic_result = await db.execute(select(Topic).where(Topic.id == topic_id))
            topic = topic_result.scalar_one_or_none()
            if topic is None:
                raise ValueError('Topic not found')

            if topic.status == 'duplicate_rejected':
                raise DuplicateTopicError('Topic is already marked as duplicate')

            existing_article_result = await db.execute(
                select(Article)
                .options(selectinload(Article.social_posts))
                .where(Article.topic_id == topic.id)
            )
            article = existing_article_result.scalar_one_or_none()

            is_duplicate, score, matched_topic_id, embedding = await self.duplicate_checker.check_topic(
                db,
                title=topic.title,
                summary=topic.summary,
                threshold=settings.duplicate_generation_similarity_threshold,
            )
            await _report_progress(progress_callback, stage='duplicate_check', progress=25, message='Checking for near-duplicate topics.')
            topic.embedding = embedding

            if is_duplicate and matched_topic_id and matched_topic_id != topic.id:
                topic.status = 'duplicate_rejected'
                await log_action(
                    db,
                    action='topic_duplicate_rejected',
                    entity_type='topic',
                    entity_id=str(topic.id),
                    actor_id=actor_id,
                    details={'matched_topic_id': matched_topic_id, 'similarity': round(score, 4)},
                )
                await db.commit()
                raise DuplicateTopicError(
                    'Near-duplicate topic detected; draft generation blocked.',
                    matched_topic_id=matched_topic_id,
                    score=score,
                )

            if not topic.statistics or not topic.trend_regions:
                await _report_progress(progress_callback, stage='enrichment', progress=35, message='Enriching topic context and statistics.')
                enriched = await self.enrichment.enrich(topic_title=topic.title, topic_summary=topic.summary)
                topic.is_trending = enriched.is_trending
                topic.trend_regions = enriched.regions
                topic.public_concerns = enriched.public_concerns
                topic.trend_statements = enriched.statements
                topic.trend_sentiment = enriched.sentiment
                topic.statistics = enriched.statistics

            source_summary = str(topic.summary or '').strip()
            await _report_progress(
                progress_callback,
                stage='fetching_source_article',
                progress=45,
                message='Fetching trusted source article content for higher-fidelity drafting.',
            )
            try:
                payload = await _fetch_article_payload(topic.source_url)
                fetched_summary = str(payload.get('summary') or '').strip()
                if fetched_summary:
                    source_summary = fetched_summary
                    topic.summary = fetched_summary
            except RuntimeError:
                # Continue with existing topic summary if source fetch fails.
                pass

            guidance = (
                'Write with strong quality-by-prompt discipline. Keep SEO metadata strict and natural: focus keyword in '
                'title, meta description, first paragraph, and at least one section heading. Keep readability at 6th-8th '
                'grade with clear 12-20 word sentences and varied rhythm. Preserve the exact nine-section structure with '
                'complete, useful content in each section. CRITICAL: Avoid plagiarism by fully paraphrasing source material — '
                'never reproduce 7+ consecutive words from the source, change sentence structures, replace terminology with '
                'synonyms, and reorganize the order of ideas. Reduce AI tone by using natural clinician language and varied '
                'sentence openings. Use first-person voice naturally but not in every sentence. Avoid keyword stuffing, '
                'duplicated lines, and template labels in section outputs.'
            )

            await _report_progress(
                progress_callback,
                stage='draft_generation',
                progress=75,
                message='Generating draft content with in-prompt quality constraints.',
            )
            focus_keyword = _derive_focus_keyword(topic.title, topic.related_keywords)

            generated = await self.graph.run(
                topic_title=topic.title,
                topic_summary=source_summary,
                focus_keyword=focus_keyword,
                regions=topic.trend_regions or ['International'],
                public_concerns=topic.public_concerns or [],
                trend_statements=topic.trend_statements or [],
                trend_sentiment=topic.trend_sentiment or 'awareness',
                statistics=topic.statistics or [],
                humanization_guidance=guidance,
                progress_callback=progress_callback,
            )

            if generated is None:
                raise RuntimeError('Draft generation failed unexpectedly.')

            await _report_progress(progress_callback, stage='quality_guard', progress=82, message='Running quality guard: readability, plagiarism, SEO, humanization.')
            try:
                qg_result = await self.quality_guard.validate_and_fix(
                    draft=generated,
                    source_text=source_summary,
                    focus_keyword=focus_keyword,
                )
                generated = qg_result.draft
                quality_readability = qg_result.readability_score
                quality_ai_prob = qg_result.ai_generated_probability
                quality_similarity = qg_result.source_similarity_score
                quality_structure = qg_result.structure_valid
                quality_notes = qg_result.quality_notes
                # When quality guard flags plagiarism issues, force human review.
                quality_requires_review = not qg_result.passed
            except Exception:
                logger.warning('Quality guard failed for topic %s, continuing with raw draft.', topic.id, exc_info=True)
                quality_readability = None
                quality_ai_prob = None
                quality_similarity = None
                quality_structure = True
                quality_notes = ['quality_guard_skipped: guard raised an exception']
                quality_requires_review = True

            if quality_requires_review:
                logger.info(
                    'Quality guard flagged topic %s for review: %s',
                    topic.id,
                    ', '.join(quality_notes[:5]) if quality_notes else 'unknown',
                )

            # Cross-article deduplication: flag if content is too similar to an existing article.
            try:
                from app.services.article_quality_guard import _plain_text
                article_plain = _plain_text(generated.content_html)
                is_self_plagiarized, cross_score, matched_aid = await check_cross_article_similarity(
                    db,
                    article_text=article_plain,
                    current_topic_id=topic.id,
                )
                if is_self_plagiarized:
                    quality_requires_review = True
                    cross_note = (
                        f'cross_article_similarity={cross_score} exceeds {CROSS_ARTICLE_SIMILARITY_THRESHOLD} '
                        f'(matched article_id={matched_aid})'
                    )
                    quality_notes = (quality_notes or []) + [cross_note]
                    logger.info('Cross-article dedup flagged topic %s: %s', topic.id, cross_note)
            except Exception:
                logger.warning('Cross-article dedup check failed for topic %s, continuing.', topic.id, exc_info=True)

            await _report_progress(progress_callback, stage='finalizing_content', progress=88, message='Applying compliance and internal links.')
            footer_blocks = [
                build_footer_disclaimer(),
                build_author_info(),
                build_source_citation(topic),
                build_internal_links_block(),
                build_meta_data_block(
                    seo_title=generated.seo_title,
                    meta_description=generated.meta_description,
                    keywords=generated.keywords,
                ),
            ]
            content_html = f"{generated.content_html}\n\n<footer>{''.join(footer_blocks)}</footer>"
            content_html = ensure_disclaimer(content_html)

            slug = _generate_slug(generated.seo_title, topic.id)

            if article is None:
                article = Article(
                    topic_id=topic.id,
                    created_by=actor_id,
                    content_html=content_html,
                    seo_title=generated.seo_title,
                    meta_description=generated.meta_description,
                    keywords=generated.keywords,
                    slug=slug,
                    issue_summary=generated.issue_summary,
                    why_it_matters=generated.why_it_matters,
                    mental_health_implications=generated.mental_health_implications,
                    professional_insight=generated.professional_insight,
                    how_services_help=generated.how_services_help,
                    call_to_action=generated.call_to_action,
                    source_url=topic.source_url,
                    status='draft',
                    requires_review=quality_requires_review,
                    internal_links_added=True,
                    readability_score=quality_readability,
                    ai_generated_probability=quality_ai_prob,
                    source_similarity_score=quality_similarity,
                    structure_valid=quality_structure,
                    quality_notes=quality_notes,
                    social_posts=[],
                )
                db.add(article)
                await db.flush()
            else:
                article.content_html = content_html
                article.seo_title = generated.seo_title
                article.meta_description = generated.meta_description
                article.keywords = generated.keywords
                article.slug = slug
                article.issue_summary = generated.issue_summary
                article.why_it_matters = generated.why_it_matters
                article.mental_health_implications = generated.mental_health_implications
                article.professional_insight = generated.professional_insight
                article.how_services_help = generated.how_services_help
                article.call_to_action = generated.call_to_action
                article.source_url = topic.source_url
                article.readability_score = quality_readability
                article.ai_generated_probability = quality_ai_prob
                article.source_similarity_score = quality_similarity
                article.structure_valid = quality_structure
                article.quality_notes = quality_notes
                article.status = 'draft'
                article.approved_at = None
                article.approved_by = None
                article.published_at = None
                article.published_url = None
                article.requires_review = quality_requires_review
                article.internal_links_added = True
                posts_result = await db.execute(select(SocialPost).where(SocialPost.article_id == article.id))
                article.social_posts = list(posts_result.scalars().all())

            upsert_social_posts(article, generated.social_posts)
            topic.status = 'processed'
            await _report_progress(progress_callback, stage='saving', progress=94, message='Saving draft and audit records.')

            await log_action(
                db,
                action='draft_generated',
                entity_type='article',
                entity_id=str(article.id),
                actor_id=actor_id,
                details={'topic_id': topic.id},
            )

            await db.commit()
            await db.refresh(article)

            await _report_progress(progress_callback, stage='notifying', progress=98, message='Notifying reviewer about new draft.')
            try:
                await self.notifier.notify_new_draft(draft_id=article.id, topic_title=topic.title)
            except Exception:
                logger.warning('Failed to send notification for draft %s, continuing.', article.id, exc_info=True)
            return article


async def _report_progress(
    callback: ProgressCallback | None,
    *,
    stage: str,
    progress: int,
    message: str,
) -> None:
    if callback is None:
        return

    outcome = callback(stage, max(0, min(100, progress)), message)
    if inspect.isawaitable(outcome):
        await outcome


def _is_valid_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
    except ValueError:
        return False
    return parsed.scheme in {'http', 'https'} and bool(parsed.netloc)


async def _fetch_article_payload(source_url: str) -> dict[str, str]:
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; WNGContentBot/1.0; +https://example.com)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    transport = httpx.AsyncHTTPTransport(retries=2)
    try:
        async with httpx.AsyncClient(
            timeout=25.0,
            follow_redirects=True,
            headers=headers,
            transport=transport,
        ) as client:
            response = await client.get(source_url)
            response.raise_for_status()
    except Exception as exc:
        raise RuntimeError(f'Unable to fetch article URL: {source_url}') from exc

    body = str(response.text or '')
    title = _extract_title(body=body, source_url=source_url)
    summary = _extract_summary(body=body)
    if not summary:
        raise RuntimeError('Could not extract article content from provided URL.')

    source_name = _extract_source_name(source_url)
    return {
        'title': title,
        'summary': summary,
        'source_name': source_name,
    }


def _extract_title(*, body: str, source_url: str) -> str:
    title_match = re.search(r'<title[^>]*>(.*?)</title>', body, flags=re.IGNORECASE | re.DOTALL)
    if title_match:
        title = _clean_html_text(title_match.group(1))
        if title:
            return title[:500]

    path = (urlparse(source_url).path or '/').rstrip('/').split('/')[-1]
    fallback = path.replace('-', ' ').replace('_', ' ').strip()
    if fallback:
        return fallback[:500]
    return 'Child adolescent mental health article'


def _extract_summary(*, body: str) -> str:
    no_script = re.sub(r'<script[^>]*>.*?</script>', ' ', body, flags=re.IGNORECASE | re.DOTALL)
    no_style = re.sub(r'<style[^>]*>.*?</style>', ' ', no_script, flags=re.IGNORECASE | re.DOTALL)
    text = _clean_html_text(no_style)
    if not text:
        return ''

    # Keep enough context for downstream generation while remaining compact.
    return text[:2800]


def _clean_html_text(value: str) -> str:
    text = html.unescape(value or '')
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _extract_source_name(source_url: str) -> str:
    host = urlparse(source_url).netloc.lower()
    host = host[4:] if host.startswith('www.') else host
    return host or 'web'


_STOP_WORDS = frozenset({
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'was', 'are', 'were', 'be', 'been',
    'has', 'have', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'that', 'this', 'these', 'those', 'as', 'it',
    'its', 'than', 'into', 'over', 'after', 'still', 'also', 'just', 'more',
    'than', 'then', 'when', 'where', 'which', 'who', 'how', 'what', 'why',
    'all', 'not', 'no', 'nor', 'so', 'yet', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'only', 'own', 'same', 'up',
    # news/event stop words
    'man', 'woman', 'person', 'people', 'new', 'says', 'say', 'said',
    'ordered', 'arrested', 'linked', 'charged', 'accused', 'released',
    'calls', 'call', 'urges', 'urge', 'warns', 'warn', 'four', 'five',
    'six', 'seven', 'eight', 'nine', 'ten', 'million', 'billion', 'thousand',
    'un', 'us', 'uk', 'eu', 'leaders', 'leader', 'sustained', 'investment',
    'commitment', 'end', 'risk', 'still', 'report', 'reports', 'study',
    # headline verbs — filter so they don't pollute keyword phrases
    'announces', 'announce', 'announced', 'reveals', 'reveal', 'revealed',
    'show', 'shows', 'showed', 'showing', 'finds', 'found',
    'launch', 'launches', 'launched', 'highlight', 'highlights', 'highlighted',
    'unveil', 'unveils', 'unveiled', 'propose', 'proposes', 'proposed',
    'approve', 'approves', 'approved', 'tackle', 'tackles', 'tackled',
    'boost', 'boosts', 'boosted', 'expand', 'expands', 'expanded',
    'save', 'saves', 'saved', 'suggest', 'suggests', 'suggested',
    'indicate', 'indicates', 'indicated', 'raise', 'raises', 'raised',
    'reduce', 'reduces', 'reduced', 'improve', 'improves', 'improved',
    'improvement', 'improvements', 'provide', 'provides', 'provided',
    'introduce', 'introduces', 'introduced', 'create', 'creates', 'created',
})


def _derive_focus_keyword(topic_title: str, related_keywords: list[str] | None = None) -> str:
    """Extract a concise 2-3 word SEO focus keyword from the topic title.

    Prefers the first entry in related_keywords if it is short enough.
    Falls back to finding the best consecutive noun-phrase from the title,
    filtering out headline verbs and organisation acronyms so the result
    is a grammatically valid keyword phrase (e.g. "mental health", not
    "SAMHSA announces mental").
    """
    if related_keywords:
        candidate = str(related_keywords[0]).strip()
        if 1 <= len(candidate.split()) <= 4:
            return candidate

    cleaned = re.sub(r'[^a-zA-Z\s]', ' ', topic_title or '')
    words = cleaned.split()

    # Build mask: True = keyword-worthy word (not a stop word, not too short,
    # not an all-caps acronym like SAMHSA/UNICEF).
    mask = []
    for w in words:
        is_stop = w.lower() in _STOP_WORDS
        is_short = len(w) <= 3
        is_acronym = w.isupper() and len(w) >= 5
        mask.append(not is_stop and not is_short and not is_acronym)

    # Find consecutive runs of meaningful words.
    runs: list[tuple[int, int]] = []
    run_start = -1
    for i, is_meaningful in enumerate(mask):
        if is_meaningful:
            if run_start == -1:
                run_start = i
        else:
            if run_start != -1:
                run_len = i - run_start
                if run_len >= 2:
                    runs.append((run_start, run_len))
                run_start = -1
    if run_start != -1:
        run_len = len(mask) - run_start
        if run_len >= 2:
            runs.append((run_start, run_len))

    if runs:
        start, length = runs[0]
        # Runs of exactly 2-3 words → use the full run.
        # Longer runs → take only first 2 (phrase boundary is unclear).
        take = length if length <= 3 else 2
        return ' '.join(words[start:start + take]).strip()

    # No consecutive run of 2+; take first 2 meaningful words.
    meaningful = [w for i, w in enumerate(words) if mask[i]]
    if len(meaningful) >= 2:
        return ' '.join(meaningful[:2]).strip()
    if meaningful:
        return meaningful[0].strip()

    # Last resort: first 2 words longer than 3 characters.
    long_words = [w for w in words if len(w) > 3]
    return ' '.join(long_words[:2]).strip() or topic_title


def _generate_slug(seo_title: str, topic_id: int) -> str:
    """Generate a URL-safe slug from the SEO title, suffixed with topic_id for uniqueness."""
    base = (seo_title or '').lower()
    base = re.sub(r'[^a-z0-9\s-]', '', base)
    base = re.sub(r'[\s-]+', '-', base).strip('-')
    base = base[:80].rstrip('-')
    return f'{base}-{topic_id}' if base else str(topic_id)
