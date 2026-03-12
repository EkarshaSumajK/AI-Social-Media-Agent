from datetime import datetime, timedelta, timezone

from celery.result import AsyncResult
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_reviewer
from app.core.celery_app import celery_app
from app.core.database import get_db
from app.models.enums import TopicStatus
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import (
    CollectTopicsRequest,
    CollectTopicsResponse,
    DraftTaskStatusResponse,
    GenerateDraftRequest,
    GenerateDraftFromUrlRequest,
    GenerateDraftResponse,
    TopicOut,
)
from app.schemas.article import MessageResponse
from app.services.audit_service import log_action
from app.services.content_pipeline_service import ContentPipelineService, DuplicateTopicError
from app.services.trusted_source_filter import is_trusted_source_url
from app.services.trend_collector_service import TrendCollector
from app.workers.tasks import generate_draft_from_url_task, generate_draft_task

router = APIRouter()


def _coerce_progress(value: object) -> int | None:
    if isinstance(value, int):
        return max(0, min(100, value))
    if isinstance(value, float):
        return max(0, min(100, int(value)))
    if isinstance(value, str) and value.strip().isdigit():
        return max(0, min(100, int(value.strip())))
    return None


@router.get('/tasks/{task_id}', response_model=DraftTaskStatusResponse)
async def get_task_status(
    task_id: str,
    _: User = Depends(get_current_reviewer),
) -> DraftTaskStatusResponse:
    task = AsyncResult(task_id, app=celery_app)
    state = task.state
    meta = task.info if isinstance(task.info, dict) else {}
    progress = _coerce_progress(meta.get('progress'))
    stage = str(meta.get('stage')).strip() if meta.get('stage') is not None else None

    if state in {'PENDING', 'RECEIVED', 'STARTED', 'RETRY'}:
        status = 'queued' if state == 'PENDING' else 'running'
        default_message = 'Draft generation is queued.' if state == 'PENDING' else 'Draft generation is in progress.'
        message = str(meta.get('message') or default_message)
        return DraftTaskStatusResponse(
            task_id=task_id,
            state=state,
            status=status,
            message=message,
            article_id=None,
            progress=progress if progress is not None else (5 if state == 'PENDING' else 20),
            stage=stage,
        )

    if state == 'FAILURE':
        message = str(meta.get('message') or 'Draft generation failed in worker.')
        return DraftTaskStatusResponse(
            task_id=task_id,
            state=state,
            status='failed',
            message=message,
            article_id=None,
            progress=progress if progress is not None else 100,
            stage=stage or 'failed',
        )

    payload = task.result if isinstance(task.result, dict) else {}
    status = str(payload.get('status') or 'completed')
    article_id = payload.get('article_id')
    progress = _coerce_progress(payload.get('progress')) or progress or 100
    stage = str(payload.get('stage')).strip() if payload.get('stage') is not None else (stage or 'completed')

    if status == 'created':
        message = 'Draft created and awaiting human review.'
    elif status == 'quality_rejected':
        message = str(payload.get('error') or 'Draft rejected by quality guard.')
    elif status == 'duplicate_rejected':
        message = 'Near-duplicate topic detected. Draft generation blocked.'
    elif status == 'already_running':
        message = str(payload.get('error') or 'Draft generation is already running for this item.')
    else:
        message = 'Draft task completed.'

    return DraftTaskStatusResponse(
        task_id=task_id,
        state=state,
        status=status,
        message=message,
        article_id=article_id if isinstance(article_id, int) else None,
        progress=progress,
        stage=stage,
    )


@router.get('', response_model=list[TopicOut])
async def list_topics(
    status: str | None = None,
    since: str = Query('today', description="Filter: 'today', '48h', 'week', or 'all'"),
    q: str | None = Query(None, description='Search in title and summary'),
    topic_category: str | None = Query(None, description='Filter by category'),
    region: str | None = Query(None, description='Filter by region'),
    is_trending: bool | None = Query(None, description='Filter trending only'),
    trust_min: int | None = Query(None, ge=0, le=100, description='Minimum trust score'),
    limit: int = Query(50, ge=1, le=200, description='Max results to return'),
    offset: int = Query(0, ge=0, description='Number of results to skip'),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_reviewer),
) -> list[TopicOut]:
    stmt = select(Topic).order_by(Topic.created_at.desc())
    if status:
        try:
            stmt = stmt.where(Topic.status == TopicStatus(status))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail='Invalid topic status') from exc

    if q and len(q.strip()) >= 1:
        search = f'%{q.strip().lower()}%'
        stmt = stmt.where(
            Topic.title.ilike(search) | (Topic.summary.isnot(None) & Topic.summary.ilike(search))
        )
    if topic_category:
        stmt = stmt.where(Topic.topic_category == topic_category)
    if region:
        stmt = stmt.where(Topic.region == region)
    if is_trending is not None:
        stmt = stmt.where(Topic.is_trending == is_trending)
    if trust_min is not None:
        stmt = stmt.where(Topic.trust_score >= trust_min)

    now = datetime.now(timezone.utc)
    if since == 'today':
        stmt = stmt.where(Topic.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0))
    elif since == '48h':
        stmt = stmt.where(Topic.created_at >= now - timedelta(hours=48))
    elif since == 'week':
        stmt = stmt.where(Topic.created_at >= now - timedelta(days=7))
    # 'all' = no date filter

    stmt = stmt.offset(offset).limit(limit)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [TopicOut.model_validate(topic) for topic in rows]


