"""
Test the hybrid search functionality in Supabase
"""

import os
from supabase import create_client, Client
import openai
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Supabase credentials
SUPABASE_URL = "https://mllidxvkwnwnmjipmhdv.supabase.co"
SUPABASE_KEY = "sb_secret_cwDOerlN0w6UJ6WqdFN3uw_bkkDKVO1"

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def test_hybrid_search():
    """Test the hybrid search functionality"""

    # Test queries for different revenue types
    test_queries = [
        "What is the current land tax rate in NSW?",
        "How do I calculate payroll tax for my business?",
        "Motor vehicle registration fees",
        "Gaming machine tax rates for clubs",
        "Foreign surcharge on property purchases"
    ]

    # Use OpenAI for query embeddings
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
                logger.info(f"     Section: {doc['section_title']}")
                logger.info(f"     Content preview: {doc['content'][:100]}...")

        except Exception as e:
            logger.error(f"Error testing query '{query}': {e}")

def test_revenue_type_filtering():
    """Test revenue type filtering"""
    logger.info("\n🎯 Testing revenue type filtering...")

    try:
        # Get available revenue types
        result = supabase.table('nsw_documents').select('revenue_type').execute()
        revenue_types = list(set(record['revenue_type'] for record in result.data))
        logger.info(f"Available revenue types: {revenue_types}")

        # Test filtering by specific revenue type
        query = "tax rates"
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding

        for revenue_type in revenue_types[:3]:  # Test first 3 types
            result = supabase.rpc('hybrid_search', {
                'query_text': query,
                'query_embedding': query_embedding,
                'revenue_filter': revenue_type,
                'match_count': 2
            }).execute()

            logger.info(f"\nRevenue type '{revenue_type}' - {len(result.data)} results:")
            for doc in result.data:
                logger.info(f"  - {doc['act_name']} (Score: {doc['combined_score']:.3f})")

    except Exception as e:
        logger.error(f"Error testing revenue type filtering: {e}")

def test_vector_similarity():
    """Test pure vector similarity search"""
    logger.info("\n🧠 Testing vector similarity...")

    try:
        query = "property tax assessment"
        response = openai.embeddings.create(
            model="text-embedding-3-small",
            input=query
        )
        query_embedding = response.data[0].embedding

        # Test with empty text (vector only)
        result = supabase.rpc('hybrid_search', {
            'query_text': '',  # Empty text for vector-only search
            'query_embedding': query_embedding,
            'revenue_filter': None,
            'match_count': 3
        }).execute()

        logger.info(f"Vector-only search results: {len(result.data)}")
        for doc in result.data:
            logger.info(f"  - {doc['act_name']} (Vector score: {doc['vector_similarity']:.3f})")

    except Exception as e:
        logger.error(f"Error testing vector similarity: {e}")

if __name__ == "__main__":
    logger.info("🧪 Testing Supabase hybrid search...")

    # Set OpenAI API key from environment
    openai.api_key = os.getenv('OPENAI_API_KEY')

    logger.info("1. Testing hybrid search...")
    test_hybrid_search()

    logger.info("\n2. Testing revenue type filtering...")
    test_revenue_type_filtering()

    logger.info("\n3. Testing vector similarity...")
    test_vector_similarity()

    logger.info("\n✅ Hybrid search testing complete!")