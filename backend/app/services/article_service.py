from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.article import Article
from app.models.enums import ArticleStatus, Platform
from app.services.audit_service import log_action
from app.services.cms_service import NativePublishService
from app.services.lock_service import redis_lock
from app.services.social_service import SocialPublisher, mark_posts_ready, upsert_social_posts


class ArticleService:
    def __init__(self) -> None:
        self.publish_service = NativePublishService()
        self.social_publisher = SocialPublisher()

    async def list_articles(self, db: AsyncSession, *, status: ArticleStatus | None = None, platform: Platform | None = None, created_by: int | None = None) -> list[Article]:
        stmt = select(Article).options(selectinload(Article.social_posts), selectinload(Article.topic)).order_by(Article.created_at.desc())
        if status:
            stmt = stmt.where(Article.status == status)
        if platform:
            stmt = stmt.where(Article.platform == platform)
        if created_by is not None:
            stmt = stmt.where(Article.created_by == created_by)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_article(self, db: AsyncSession, article_id: int) -> Article:
        result = await db.execute(
            select(Article)
            .options(selectinload(Article.social_posts), selectinload(Article.topic), selectinload(Article.approver))
            .where(Article.id == article_id)
        )
        article = result.scalar_one_or_none()
        if not article:
            raise ValueError('Article not found')
        return article

    async def update_draft(
        self,
        db: AsyncSession,
        *,
        article_id: int,
        actor_id: int,
        content_html: str,
        seo_title: str,
        meta_description: str,
        keywords: list[str],
        issue_summary: str,
        why_it_matters: str,
        mental_health_implications: str,
        professional_insight: str,
        how_services_help: str,
        call_to_action: str,
        social_posts: dict[str, str],
    ) -> Article:
        article = await self.get_article(db, article_id)

        if article.status == ArticleStatus.PUBLISHED:
            raise RuntimeError('Published articles cannot be edited from draft workflow.')

        article.content_html = content_html
        article.seo_title = seo_title
        article.meta_description = meta_description
        article.keywords = keywords
        article.issue_summary = issue_summary
        article.why_it_matters = why_it_matters
        article.mental_health_implications = mental_health_implications
        article.professional_insight = professional_insight
        article.how_services_help = how_services_help
        article.call_to_action = call_to_action

        upsert_social_posts(article, social_posts)

        await log_action(
            db,
            action='draft_updated',
            entity_type='article',
            entity_id=str(article.id),
            actor_id=actor_id,
            details={'status': article.status.value},
        )
        await db.commit()
        await db.refresh(article)
        return await self.get_article(db, article.id)

    async def approve_draft(self, db: AsyncSession, *, article_id: int, actor_id: int) -> Article:
        article = await self.get_article(db, article_id)

        if article.status not in {ArticleStatus.DRAFT, ArticleStatus.REJECTED}:
            raise RuntimeError('Only draft or rejected articles can be approved.')

        article.status = ArticleStatus.APPROVED
        article.approved_by = actor_id
        article.approved_at = datetime.now(timezone.utc)

        await log_action(
            db,
            action='draft_approved',
            entity_type='article',
            entity_id=str(article.id),
            actor_id=actor_id,
        )
        await db.commit()
        await db.refresh(article)
        return await self.get_article(db, article.id)

    async def reject_draft(self, db: AsyncSession, *, article_id: int, actor_id: int) -> Article:
        article = await self.get_article(db, article_id)

        if article.status == ArticleStatus.PUBLISHED:
            raise RuntimeError('Published articles cannot be rejected.')

        article.status = ArticleStatus.REJECTED
        article.approved_by = None
        article.approved_at = None

        await log_action(
            db,
            action='draft_rejected',
            entity_type='article',
            entity_id=str(article.id),
            actor_id=actor_id,
        )
        await db.commit()
        await db.refresh(article)
        return await self.get_article(db, article.id)

    async def publish_article(self, db: AsyncSession, *, article_id: int, actor_id: int) -> Article:
        async with redis_lock(f'article:{article_id}:publish', ttl_seconds=180):
            article = await self.get_article(db, article_id)

            if article.status != ArticleStatus.APPROVED:
                raise RuntimeError('Article must be approved before publishing.')
            if not article.approved_by or not article.approved_at:
                raise RuntimeError('Approval metadata missing; publishing blocked by policy.')

            published_url, _ = await self.publish_service.publish_article(article)

            article.status = ArticleStatus.PUBLISHED
            article.published_url = published_url
            article.published_at = datetime.now(timezone.utc)
            mark_posts_ready(article)

            await log_action(
                db,
                action='article_published',
                entity_type='article',
                entity_id=str(article.id),
                actor_id=actor_id,
                details={'published_url': published_url},
            )
            await db.commit()
            await db.refresh(article)
            return await self.get_article(db, article.id)

    async def publish_social(self, db: AsyncSession, *, article_id: int, actor_id: int | None = None) -> tuple[Article, dict[str, str]]:
        async with redis_lock(f'article:{article_id}:social_publish', ttl_seconds=180):
            article = await self.get_article(db, article_id)
            outcomes = await self.social_publisher.publish_pending_posts(db, article)

            await log_action(
                db,
                action='social_publish_attempt',
                entity_type='article',
                entity_id=str(article.id),
                actor_id=actor_id,
                details=outcomes,
            )
            await db.commit()
            await db.refresh(article)
            return await self.get_article(db, article.id), outcomes
