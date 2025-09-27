"""
Upload documents to Supabase using REST API (now that table exists)
"""

import os
import json
import numpy as np
from pathlib import Path
from supabase import create_client, Client
import pickle
from typing import List, Dict
import logging
import time

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

def test_table_access():
    """Test if we can access the table via REST API"""
    try:
        result = supabase.table('nsw_documents').select('count', count='exact').execute()
        logger.info(f"✅ Table accessible via REST API: {result.count} records")
        return True
    except Exception as e:
        logger.error(f"❌ Table access failed: {e}")
        return False

def upload_batch_via_rest(batch_data: List[Dict], batch_num: int, total_batches: int):
    """Upload a batch of documents using REST API"""
    try:
        result = supabase.table('nsw_documents').insert(batch_data).execute()
        logger.info(f"✅ Uploaded batch {batch_num}/{total_batches} ({len(batch_data)} documents)")
        return True
    except Exception as e:
        logger.error(f"❌ Error uploading batch {batch_num}: {e}")

        # Try uploading one by one if batch fails
        logger.info(f"Trying to upload batch {batch_num} records individually...")
        success_count = 0
        for i, record in enumerate(batch_data):
            try:
                supabase.table('nsw_documents').insert([record]).execute()
                success_count += 1
            except Exception as e2:
                logger.error(f"Failed to upload record {i+1}: {e2}")

        logger.info(f"Individual upload: {success_count}/{len(batch_data)} records succeeded")
        return success_count > 0

def upload_documents_to_supabase(documents: List[str], metadata_list: List[Dict], embeddings: np.ndarray):
    """Upload documents with embeddings to Supabase using REST API"""

    # Clear existing data first
    try:
        result = supabase.table('nsw_documents').delete().neq('id', 0).execute()
        logger.info("Cleared existing documents")
    except Exception as e:
        logger.info(f"No existing documents to clear: {e}")

    # Prepare batch upload
    batch_size = 25  # Smaller batches for REST API
    total_batches = (len(documents) + batch_size - 1) // batch_size

    successful_uploads = 0
    failed_uploads = 0

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

        if upload_batch_via_rest(batch_data, i//batch_size + 1, total_batches):
            successful_uploads += len(batch_data)
        else:
            failed_uploads += len(batch_data)

        # Small delay to avoid rate limiting
        time.sleep(0.1)

    logger.info(f"Upload complete: {successful_uploads} successful, {failed_uploads} failed")
    return successful_uploads, failed_uploads

def verify_upload():
    """Verify the upload was successful"""
    try:
        # Check total count
        result = supabase.table('nsw_documents').select('count', count='exact').execute()
        total_count = result.count
        logger.info(f"Total records in database: {total_count}")

        # Check revenue types
        revenue_result = supabase.table('nsw_documents').select('revenue_type').execute()
        revenue_types = set(record['revenue_type'] for record in revenue_result.data)
        logger.info(f"Revenue types found: {len(revenue_types)} types")

        # Sample data
        sample_result = supabase.table('nsw_documents').select('id,act_name,revenue_type,section_title').limit(3).execute()
        logger.info(f"Sample records: {sample_result.data}")

        return total_count
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return 0

def main():
    """Main upload function"""
    logger.info("🚀 Starting REST API document upload to Supabase")

    # Step 1: Test table access
    logger.info("📋 Testing table access...")
    if not test_table_access():
        logger.error("❌ Cannot access table via REST API")
        return

    # Step 2: Load documents
    logger.info("📄 Loading documents from hybrid cache...")
    documents, metadata_list, embeddings = load_hybrid_cache_data()

    # Step 3: Upload via REST API
    logger.info("📤 Uploading documents via REST API...")
    successful, failed = upload_documents_to_supabase(documents, metadata_list, embeddings)

    # Step 4: Verify upload
    logger.info("🔍 Verifying upload...")
    final_count = verify_upload()

    if final_count == len(documents):
        logger.info("✅ Upload successful! All documents uploaded.")
    else:
        logger.warning(f"⚠️ Upload incomplete: {final_count}/{len(documents)} documents uploaded")

    logger.info("✅ Upload process complete!")

if __name__ == "__main__":
    main()