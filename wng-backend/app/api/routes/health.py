from fastapi import APIRouter
import redis.asyncio as aioredis

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get('/health')
async def health() -> dict:
    redis_ok = False
    celery_ok = False

    try:
        # Check Redis connection
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        redis_ok = True
        
        # Check Celery workers using Celery's inspect API
        try:
            from app.core.celery_app import celery_app
            inspect = celery_app.control.inspect(timeout=2.0)
            active_workers = inspect.active()
            celery_ok = active_workers is not None and len(active_workers) > 0
        except Exception:
            # Fallback: check for Celery-related keys in Redis
            r2 = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
            # Celery workers create keys with patterns like:
            # - _kombu.binding.* (queue bindings)
            # - celery-task-meta-* (task results)
            # - unacked_* (unacked messages)
            keys = await r2.keys('_kombu.binding.*')
            await r2.aclose()
            celery_ok = len(keys) > 0
    except Exception:
        pass

    return {
        'status': 'healthy',
        'backend': True,
        'redis': redis_ok,
        'celery': celery_ok,
    }
