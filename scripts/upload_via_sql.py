"""
Upload documents to Supabase using direct SQL INSERT statements
"""

import os
import json
import numpy as np
from pathlib import Path
from supabase import create_client, Client
import pickle
from typing import List, Dict
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

def load_hybrid_cache_data():
    """Load documents and embeddings from hybrid cache"""
    cache_dir = Path("data/hybrid_cache")

    # Load documents
    with open(cache_dir / "documents.pkl", 'rb') as f:
        documents = pickle.load(f)

    # Load metadata
    with open(cache_dir / "metadata.json", 'r') as f:
        metadata_list = json.load(f)

    # Load embeddings
    embeddings = np.load(cache_dir / "embeddings.npy")

    logger.info(f"Loaded {len(documents)} documents with {embeddings.shape} embeddings")
    return documents, metadata_list, embeddings

def create_table_with_permissions():
    """Create table with proper permissions"""
    sql_commands = [
        # Enable pgvector extension
        "CREATE EXTENSION IF NOT EXISTS vector;",

        # Drop table if it exists to start fresh
        "DROP TABLE IF EXISTS nsw_documents;",

        # Create documents table
        """
        CREATE TABLE nsw_documents (
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

        # Grant permissions explicitly
        "GRANT ALL ON TABLE nsw_documents TO anon, authenticated;",
        "GRANT USAGE, SELECT ON SEQUENCE nsw_documents_id_seq TO anon, authenticated;",

        # Create basic indexes
        "CREATE INDEX IF NOT EXISTS idx_nsw_documents_revenue_type ON nsw_documents (revenue_type);",
        "CREATE INDEX IF NOT EXISTS idx_nsw_documents_act_name ON nsw_documents (act_name);"
    ]

    for i, sql in enumerate(sql_commands):
        try:
            logger.info(f"Executing SQL command {i+1}/{len(sql_commands)}")
            result = supabase.rpc('execute_sql', {'query': sql})
            logger.info(f"✅ SQL command {i+1} executed successfully")
        except Exception as e:
            logger.error(f"❌ Error executing SQL command {i+1}: {e}")
            return False

    return True

def upload_batch_via_sql(batch_data: List[Dict], batch_num: int, total_batches: int):
    """Upload a batch of documents using SQL INSERT"""

    # Build SQL INSERT statement
    values_list = []
    for doc in batch_data:
        # Escape single quotes in text fields (handle None values)
        act_name = str(doc['act_name']).replace("'", "''")
        content = str(doc['content']).replace("'", "''")
        revenue_type = str(doc['revenue_type']).replace("'", "''")
        section_title = str(doc.get('section_title') or '').replace("'", "''")
        section_number = str(doc.get('section_number') or '').replace("'", "''")
        category = str(doc.get('category') or '').replace("'", "''")
        file_path = str(doc.get('file_path') or '').replace("'", "''")

        # Convert embedding to PostgreSQL vector format
        embedding_str = f"'[{','.join(map(str, doc['embedding']))}]'"

        # Convert metadata to JSON string
        metadata_str = json.dumps(doc['metadata']).replace("'", "''")

        value = f"('{act_name}', '{content}', '{revenue_type}', '{section_title}', '{section_number}', '{category}', '{file_path}', {embedding_str}::vector, '{metadata_str}'::jsonb)"
        values_list.append(value)

    # Create INSERT statement
    sql = f"""
    INSERT INTO nsw_documents (act_name, content, revenue_type, section_title, section_number, category, file_path, embedding, metadata)
    VALUES {', '.join(values_list)};
    """

    try:
        result = supabase.rpc('execute_sql', {'query': sql})
        logger.info(f"✅ Uploaded batch {batch_num}/{total_batches} ({len(batch_data)} documents)")
        return True
    except Exception as e:
        logger.error(f"❌ Error uploading batch {batch_num}: {e}")
        # Try smaller batch if needed
        if len(batch_data) > 1:
            logger.info(f"Trying to upload batch {batch_num} one record at a time...")
            for i, record in enumerate(batch_data):
                try:
                    upload_batch_via_sql([record], f"{batch_num}.{i+1}", f"{total_batches}")
                except Exception as e2:
                    logger.error(f"Failed to upload individual record {i+1}: {e2}")
        return False

def upload_documents_to_supabase(documents: List[str], metadata_list: List[Dict], embeddings: np.ndarray):
    """Upload documents with embeddings to Supabase using SQL"""

    # Prepare batch upload
    batch_size = 10  # Smaller batches for SQL approach
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_metadata = metadata_list[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        batch_data = []
        for doc, meta, embedding in zip(batch_docs, batch_metadata, batch_embeddings):
            # Convert numpy array to list for JSON serialization
            embedding_list = embedding.tolist()

            record = {
                'act_name': meta.get('act_name', 'unknown'),
                'content': doc,
                'revenue_type': meta.get('revenue_type', 'general'),
                'section_title': meta.get('section_title', ''),
                'section_number': meta.get('section_number', ''),
                'category': meta.get('category', ''),
                'file_path': meta.get('file_path', ''),
                'embedding': embedding_list,
                'metadata': {
                    'file_size': meta.get('file_size', 0),
                    'section_index': meta.get('section_index', 0),
                    'original_metadata': meta
                }
            }
            batch_data.append(record)

        upload_batch_via_sql(batch_data, i//batch_size + 1, total_batches)

def main():
    """Main upload function"""
    logger.info("🚀 Starting SQL-based document upload to Supabase")

    # Step 1: Create table with proper permissions
    logger.info("📋 Creating table with permissions...")
    if not create_table_with_permissions():
        logger.error("❌ Failed to create table")
        return

    # Step 2: Load documents
    logger.info("📄 Loading documents from hybrid cache...")
    documents, metadata_list, embeddings = load_hybrid_cache_data()

    # Step 3: Upload via SQL
    logger.info("📤 Uploading documents via SQL INSERT...")
    upload_documents_to_supabase(documents, metadata_list, embeddings)

    logger.info("✅ Upload process complete!")

if __name__ == "__main__":
    main()