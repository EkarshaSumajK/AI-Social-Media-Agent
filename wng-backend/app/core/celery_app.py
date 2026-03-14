import sys

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    'wng_content_workers',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['app.workers.tasks'],
)

celery_app.conf.update(
    timezone='UTC',
    task_acks_late=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
)

# Celery prefork is unreliable on Windows; force solo for local stability.
if sys.platform.startswith('win'):
    celery_app.conf.update(
        worker_pool='solo',
        worker_concurrency=1,
    )

celery_app.conf.beat_schedule = {
    'collect-trending-topics-morning': {
        'task': 'app.workers.tasks.collect_topics_task',
        'schedule': crontab(hour=7, minute=0),
    },
    'collect-trending-topics-afternoon': {
        'task': 'app.workers.tasks.collect_topics_task',
        'schedule': crontab(hour=13, minute=0),
    },
    'collect-trending-topics-evening': {
        'task': 'app.workers.tasks.collect_topics_task',
        'schedule': crontab(hour=20, minute=0),
    },
}
