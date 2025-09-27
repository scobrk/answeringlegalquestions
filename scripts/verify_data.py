"""
Verify data exists in Supabase and check table status
"""

import os
from supabase import create_client, Client
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = "https://mllidxvkwnwnmjipmhdv.supabase.co"
SUPABASE_KEY = "sb_secret_cwDOerlN0w6UJ6WqdFN3uw_bkkDKVO1"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def check_data_via_sql():
    """Check data using direct SQL queries"""
    try:
        # Check if table exists and has data
        sql = """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT revenue_type) as revenue_types,
            COUNT(DISTINCT act_name) as acts
        FROM nsw_documents;
        """
        result = supabase.rpc('execute_sql', {'query': sql})
        logger.info(f"✅ Data check via SQL: {result}")

        # Get some sample data
        sql_sample = """
        SELECT id, act_name, revenue_type, section_title
        FROM nsw_documents
        LIMIT 5;
        """
        sample = supabase.rpc('execute_sql', {'query': sql_sample})
        logger.info(f"✅ Sample data: {sample}")

        return True
    except Exception as e:
        logger.error(f"❌ SQL data check failed: {e}")
        return False

def check_table_schema():
    """Check table schema and permissions"""
    try:
        sql = """
        SELECT column_name, data_type, is_nullable
        FROM information_schema.columns
        WHERE table_name = 'nsw_documents'
        ORDER BY ordinal_position;
        """
        result = supabase.rpc('execute_sql', {'query': sql})
        logger.info(f"✅ Table schema: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Schema check failed: {e}")
        return False

def check_permissions():
    """Check table permissions"""
    try:
        sql = """
        SELECT grantee, privilege_type
        FROM information_schema.role_table_grants
        WHERE table_name = 'nsw_documents';
        """
        result = supabase.rpc('execute_sql', {'query': sql})
        logger.info(f"✅ Table permissions: {result}")
        return True
    except Exception as e:
        logger.error(f"❌ Permissions check failed: {e}")
        return False

def check_rest_api_access():
    """Try to access via REST API"""
    try:
        result = supabase.table('nsw_documents').select('count', count='exact').execute()
        logger.info(f"✅ REST API access successful: {result.count} records")
        return True
    except Exception as e:
        logger.error(f"❌ REST API access failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Verifying Supabase data...")

    logger.info("1. Checking data via SQL...")
    check_data_via_sql()

    logger.info("2. Checking table schema...")
    check_table_schema()

    logger.info("3. Checking permissions...")
    check_permissions()

    logger.info("4. Checking REST API access...")
    check_rest_api_access()