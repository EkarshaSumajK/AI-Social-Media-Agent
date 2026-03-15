from fastapi import APIRouter
import redis.asyncio as aioredis
import ssl

from app.core.config import get_settings

router = APIRouter()
settings = get_settings()


@router.get('/health')
async def health() -> dict:
    redis_ok = False
    celery_ok = False

    try:
        # Check Redis connection with SSL support for Upstash
        redis_url = settings.redis_url
        
        # Configure SSL for Upstash
        if 'upstash.io' in redis_url:
            if redis_url.startswith('redis://'):
                redis_url = redis_url.replace('redis://', 'rediss://')
            
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            r = aioredis.from_url(
                redis_url,
                socket_connect_timeout=3,
                ssl=ssl_context
            )
        else:
            r = aioredis.from_url(redis_url, socket_connect_timeout=3)
        
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
            if 'upstash.io' in settings.redis_url:
                redis_url_check = settings.redis_url
                if redis_url_check.startswith('redis://'):
                    redis_url_check = redis_url_check.replace('redis://', 'rediss://')
                
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                
                r2 = aioredis.from_url(
                    redis_url_check,
                    socket_connect_timeout=3,
                    ssl=ssl_context
                )
            else:
                r2 = aioredis.from_url(settings.redis_url, socket_connect_timeout=3)
            
            keys = await r2.keys('_kombu.binding.*')
            await r2.aclose()
            celery_ok = len(keys) > 0
    except Exception as e:
        # Log error for debugging but don't fail health check
        print(f"Health check error: {e}")

    return {
        'status': 'healthy',
        'backend': True,
        'redis': redis_ok,
        'celery': celery_ok,
    }
