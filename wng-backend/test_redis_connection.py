#!/usr/bin/env python3
"""
Test script to verify Redis connection and lock functionality.
Run this to test if the Redis connection issues are resolved.
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.redis import ping_redis, get_redis_client, reset_redis_pools
from app.services.lock_service import redis_lock, LockUnavailableError


async def test_redis_connection():
    """Test basic Redis connectivity."""
    print("Testing Redis connection...")
    
    try:
        success = await ping_redis(timeout=5.0)
        if success:
            print("✅ Redis connection successful")
            return True
        else:
            print("❌ Redis connection failed")
            return False
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        return False


async def test_redis_operations():
    """Test basic Redis operations."""
    print("\nTesting Redis operations...")
    
    try:
        redis = get_redis_client()
        
        # Test set/get
        await redis.set("test_key", "test_value", ex=10)
        value = await redis.get("test_key")
        
        if value == "test_value":
            print("✅ Redis set/get operations successful")
        else:
            print(f"❌ Redis set/get failed: expected 'test_value', got '{value}'")
            return False
        
        # Clean up
        await redis.delete("test_key")
        await redis.aclose()
        
        return True
        
    except Exception as e:
        print(f"❌ Redis operations error: {e}")
        return False


async def test_redis_lock():
    """Test Redis lock functionality."""
    print("\nTesting Redis lock...")
    
    try:
        # Test successful lock acquisition
        async with redis_lock("test_lock", ttl_seconds=10):
            print("✅ Redis lock acquired successfully")
        
        print("✅ Redis lock released successfully")
        
        # Test lock contention
        try:
            async with redis_lock("test_lock_2", ttl_seconds=5):
                # Try to acquire the same lock (should fail)
                try:
                    async with redis_lock("test_lock_2", ttl_seconds=5):
                        print("❌ Lock contention test failed - second lock should not be acquired")
                        return False
                except LockUnavailableError:
                    print("✅ Lock contention test passed - second lock correctly rejected")
        except Exception as e:
            print(f"❌ Lock contention test error: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Redis lock error: {e}")
        return False


async def main():
    """Run all Redis tests."""
    print("🔧 Testing Redis connection and functionality...\n")
    
    tests = [
        test_redis_connection,
        test_redis_operations,
        test_redis_lock,
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Redis connection should be working properly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the Redis configuration and connection.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)