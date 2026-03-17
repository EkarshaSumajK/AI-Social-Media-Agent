from fastapi import APIRouter

from app.core.config import get_settings
from app.core.redis import ping_redis, get_redis_client

router = APIRouter()
settings = get_settings()


@router.get('/health')
async def health() -> dict:
    redis_ok = False
    celery_ok = False
    error_msg = None

    try:
        # Check Redis connection using shared utility
        redis_ok = await ping_redis(timeout=3.0)
        
        # Check Celery workers using Celery's inspect API
        try:
            from app.core.celery_app import celery_app
            inspect = celery_app.control.inspect(timeout=2.0)
            active_workers = inspect.active()
            celery_ok = active_workers is not None and len(active_workers) > 0
        except Exception as celery_err:
            print(f"Celery inspect error: {celery_err}")
            # Fallback: check for Celery-related keys in Redis
            try:
                redis = get_redis_client(decode_responses=False)
                keys = await redis.keys('_kombu.binding.*')
                await redis.aclose()
                celery_ok = len(keys) > 0
                print(f"Celery fallback check: {celery_ok}, keys found: {len(keys)}")
            except Exception as redis_err:
                print(f"Celery fallback Redis check failed: {redis_err}")
                celery_ok = False
                
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
