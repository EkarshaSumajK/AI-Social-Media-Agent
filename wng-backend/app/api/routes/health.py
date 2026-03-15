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
    error_msg = None

    try:
        # Check Redis connection with SSL support for Upstash
        redis_url = settings.redis_url
        
        # Configure SSL for Upstash - use rediss:// protocol
        if 'upstash.io' in redis_url and redis_url.startswith('redis://'):
            redis_url = redis_url.replace('redis://', 'rediss://')
        
        # For rediss://, the library handles SSL automatically
        r = aioredis.from_url(
            redis_url,
            socket_connect_timeout=3,
            decode_responses=False
        )
        
        await r.ping()
        await r.aclose()
        redis_ok = True
        
        # Check Celery workers using Celery's inspect API
        try:
            from app.core.celery_app import celery_app
            inspect = celery_app.control.inspect(timeout=2.0)
            active_workers = inspect.active()
            celery_ok = active_workers is not None and len(active_workers) > 0
        except Exception as celery_err:
            print(f"Celery inspect error: {celery_err}")
            # Fallback: check for Celery-related keys in Redis
            redis_url_check = settings.redis_url
            if 'upstash.io' in redis_url_check and redis_url_check.startswith('redis://'):
                redis_url_check = redis_url_check.replace('redis://', 'rediss://')
            
            r2 = aioredis.from_url(
                redis_url_check,
                socket_connect_timeout=3,
                decode_responses=False
            )
            
            keys = await r2.keys('_kombu.binding.*')
            await r2.aclose()
            celery_ok = len(keys) > 0
            print(f"Celery fallback check: {celery_ok}, keys found: {len(keys)}")
    except Exception as e:
        # Log error for debugging but don't fail health check
        error_msg = str(e)
        print(f"Health check error: {e}")

    result = {
        'status': 'healthy',
        'backend': True,
        'redis': redis_ok,
        'celery': celery_ok,
    }
    
    if error_msg:
        result['error'] = error_msg
    
    print(f"Health check result: {result}")
    return result
