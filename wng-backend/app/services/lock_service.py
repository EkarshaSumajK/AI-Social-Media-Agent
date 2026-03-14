from __future__ import annotations

import uuid
from contextlib import asynccontextmanager

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()


class LockUnavailableError(RuntimeError):
    pass


@asynccontextmanager
async def redis_lock(key: str, *, ttl_seconds: int = 300):
    token = str(uuid.uuid4())
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    lock_key = f'lock:{key}'

    acquired = await redis.set(lock_key, token, ex=ttl_seconds, nx=True)
    if not acquired:
        await redis.aclose()
        raise LockUnavailableError(f'Unable to acquire lock for {key}')

    try:
        yield
    finally:
        current = await redis.get(lock_key)
        if current == token:
            await redis.delete(lock_key)
        await redis.aclose()
