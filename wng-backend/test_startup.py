#!/usr/bin/env python3
"""
Test if the app can start without errors.
"""
import asyncio
import sys
from pathlib import Path

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.user_service import ensure_admin_user
from app.core.database import verify_schema_ready

async def test_startup():
    """Test the startup sequence."""
    try:
        print("🔄 Testing database schema...")
        await verify_schema_ready()
        
        print("🔄 Testing admin user creation...")
        await ensure_admin_user()
        
        print("✅ Startup test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Startup test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_startup())
    sys.exit(0 if success else 1)