import re

from app.models.topic import Topic

DISCLAIMER_TEXT = 'This content is for educational purposes only'
AUTHOR_INFO_TEXT = 'Horizon Therapy Centre Clinical Content Team'


def ensure_disclaimer(content_html: str) -> str:
    if 'Footer Disclaimer' in content_html:
        return content_html
    return f'{content_html}\n\n{build_footer_disclaimer()}'


def build_source_citation(topic: Topic) -> str:
    safe_title = (topic.title or 'Source article').replace('<', '').replace('>', '')
    safe_url = (topic.source_url or '').replace('"', '%22')
    safe_source = (topic.source_name or 'Trusted source').replace('<', '').replace('>', '')
    citation_year = _resolve_citation_year(topic)
    return (
        '<section>'
        '<h3>Citations</h3>'
        '<ul>'
        f'<li>{safe_source} ({citation_year}). <a href="{safe_url}" target="_blank" rel="noopener noreferrer">{safe_title}</a></li>'
        '</ul>'
        '</section>'
    )


def build_footer_disclaimer() -> str:
    return f'<section><h3>Footer Disclaimer</h3><p><em>{DISCLAIMER_TEXT}</em></p></section>'


def build_author_info() -> str:
    return f'<section><h3>Author Info</h3><p>{AUTHOR_INFO_TEXT}</p></section>'


def build_meta_data_block(*, seo_title: str, meta_description: str, keywords: list[str] | None) -> str:
    safe_title = (seo_title or '').strip().replace('<', '').replace('>', '')
    safe_meta = (meta_description or '').strip().replace('<', '').replace('>', '')
    normalized_keywords = [str(item).strip() for item in (keywords or []) if str(item).strip()]
    safe_keywords = ', '.join(normalized_keywords) if normalized_keywords else 'n/a'

    # Derive OG and Twitter tags from existing SEO fields
    og_title = safe_title
    og_description = safe_meta[:200]
    twitter_title = safe_title[:70]
    twitter_description = safe_meta[:200]

    return (
        '<section>'
        '<h3>Meta Data</h3>'
        '<ul>'
        f'<li><strong>SEO Title:</strong> {safe_title}</li>'
        f'<li><strong>Meta Description:</strong> {safe_meta}</li>'
        f'<li><strong>Keywords:</strong> {safe_keywords}</li>'
        '</ul>'
        '<h4>Open Graph</h4>'
        '<ul>'
        f'<li><strong>og:title:</strong> {og_title}</li>'
        f'<li><strong>og:description:</strong> {og_description}</li>'
        '<li><strong>og:type:</strong> article</li>'
        '</ul>'
        '<h4>Twitter Card</h4>'
        '<ul>'
        f'<li><strong>twitter:title:</strong> {twitter_title}</li>'
        f'<li><strong>twitter:description:</strong> {twitter_description}</li>'
        '<li><strong>twitter:card:</strong> summary_large_image</li>'
        '</ul>'
        '</section>'
    )


def _resolve_citation_year(topic: Topic) -> str:
    source_url = str(topic.source_url or '')
    match = re.search(r'(?<!\d)(20\d{2})(?!\d)', source_url)
    if match:
        return str(int(match.group(1)))

    original_published_at = getattr(topic, 'original_published_at', None)
    if original_published_at is not None:
        return str(int(original_published_at.year))

    created_at = getattr(topic, 'created_at', None)
    if created_at is not None:
        return str(int(created_at.year))

    return 'n.d.'
