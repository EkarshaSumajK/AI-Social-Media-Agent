import sys
import ssl

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

# Configure Redis URL with SSL for Upstash
redis_url = settings.redis_url

# Upstash requires SSL - ensure we use rediss:// and configure SSL
if redis_url and 'upstash.io' in redis_url:
    # Replace redis:// with rediss:// for SSL
    if redis_url.startswith('redis://'):
        redis_url = redis_url.replace('redis://', 'rediss://')
    
    # Configure broker with SSL
    broker_use_ssl = {
        'ssl_cert_reqs': ssl.CERT_NONE,
        'ssl_ca_certs': None,
        'ssl_certfile': None,
        'ssl_keyfile': None,
    }
else:
    broker_use_ssl = None

celery_app = Celery(
    'wng_content_workers',
    broker=redis_url,
    backend=redis_url,
    include=['app.workers.tasks'],
)

celery_app.conf.update(
    timezone='UTC',
    task_acks_late=True,
    task_track_started=True,
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,
    result_backend_transport_options={
        'retry_on_timeout': True,
    },
    broker_transport_options={
        'retry_on_timeout': True,
    },
)

# Apply SSL configuration if needed
if broker_use_ssl:
    celery_app.conf.update(
        broker_use_ssl=broker_use_ssl,
        redis_backend_use_ssl=broker_use_ssl,
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
