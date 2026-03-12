"""Scrape web pages via Firecrawl API."""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def scrape_url(url: str, *, wait_for_ms: int = 5000) -> str | None:
    """Scrape a URL and return markdown content. Returns None if scraping fails or API key is missing."""
    settings = get_settings()
    api_key = settings.firecrawl_api_key
    if not api_key:
        logger.debug('FIRECRAWL_API_KEY not set, skipping scrape')
        return None

    payload: dict = {
        'url': url,
        'formats': ['markdown'],
        'onlyMainContent': True,
    }
    if wait_for_ms > 0:
        payload['waitFor'] = wait_for_ms

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                'https://api.firecrawl.dev/v1/scrape',
                headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning('Firecrawl scrape failed for %s: %s', url, exc)
        return None

    if not data.get('success'):
        logger.warning('Firecrawl scrape returned success=false for %s', url)
        return None

    markdown = (data.get('data') or {}).get('markdown')
    if not markdown or not isinstance(markdown, str):
        return None

    return markdown.strip() or None
