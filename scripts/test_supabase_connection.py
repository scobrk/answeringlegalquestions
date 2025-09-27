"""
Test Supabase connection and basic table operations
"""

import os
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Validate required environment variables
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY environment variable is required")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_connection():
    """Test basic connection to Supabase"""
    try:
        # Try to execute a simple query
        result = supabase.rpc('execute_sql', {'query': 'SELECT 1 as test'})
        logger.info(f"✅ Connection successful: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        return False

def test_table_exists():
    """Check if nsw_documents table exists"""
    try:
        result = supabase.table('nsw_documents').select('count', count='exact').execute()
        logger.info(f"✅ Table exists with {result.count} records")
        return True
    except Exception as e:
        logger.error(f"❌ Table check failed: {e}")
        return False

def create_simple_table():
    """Try to create a simple test table"""
    try:
        sql = """
        CREATE TABLE IF NOT EXISTS test_table (
            id SERIAL PRIMARY KEY,
            name TEXT,
            data JSONB
        );
        """
        result = supabase.rpc('execute_sql', {'query': sql})
        logger.info(f"✅ Test table created: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Table creation failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🧪 Testing Supabase connection...")

    if test_connection():
        logger.info("✅ Basic connection works")

        if test_table_exists():
            logger.info("✅ NSW documents table exists")
        else:
            logger.info("❌ NSW documents table not found")
            logger.info("Trying to create a simple test table...")
            create_simple_table()
    else:
        logger.error("❌ Cannot connect to Supabase")