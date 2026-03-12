import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.database import get_db
from app.models.enums import ArticleStatus
from app.models.user import User
from app.schemas.article import ArticleOut, DraftUpdateRequest, MessageResponse, SocialPublishResponse
from app.services.article_service import ArticleService
from app.services.content_pipeline_service import ContentPipelineService, DuplicateTopicError
from app.workers.tasks import generate_draft_task, publish_social_posts_task

router = APIRouter()
service = ArticleService()
logger = logging.getLogger(__name__)


@router.get('', response_model=list[ArticleOut])
async def list_drafts(
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200, description='Max results to return'),
    offset: int = Query(0, ge=0, description='Number of results to skip'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> list[ArticleOut]:
    status_enum = None
    if status:
        try:
            status_enum = ArticleStatus(status)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail='Invalid article status') from exc

    records = await service.list_articles(db, status=status_enum)
    paginated = records[offset:offset + limit]
    return [ArticleOut.model_validate(record) for record in paginated]


@router.get('/{article_id}', response_model=ArticleOut)
async def get_draft(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_reviewer),
) -> ArticleOut:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ArticleOut.model_validate(article)


@router.put('/{article_id}', response_model=ArticleOut)
async def update_draft(
    article_id: int,
    payload: DraftUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ArticleOut:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        article = await service.update_draft(
            db,
            article_id=article_id,
            actor_id=current_user.id,
            content_html=payload.content_html,
            seo_title=payload.seo_title,
            meta_description=payload.meta_description,
            keywords=payload.keywords,
            issue_summary=payload.issue_summary,
            why_it_matters=payload.why_it_matters,
            mental_health_implications=payload.mental_health_implications,
            professional_insight=payload.professional_insight,
            how_services_help=payload.how_services_help,
            call_to_action=payload.call_to_action,
            social_posts=payload.social_posts,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ArticleOut.model_validate(article)


@router.post('/{article_id}/approve', response_model=ArticleOut)
async def approve_draft(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ArticleOut:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        article = await service.approve_draft(db, article_id=article_id, actor_id=current_user.id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArticleOut.model_validate(article)


@router.post('/{article_id}/reject', response_model=ArticleOut)
async def reject_draft(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ArticleOut:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        article = await service.reject_draft(db, article_id=article_id, actor_id=current_user.id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ArticleOut.model_validate(article)


@router.post('/{article_id}/publish', response_model=ArticleOut)
async def publish_draft(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ArticleOut:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        article = await service.publish_article(db, article_id=article_id, actor_id=current_user.id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        publish_social_posts_task.delay(article.id, current_user.id)
    except Exception:
        logger.exception(
            'Social publish task enqueue failed after article publish (article_id=%s, actor_id=%s)',
            article.id,
            current_user.id,
        )
    return ArticleOut.model_validate(article)


@router.post('/{article_id}/social/publish', response_model=SocialPublishResponse)
async def publish_social(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> SocialPublishResponse:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        article, outcomes = await service.publish_social(db, article_id=article_id, actor_id=current_user.id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return SocialPublishResponse(article_id=article.id, outcomes=outcomes)


@router.post('/{article_id}/regenerate', response_model=ArticleOut)
async def regenerate_draft(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> ArticleOut:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if article.topic_id is None:
        raise HTTPException(status_code=400, detail='Article has no linked topic for regeneration.')

    pipeline = ContentPipelineService()
    try:
        article = await pipeline.generate_draft_for_topic(db, topic_id=article.topic_id, actor_id=current_user.id)
    except DuplicateTopicError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ArticleOut.model_validate(article)


@router.delete('/{article_id}', response_model=MessageResponse)
async def delete_draft(
    article_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> MessageResponse:
    try:
        article = await service.get_article(db, article_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if article.status == ArticleStatus.PUBLISHED:
        raise HTTPException(status_code=400, detail='Published articles cannot be deleted.')

    await db.delete(article)
    await db.commit()
    return MessageResponse(message=f'Draft {article_id} deleted.')
