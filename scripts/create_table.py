"""
Create the nsw_documents table in Supabase
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

def create_nsw_documents_table():
    """Create the nsw_documents table with pgvector"""
    sql_commands = [
        # Enable pgvector extension
        "CREATE EXTENSION IF NOT EXISTS vector;",

        # Create documents table
        """
        CREATE TABLE IF NOT EXISTS nsw_documents (
            id SERIAL PRIMARY KEY,
            act_name TEXT NOT NULL,
            content TEXT NOT NULL,
            revenue_type TEXT NOT NULL,
            section_title TEXT,
            section_number TEXT,
            category TEXT,
            file_path TEXT,
            embedding vector(768),
            metadata JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,

        # Create basic indexes (skip vector index for now)
        "CREATE INDEX IF NOT EXISTS idx_nsw_documents_revenue_type ON nsw_documents (revenue_type);",
        "CREATE INDEX IF NOT EXISTS idx_nsw_documents_act_name ON nsw_documents (act_name);",
    ]

    for i, sql in enumerate(sql_commands):
        try:
            logger.info(f"Executing SQL command {i+1}/{len(sql_commands)}")
            result = supabase.rpc('execute_sql', {'query': sql})
            logger.info(f"✅ SQL command {i+1} executed successfully")
        except Exception as e:
            logger.error(f"❌ Error executing SQL command {i+1}: {e}")
            if "already exists" not in str(e):
                return False

    return True

def test_table_access():
    """Test if we can access the created table"""
    try:
        # Try to insert a test record
        test_record = {
            'act_name': 'Test Act',
            'content': 'Test content',
            'revenue_type': 'test',
            'section_title': 'Test Section',
            'section_number': '1',
            'category': 'test',
            'file_path': '/test',
            'metadata': {'test': True}
        }

        result = supabase.table('nsw_documents').insert([test_record]).execute()
        logger.info(f"✅ Test record inserted: {result.data}")

        # Clean up
        supabase.table('nsw_documents').delete().eq('act_name', 'Test Act').execute()
        logger.info("✅ Test record deleted")

        return True
    except Exception as e:
        logger.error(f"❌ Table access failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("🚀 Creating NSW documents table...")

    if create_nsw_documents_table():
        logger.info("✅ Table creation completed")

        # Wait a moment for the schema cache to update
        import time
        time.sleep(2)

        if test_table_access():
            logger.info("✅ Table is accessible and ready for data upload")
        else:
            logger.error("❌ Table created but not accessible via REST API")
    else:
        logger.error("❌ Table creation failed")