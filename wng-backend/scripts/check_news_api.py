import asyncio
import sys
from pathlib import Path

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()

    if not settings.news_api_key:
        print('FAIL: NEWS_API_KEY is missing. Set NEWS_API_KEY in .env')
        raise SystemExit(1)

    params = {
        'q': 'mental health',
        'sources': settings.news_api_sources,
        'sortBy': 'publishedAt',
        'language': 'en',
        'pageSize': 5,
        'apiKey': settings.news_api_key,
    }

    url = 'https://newsapi.org/v2/everything'

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)
            payload = response.json()
    except Exception as exc:
        print(f'FAIL: Request error: {exc}')
        raise SystemExit(1)

    if response.status_code != 200:
        print(f'FAIL: HTTP {response.status_code}')
        print(payload)
        raise SystemExit(1)

    if payload.get('status') != 'ok':
        print('FAIL: NewsAPI returned non-ok status')
        print(payload)
        raise SystemExit(1)

    articles = payload.get('articles') or []
    print(f'PASS: NewsAPI reachable. Articles returned: {len(articles)}')
    for index, article in enumerate(articles[:3], start=1):
        title = str(article.get('title') or '').strip()
        source = str((article.get('source') or {}).get('name') or 'Unknown').strip()
        print(f'{index}. {title} [{source}]')


if __name__ == '__main__':
    asyncio.run(main())
