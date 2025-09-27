"""
Setup Supabase database schema and upload NSW legislation documents with embeddings
"""

import os
import json
import numpy as np
from pathlib import Path
from supabase import create_client, Client
import openai
from sentence_transformers import SentenceTransformer
import pickle
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase credentials - SECURITY: Use environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Validate required environment variables
if not SUPABASE_URL:
    raise ValueError("SUPABASE_URL environment variable is required")
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_KEY environment variable is required")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def create_database_schema():
    """Create the database schema with pgvector extension and tables"""

    # First, try to create the table using Supabase REST API directly
    try:
        # Check if table already exists by trying to query it
        result = supabase.table('nsw_documents').select('id').limit(1).execute()
        logger.info("Table 'nsw_documents' already exists")
        return
    except Exception as e:
        logger.info(f"Table doesn't exist yet, will create it: {e}")

    # Since we can't use SQL directly, let's create a simple schema first
    # We'll use the Supabase dashboard or try a different approach
    logger.info("Creating table schema using insert operation to trigger table creation...")

    # Try to insert a dummy record to create the table structure
    try:
        dummy_record = {
            'act_name': 'Test Act',
            'content': 'Test content for schema creation',
            'revenue_type': 'test',
            'section_title': 'Test Section',
            'section_number': '1',
            'category': 'test',
            'file_path': '/test',
            'metadata': {'test': True}
        }

        # This will likely fail but may help us understand the schema requirements
        result = supabase.table('nsw_documents').insert([dummy_record]).execute()
        logger.info("Table created successfully with dummy record")

        # Delete the dummy record
        supabase.table('nsw_documents').delete().eq('act_name', 'Test Act').execute()
        logger.info("Dummy record deleted")

    except Exception as e:
        logger.error(f"Could not create table via insert: {e}")
        logger.info("Please create the table manually in Supabase dashboard with this schema:")
        logger.info("""
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
        """)

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

def upload_documents_to_supabase(documents: List[str], metadata_list: List[Dict], embeddings: np.ndarray):
    """Upload documents with embeddings to Supabase"""

    # Clear existing data
    try:
        result = supabase.table('nsw_documents').delete().neq('id', 0).execute()
        logger.info("Cleared existing documents")
    except Exception as e:
        logger.info(f"No existing documents to clear: {e}")

    # Prepare batch upload
    batch_size = 50
    total_batches = (len(documents) + batch_size - 1) // batch_size

    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i + batch_size]
        batch_metadata = metadata_list[i:i + batch_size]
        batch_embeddings = embeddings[i:i + batch_size]

        batch_data = []
        for j, (doc, meta, embedding) in enumerate(zip(batch_docs, batch_metadata, batch_embeddings)):
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

        try:
            result = supabase.table('nsw_documents').insert(batch_data).execute()
            logger.info(f"Uploaded batch {i//batch_size + 1}/{total_batches} ({len(batch_data)} documents)")
        except Exception as e:
            logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
            # Try smaller batches if needed
            for record in batch_data:
                try:
                    result = supabase.table('nsw_documents').insert([record]).execute()
                except Exception as e2:
                    logger.error(f"Error uploading individual record: {e2}")

def test_hybrid_search():
    """Test the hybrid search functionality"""

    # Test queries for different revenue types
    test_queries = [
        "What is the current land tax rate in NSW?",
        "How do I calculate payroll tax for my business?",
        "Motor vehicle registration fees",
        "Gaming machine tax rates for clubs"
    ]

    # Use OpenAI for query embeddings (minimal cost)
    openai.api_key = os.getenv('OPENAI_API_KEY')

    for query in test_queries:
        logger.info(f"\n🔍 Testing query: '{query}'")

        try:
            # Generate query embedding
            response = openai.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            query_embedding = response.data[0].embedding

            # Execute hybrid search
            result = supabase.rpc('hybrid_search', {
                'query_text': query,
                'query_embedding': query_embedding,
                'revenue_filter': None,
                'match_count': 3
            }).execute()

            logger.info(f"Found {len(result.data)} results:")
            for i, doc in enumerate(result.data, 1):
                logger.info(f"  {i}. {doc['act_name']} ({doc['revenue_type']}) - Score: {doc['combined_score']:.3f}")

        except Exception as e:
            logger.error(f"Error testing query '{query}': {e}")

def main():
    """Main setup function"""
    logger.info("🚀 Starting Supabase setup for NSW Revenue AI Assistant")

    # Step 1: Check if table exists
    logger.info("📋 Checking database schema...")
    try:
        result = supabase.table('nsw_documents').select('id').limit(1).execute()
        logger.info("✅ Table 'nsw_documents' exists and is accessible")
    except Exception as e:
        logger.error(f"❌ Table not found: {e}")
        logger.info("Please run the SQL in scripts/supabase_schema.sql in your Supabase dashboard first")
        return

    # Step 2: Load and upload documents
    logger.info("📄 Loading documents from hybrid cache...")
    documents, metadata_list, embeddings = load_hybrid_cache_data()

    logger.info("📤 Uploading documents to Supabase...")
    upload_documents_to_supabase(documents, metadata_list, embeddings)

    # Step 3: Test functionality
    logger.info("🧪 Testing hybrid search...")
    test_hybrid_search()

    logger.info("✅ Supabase setup complete!")

    # Print connection info
    logger.info(f"🔗 Supabase URL: {SUPABASE_URL}")
    logger.info(f"🔑 Using service role key for setup")

if __name__ == "__main__":
    main()