"""
Reload Supabase schema cache
"""

import os
from supabase import create_client, Client
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = "https://mllidxvkwnwnmjipmhdv.supabase.co"
SUPABASE_KEY = "sb_secret_cwDOerlN0w6UJ6WqdFN3uw_bkkDKVO1"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def reload_schema():
    """Try to reload the PostgREST schema cache"""
    try:
        # This should trigger a schema reload
        result = supabase.rpc('execute_sql', {'query': 'NOTIFY pgrst, \'reload schema\';'})
        logger.info(f"✅ Schema reload notification sent: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Schema reload failed: {e}")
        return False

def check_table_exists():
    """Check if table exists using direct SQL"""
    try:
        sql = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'nsw_documents'
        );
        """
        result = supabase.rpc('execute_sql', {'query': sql})
        logger.info(f"✅ Table existence check: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Table check failed: {e}")
        return False

def wait_and_test_access():
    """Wait for schema cache and test access"""
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_attempts} to access table...")
            result = supabase.table('nsw_documents').select('count', count='exact').execute()
            logger.info(f"✅ Table accessible! Records: {result.count}")
            return True
        except Exception as e:
            logger.info(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_attempts - 1:
                time.sleep(5)  # Wait 5 seconds between attempts

    return False

if __name__ == "__main__":
    logger.info("🔄 Reloading Supabase schema cache...")

    check_table_exists()
    reload_schema()

    logger.info("⏳ Waiting for schema cache to update...")
    if wait_and_test_access():
        logger.info("✅ Table is now accessible!")
    else:
        logger.error("❌ Table still not accessible after cache reload")