from __future__ import annotations

import re

from app.models.article import Article


class NativePublishService:
    def generate_slug(self, title: str) -> str:
        slug = title.lower().strip()
        slug = re.sub(r'[^a-z0-9]+', '-', slug)
        slug = slug.strip('-')
        return slug[:490]

    async def publish_article(self, article: Article) -> tuple[str, str]:
        base_slug = self.generate_slug(article.seo_title)
        article.slug = f'{base_slug}-{article.id}'
        published_url = f'/articles/{article.slug}'
        return published_url, str(article.id)
