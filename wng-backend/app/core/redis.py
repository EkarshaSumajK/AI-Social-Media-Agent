"""
Shared Redis connection utilities with proper SSL configuration and connection pooling.
"""

import ssl
from typing import Optional

from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import ConnectionError, TimeoutError

from app.core.config import get_settings

settings = get_settings()

# Global connection pools
_redis_pool: Optional[ConnectionPool] = None
_redis_pool_no_decode: Optional[ConnectionPool] = None


def _create_redis_pool(decode_responses: bool = True) -> ConnectionPool:
    """Create a Redis connection pool with proper SSL configuration."""
    redis_url = settings.redis_url
    
    # Configure SSL for Upstash
    if redis_url and 'upstash.io' in redis_url:
        # Ensure we use rediss:// for SSL
        if redis_url.startswith('redis://'):
            redis_url = redis_url.replace('redis://', 'rediss://')
    
    # Use simple connection pool - redis-py handles SSL automatically for rediss://
    return ConnectionPool.from_url(
        redis_url,
        decode_responses=decode_responses,
        retry_on_timeout=True,
        health_check_interval=30,
        max_connections=20,
        socket_connect_timeout=10,
        socket_timeout=10,
    )


def get_redis_pool(decode_responses: bool = True) -> ConnectionPool:
    """Get or create a Redis connection pool."""
    global _redis_pool, _redis_pool_no_decode
    
    if decode_responses:
        if _redis_pool is None:
            _redis_pool = _create_redis_pool(decode_responses=True)
        return _redis_pool
    else:
        if _redis_pool_no_decode is None:
            _redis_pool_no_decode = _create_redis_pool(decode_responses=False)
        return _redis_pool_no_decode


def get_redis_client(decode_responses: bool = True) -> Redis:
    """Get a Redis client using the connection pool."""
    return Redis(connection_pool=get_redis_pool(decode_responses=decode_responses))


async def reset_redis_pools():
    """Reset connection pools to force reconnection."""
    global _redis_pool, _redis_pool_no_decode
    
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None
    
    if _redis_pool_no_decode:
        await _redis_pool_no_decode.aclose()
        _redis_pool_no_decode = None


async def ping_redis(timeout: float = 3.0) -> bool:
    """Test Redis connectivity."""
    try:
        redis = get_redis_client(decode_responses=False)
        await redis.ping()
        await redis.aclose()
        return True
    except (ConnectionError, TimeoutError):
        return False