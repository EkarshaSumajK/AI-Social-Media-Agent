from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.article import Article
from app.models.enums import ArticleStatus
from app.schemas.article import PublishedArticleOut

router = APIRouter()


@router.get('', response_model=list[PublishedArticleOut])
async def list_published_articles(
    platform: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> list[PublishedArticleOut]:
    stmt = (
        select(Article)
        .where(Article.status == ArticleStatus.PUBLISHED)
        .order_by(Article.published_at.desc())
    )
    if platform:
        stmt = stmt.where(Article.platform == platform)
    result = await db.execute(stmt)
    return [PublishedArticleOut.model_validate(a) for a in result.scalars().all()]


@router.get('/{slug}', response_model=PublishedArticleOut)
async def get_published_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> PublishedArticleOut:
    result = await db.execute(
        select(Article).where(
            Article.slug == slug,
            Article.status == ArticleStatus.PUBLISHED,
        )
    )
    article = result.scalar_one_or_none()
    if not article:
        raise HTTPException(status_code=404, detail='Article not found')
    return PublishedArticleOut.model_validate(article)
