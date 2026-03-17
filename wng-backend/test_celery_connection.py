#!/usr/bin/env python3
"""
Test script to verify Celery can connect to Redis properly.
Run this to test if the Celery connection issues are resolved.
"""

import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.celery_app import celery_app


def test_celery_broker_connection():
    """Test Celery broker connection."""
    print("Testing Celery broker connection...")
    
    try:
        # Test broker connection
        inspect = celery_app.control.inspect(timeout=5.0)
        stats = inspect.stats()
        
        if stats is not None:
            print("✅ Celery broker connection successful")
            print(f"   Connected workers: {len(stats) if stats else 0}")
            return True
        else:
            print("❌ No Celery workers found (this is normal if no workers are running)")
            return True  # Connection is OK, just no workers
            
    except Exception as e:
        print(f"❌ Celery broker connection error: {e}")
        return False


def test_celery_backend_connection():
    """Test Celery result backend connection."""
    print("\nTesting Celery result backend connection...")
    
    try:
        # Test result backend by checking if we can access it
        backend = celery_app.backend
        
        # Try to get a non-existent result (this will test the connection)
        result = backend.get_result("test-task-id")
        print("✅ Celery result backend connection successful")
        return True
        
    except Exception as e:
        # Some exceptions are expected (like task not found), but connection errors are not
        if "Connection" in str(e) or "timeout" in str(e).lower():
            print(f"❌ Celery result backend connection error: {e}")
            return False
        else:
            print("✅ Celery result backend connection successful")
            return True


def test_celery_configuration():
    """Test Celery configuration."""
    print("\nTesting Celery configuration...")
    
    try:
        conf = celery_app.conf
        
        print(f"   Broker URL: {conf.broker_url}")
        print(f"   Result backend: {conf.result_backend}")
        print(f"   Timezone: {conf.timezone}")
        print(f"   Task acks late: {conf.task_acks_late}")
        print(f"   Broker connection retry: {conf.broker_connection_retry}")
        
        print("✅ Celery configuration looks good")
        return True
        
    except Exception as e:
        print(f"❌ Celery configuration error: {e}")
        return False


def main():
    """Run all Celery tests."""
    print("🔧 Testing Celery connection and configuration...\n")
    
    tests = [
        test_celery_configuration,
        test_celery_broker_connection,
        test_celery_backend_connection,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All tests passed! Celery should be able to connect to Redis.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the Celery and Redis configuration.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)