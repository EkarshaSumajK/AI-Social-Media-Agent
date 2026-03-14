import asyncio
from collections.abc import Callable, Coroutine
from contextlib import suppress
from typing import Any

from celery.signals import worker_shutdown
from celery.app.task import Task
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.celery_app import celery_app
from app.core.config import get_settings
from app.core.database import SessionLocal, engine
from app.services.article_service import ArticleService
from app.services.content_pipeline_service import ContentPipelineService, DuplicateTopicError
from app.services.lock_service import LockUnavailableError
from app.services.trend_collector_service import TrendCollector

_worker_loop: asyncio.AbstractEventLoop | None = None
ProgressCallback = Callable[[str, int, str], None]
settings = get_settings()


def _get_worker_loop() -> asyncio.AbstractEventLoop:
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop


def _run_async(coro: Coroutine[object, object, dict]) -> dict:
    loop = _get_worker_loop()
    return loop.run_until_complete(coro)


def _publish_progress(task: Task, *, stage: str, progress: int, message: str) -> None:
    task.update_state(
        state='STARTED',
        meta={
            'stage': stage,
            'progress': max(0, min(100, progress)),
            'message': message,
        },
    )


@celery_app.task(
    name='app.workers.tasks.collect_topics_task',
    autoretry_for=(OSError, SQLAlchemyError),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def collect_topics_task() -> dict:
    return _run_async(_collect_topics())


async def _collect_topics() -> dict:
    async with SessionLocal() as db:
        # Set search_path for schema isolation
        await db.execute(text(f"SET search_path TO {settings.database_schema}, public"))
        collector = TrendCollector()
        return await collector.collect_and_store(db)


@celery_app.task(
    bind=True,
    name='app.workers.tasks.generate_draft_task',
    autoretry_for=(OSError, SQLAlchemyError),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def generate_draft_task(self: Task, topic_id: int, actor_id: int | None = None) -> dict:
    callback: ProgressCallback = lambda stage, progress, message: _publish_progress(
        self,
        stage=stage,
        progress=progress,
        message=message,
    )
    _publish_progress(self, stage='queued', progress=5, message='Draft task accepted and waiting for worker.')
    return _run_async(_generate_draft(topic_id, actor_id, progress_callback=callback))


async def _generate_draft(
    topic_id: int,
    actor_id: int | None,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    async with SessionLocal() as db:
        # Set search_path for schema isolation
        await db.execute(text(f"SET search_path TO {settings.database_schema}, public"))
        pipeline = ContentPipelineService()
        try:
            if progress_callback:
                progress_callback('loading_topic', 15, 'Loading topic and checking duplicates.')
            article = await pipeline.generate_draft_for_topic(
                db,
                topic_id=topic_id,
                actor_id=actor_id,
                progress_callback=progress_callback,
            )
        except DuplicateTopicError as exc:
            return {
                'status': 'duplicate_rejected',
                'topic_id': topic_id,
                'matched_topic_id': exc.matched_topic_id,
                'similarity': exc.score,
                'stage': 'completed',
                'progress': 100,
            }
        except LockUnavailableError as exc:
            return {
                'status': 'already_running',
                'topic_id': topic_id,
                'error': str(exc),
                'stage': 'completed',
                'progress': 100,
            }
        except RuntimeError as exc:
            return {
                'status': 'quality_rejected',
                'topic_id': topic_id,
                'error': str(exc),
                'stage': 'completed',
                'progress': 100,
            }

        return {
            'status': 'created',
            'article_id': article.id,
            'topic_id': topic_id,
            'stage': 'completed',
            'progress': 100,
        }


@celery_app.task(
    bind=True,
    name='app.workers.tasks.generate_draft_from_url_task',
    autoretry_for=(OSError, SQLAlchemyError),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def generate_draft_from_url_task(self: Task, source_url: str, actor_id: int | None = None) -> dict:
    callback: ProgressCallback = lambda stage, progress, message: _publish_progress(
        self,
        stage=stage,
        progress=progress,
        message=message,
    )
    _publish_progress(self, stage='queued', progress=5, message='URL draft task accepted and waiting for worker.')
    return _run_async(_generate_draft_from_url(source_url, actor_id, progress_callback=callback))


async def _generate_draft_from_url(
    source_url: str,
    actor_id: int | None,
    progress_callback: ProgressCallback | None = None,
) -> dict:
    async with SessionLocal() as db:
        # Set search_path for schema isolation
        await db.execute(text(f"SET search_path TO {settings.database_schema}, public"))
        pipeline = ContentPipelineService()
        try:
            if progress_callback:
                progress_callback('validating_url', 10, 'Validating article URL.')
            article = await pipeline.generate_draft_from_url(
                db,
                source_url=source_url,
                actor_id=actor_id,
                progress_callback=progress_callback,
            )
        except DuplicateTopicError as exc:
            return {
                'status': 'duplicate_rejected',
                'source_url': source_url,
                'matched_topic_id': exc.matched_topic_id,
                'similarity': exc.score,
                'stage': 'completed',
                'progress': 100,
            }
        except LockUnavailableError as exc:
            return {
                'status': 'already_running',
                'source_url': source_url,
                'error': str(exc),
                'stage': 'completed',
                'progress': 100,
            }
        except RuntimeError as exc:
            return {
                'status': 'quality_rejected',
                'source_url': source_url,
                'error': str(exc),
                'stage': 'completed',
                'progress': 100,
            }

        return {
            'status': 'created',
            'article_id': article.id,
            'source_url': source_url,
            'stage': 'completed',
            'progress': 100,
        }


@celery_app.task(
    name='app.workers.tasks.publish_social_posts_task',
    autoretry_for=(OSError, SQLAlchemyError),
    retry_backoff=True,
    retry_backoff_max=120,
    retry_jitter=True,
    retry_kwargs={'max_retries': 5},
)
def publish_social_posts_task(article_id: int, actor_id: int | None = None) -> dict:
    return _run_async(_publish_social(article_id, actor_id))


async def _publish_social(article_id: int, actor_id: int | None) -> dict:
    async with SessionLocal() as db:
        # Set search_path for schema isolation
        await db.execute(text(f"SET search_path TO {settings.database_schema}, public"))
        service = ArticleService()
        article, outcomes = await service.publish_social(db, article_id=article_id, actor_id=actor_id)
        return {'article_id': article.id, 'status': article.status.value, 'outcomes': outcomes}


@worker_shutdown.connect
def _shutdown_async_resources(**_: object) -> None:
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        return

    with suppress(Exception):
        _worker_loop.run_until_complete(engine.dispose())
    _worker_loop.close()
