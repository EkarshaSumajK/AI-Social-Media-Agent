#!/usr/bin/env python3
"""
Check what's in the database to debug the enum issue.
"""
import asyncio
import sys
from pathlib import Path

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import SessionLocal
from app.core.config import get_settings
from sqlalchemy import text

async def check_database():
    """Check database contents."""
    try:
        settings = get_settings()
        print(f"✅ Config loaded successfully")
        print(f"   Database: {settings.database_url_dashboard}")
        print(f"   Schema: {settings.database_schema}")
        
        async with SessionLocal() as session:
            # Set search_path
            await session.execute(text(f"SET search_path TO {settings.database_schema}, public"))
            
            # Check if users table exists
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = :schema AND table_name = 'users'
            """), {"schema": settings.database_schema})
            
            if result.fetchone():
                print("✅ Users table exists")
                
                # Check users in the table
                result = await session.execute(text("SELECT email, role FROM users LIMIT 5"))
                users = result.fetchall()
                print(f"📊 Found {len(users)} users:")
                for user in users:
                    print(f"   - {user.email}: {user.role} (type: {type(user.role)})")
                    
                # Check enum type definition
                result = await session.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'userrole'
                    ORDER BY e.enumsortorder
                """))
                enum_values = result.fetchall()
                print(f"🔍 UserRole enum values in database:")
                for value in enum_values:
                    print(f"   - '{value.enumlabel}'")
                    
            else:
                print("❌ Users table does not exist")
                
                # List all tables
                result = await session.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = :schema
                """), {"schema": settings.database_schema})
                tables = result.fetchall()
                print(f"📋 Available tables in schema '{settings.database_schema}':")
                for table in tables:
                    print(f"   - {table.table_name}")
                
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(check_database())
    sys.exit(0 if success else 1)