@router.post('/collect', response_model=CollectTopicsResponse)
async def collect_topics(
    payload: CollectTopicsRequest = Body(default=CollectTopicsRequest()),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> CollectTopicsResponse:
    query = (payload.query or '').strip() if payload else None
    normalized_query = query if query and len(query) >= 2 else None
    collector = TrendCollector()
    output = await collector.collect_and_store(db, query=normalized_query)

    await log_action(
        db,
        action='topics_collected',
        entity_type='system',
        entity_id='topics_collector',
        actor_id=current_user.id,
        details={**output, 'query': normalized_query},
    )
    await db.commit()
    return CollectTopicsResponse(**output)


@router.post('/{topic_id}/generate-draft', response_model=GenerateDraftResponse)
async def generate_draft(
    topic_id: int,
    payload: GenerateDraftRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> GenerateDraftResponse:
    topic_result = await db.execute(select(Topic).where(Topic.id == topic_id).limit(1))
    topic = topic_result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail='Topic not found')

    if payload.run_async:
        task = generate_draft_task.delay(topic_id=topic_id, actor_id=current_user.id)
        return GenerateDraftResponse(
            status='queued',
            message='Draft generation queued. Review drafts list shortly.',
            task_id=task.id,
        )

    service = ContentPipelineService()
    try:
        article = await service.generate_draft_for_topic(db, topic_id=topic_id, actor_id=current_user.id)
    except DuplicateTopicError:
        return GenerateDraftResponse(
            status='duplicate_rejected',
            message='Near-duplicate topic detected. Draft generation blocked.',
            article_id=None,
            task_id=None,
        )
    except RuntimeError as exc:
        return GenerateDraftResponse(
            status='quality_rejected',
            message=str(exc),
            article_id=None,
            task_id=None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return GenerateDraftResponse(
        status='created',
        message='Draft created and awaiting human review.',
        article_id=article.id,
    )


@router.post('/generate-draft-from-url', response_model=GenerateDraftResponse)
async def generate_draft_from_url(
    payload: GenerateDraftFromUrlRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> GenerateDraftResponse:
    source_url = payload.url.strip()
    if not source_url:
        raise HTTPException(status_code=400, detail='URL is required')

    if payload.run_async:
        task = generate_draft_from_url_task.delay(source_url=source_url, actor_id=current_user.id)
        return GenerateDraftResponse(
            status='queued',
            message='URL draft generation queued. Review drafts list shortly.',
            task_id=task.id,
        )

    service = ContentPipelineService()
    try:
        article = await service.generate_draft_from_url(db, source_url=source_url, actor_id=current_user.id)
    except DuplicateTopicError:
        return GenerateDraftResponse(
            status='duplicate_rejected',
            message='Near-duplicate topic detected. Draft generation blocked.',
            article_id=None,
            task_id=None,
        )
    except RuntimeError as exc:
        return GenerateDraftResponse(
            status='quality_rejected',
            message=str(exc),
            article_id=None,
            task_id=None,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return GenerateDraftResponse(
        status='created',
        message='Draft created from URL and awaiting human review.',
        article_id=article.id,
    )


@router.delete('/{topic_id}', response_model=MessageResponse)
async def delete_topic(
    topic_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_reviewer),
) -> MessageResponse:
    topic_result = await db.execute(select(Topic).where(Topic.id == topic_id).limit(1))
    topic = topic_result.scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail='Topic not found')

    if topic.status == TopicStatus.PROCESSED:
        raise HTTPException(status_code=400, detail='Cannot delete a topic that has been processed into a draft.')

    await db.delete(topic)
    await log_action(
        db,
        action='topic_deleted',
        entity_type='topic',
        entity_id=str(topic_id),
        actor_id=current_user.id,
    )
    await db.commit()
    return MessageResponse(message=f'Topic {topic_id} deleted.')
