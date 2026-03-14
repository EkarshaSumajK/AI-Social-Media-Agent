#!/usr/bin/env python3
"""
Debug the database URL processing.
"""
import sys
from pathlib import Path

# Add the app to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.core.database import _async_database_url

def debug_db_url():
    """Debug database URL processing."""
    try:
        settings = get_settings()
        print(f"Original URL: {settings.database_url_dashboard}")
        
        processed_url = _async_database_url()
        print(f"Processed URL: {processed_url}")
        
        # Check if the URL looks correct
        if 'asyncpg' in processed_url:
            print("✅ URL contains asyncpg driver")
        else:
            print("❌ URL missing asyncpg driver")
            
        return True
        
    except Exception as e:
        print(f"❌ URL processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = debug_db_url()
    sys.exit(0 if success else 1)