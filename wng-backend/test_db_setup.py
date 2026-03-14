#!/usr/bin/env python3
"""
Quick test to verify database setup works without Alembic.
"""
import asyncio
import sys
from pathlib import Path

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import verify_schema_ready, SessionLocal
from app.core.config import get_settings

async def test_db_setup():
    """Test that database setup works."""
    try:
        settings = get_settings()
        print(f"✅ Config loaded successfully")
        print(f"   Database: {settings.database_url_dashboard}")
        print(f"   Schema: {settings.database_schema}")
        
        print("🔄 Testing database connection and schema setup...")
        await verify_schema_ready()
        print("✅ Database schema is ready!")
        
        # Test a simple query
        async with SessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row.test == 1:
                print("✅ Database query test passed!")
            else:
                print("❌ Database query test failed!")
                return False
                
        print("🎉 All database tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_db_setup())
    sys.exit(0 if success else 1)