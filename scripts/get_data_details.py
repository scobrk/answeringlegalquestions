"""
Get actual data from Supabase and display results
"""

import os
from supabase import create_client, Client
import logging
import json

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

def get_data_stats():
    """Get detailed data statistics"""
    try:
        # Check if table exists and has data
        sql = """
        SELECT
            COUNT(*) as total_records,
            COUNT(DISTINCT revenue_type) as revenue_types,
            COUNT(DISTINCT act_name) as acts,
            AVG(LENGTH(content)) as avg_content_length
        FROM nsw_documents;
        """
        result = supabase.rpc('execute_sql', {'query': sql}).execute()
        print(f"Data Stats: {result.data}")

        # Get revenue types
        sql_revenue = """
        SELECT revenue_type, COUNT(*) as count
        FROM nsw_documents
        GROUP BY revenue_type
        ORDER BY count DESC
        LIMIT 10;
        """
        revenue_result = supabase.rpc('execute_sql', {'query': sql_revenue}).execute()
        print(f"Top Revenue Types: {revenue_result.data}")

        # Get some sample records
        sql_sample = """
        SELECT id, act_name, revenue_type, section_title, LENGTH(content) as content_length
        FROM nsw_documents
        ORDER BY id
        LIMIT 5;
        """
        sample_result = supabase.rpc('execute_sql', {'query': sql_sample}).execute()
        print(f"Sample Records: {sample_result.data}")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to get data stats: {e}")
        return False

def check_table_visibility():
    """Check why table isn't visible in dashboard"""
    try:
        # Check table owner
        sql = """
        SELECT schemaname, tablename, tableowner, hasindexes, hasrules, hastriggers
        FROM pg_tables
        WHERE tablename = 'nsw_documents';
        """
        result = supabase.rpc('execute_sql', {'query': sql}).execute()
        print(f"Table Info: {result.data}")

        # Check if RLS is enabled
        sql_rls = """
        SELECT schemaname, tablename, rowsecurity
        FROM pg_tables
        WHERE tablename = 'nsw_documents';
        """
        rls_result = supabase.rpc('execute_sql', {'query': sql_rls}).execute()
        print(f"RLS Status: {rls_result.data}")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to check table visibility: {e}")
        return False

def fix_table_visibility():
    """Try to fix table visibility for dashboard"""
    try:
        # Disable RLS for now to make table visible
        sql_commands = [
            "ALTER TABLE nsw_documents DISABLE ROW LEVEL SECURITY;",
            # Add explicit grants for dashboard access
            "GRANT ALL ON TABLE nsw_documents TO postgres;",
            "GRANT ALL ON TABLE nsw_documents TO service_role;",
            # Force schema cache reload
            "NOTIFY pgrst, 'reload schema';"
        ]

        for sql in sql_commands:
            result = supabase.rpc('execute_sql', {'query': sql}).execute()
            print(f"Executed: {sql[:50]}... Result: Success")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix table visibility: {e}")
        return False

if __name__ == "__main__":
    logger.info("🔍 Getting detailed Supabase data info...")

    print("\n=== DATA STATISTICS ===")
    get_data_stats()

    print("\n=== TABLE VISIBILITY ===")
    check_table_visibility()

    print("\n=== FIXING VISIBILITY ===")
    fix_table_visibility()

    print("\n=== RE-CHECKING AFTER FIX ===")
    get_data_stats()