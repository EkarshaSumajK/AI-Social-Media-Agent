from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from redis.exceptions import ConnectionError, TimeoutError

from app.core.redis import get_redis_client, reset_redis_pools


class LockUnavailableError(RuntimeError):
    pass


@asynccontextmanager
async def redis_lock(key: str, *, ttl_seconds: int = 300, max_retries: int = 3):
    """
    Acquire a distributed Redis lock with retry logic.
    
    Args:
        key: Lock identifier
        ttl_seconds: Lock timeout in seconds
        max_retries: Maximum connection retry attempts
    """
    token = str(uuid.uuid4())
    lock_key = f'lock:{key}'
    redis = None
    
    for attempt in range(max_retries + 1):
        try:
            redis = get_redis_client()
            
            acquired = await redis.set(lock_key, token, ex=ttl_seconds, nx=True)
            if not acquired:
                raise LockUnavailableError(f'Unable to acquire lock for {key}')
            
            break
            
        except (ConnectionError, TimeoutError) as e:
            if attempt == max_retries:
                raise ConnectionError(f'Failed to acquire lock after {max_retries + 1} attempts: {e}')
            
            # Reset the pools on connection errors to force reconnection
            await reset_redis_pools()
            continue

    try:
        yield
    finally:
        if redis:
            try:
                # Only delete if we still own the lock
                current = await redis.get(lock_key)
                if current == token:
                    await redis.delete(lock_key)
            except (ConnectionError, TimeoutError):
                # If we can't release the lock, it will expire naturally
                pass
            finally:
                await redis.aclose()
