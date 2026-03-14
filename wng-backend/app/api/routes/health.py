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
        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        await r.ping()
        await r.aclose()
        redis_ok = True
        # Check if any Celery worker heartbeat keys exist in Redis
        r2 = aioredis.from_url(settings.redis_url, socket_connect_timeout=2)
        keys = await r2.keys('celery*')
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
