"""
Lightweight Supabase integration for Vercel
Memory-optimized NSW Revenue legislation search
"""

import os
import json
from supabase import create_client, Client
import openai
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseSearchEngine:
    """
    Lightweight search engine using Supabase hybrid search
    Designed for memory-constrained Vercel environment
    """

    def __init__(self):
        # Initialize Supabase client
        self.supabase_url = os.getenv('SUPABASE_URL', 'https://mllidxvkwnwnmjipmhdv.supabase.co')
        self.supabase_key = os.getenv('SUPABASE_KEY', 'sb_secret_cwDOerlN0w6UJ6WqdFN3uw_bkkDKVO1')
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Initialize OpenAI for embeddings
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')

        logger.info("SupabaseSearchEngine initialized")

    def generate_query_embedding(self, query: str) -> List[float]:
        """Generate embedding for search query using OpenAI"""
        try:
            response = openai.embeddings.create(
                model=self.embedding_model,
                input=query,
                dimensions=768  # Reduce to match Legal-BERT dimensions
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * 768

    def search(self,
               query: str,
               top_k: int = 5,
               revenue_type_filter: Optional[str] = None) -> List[Dict]:
        """
        Perform hybrid search using Supabase function

        Args:
            query: Search query text
            top_k: Number of results to return
            revenue_type_filter: Optional revenue type filter

        Returns:
            List of search results with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.generate_query_embedding(query)

            # Execute hybrid search
            result = self.supabase.rpc('hybrid_search', {
                'query_text': query,
                'query_embedding': query_embedding,
                'revenue_filter': revenue_type_filter,
                'match_count': top_k
            }).execute()

            # Format results
            formatted_results = []
            for doc in result.data:
                formatted_results.append({
                    'id': doc['id'],
                    'act_name': doc['act_name'],
                    'content': doc['content'],
                    'revenue_type': doc['revenue_type'],
                    'section_title': doc['section_title'],
                    'section_number': doc['section_number'],
                    'combined_score': doc['combined_score'],
                    'bm25_rank': doc['bm25_rank'],
                    'vector_similarity': doc['vector_similarity'],
                    'metadata': doc['metadata']
                })

            logger.info(f"Found {len(formatted_results)} results for query: '{query}'")
            return formatted_results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def get_revenue_types(self) -> List[Dict]:
        """Get available revenue types from the database"""
        try:
            result = self.supabase.table('nsw_documents').select('revenue_type').execute()
            revenue_types = {}

            for record in result.data:
                revenue_type = record['revenue_type']
                revenue_types[revenue_type] = revenue_types.get(revenue_type, 0) + 1

            # Sort by frequency
            sorted_types = sorted(revenue_types.items(), key=lambda x: x[1], reverse=True)

            return [{'revenue_type': rt, 'count': count} for rt, count in sorted_types]

        except Exception as e:
            logger.error(f"Error getting revenue types: {e}")
            return []

    def get_database_stats(self) -> Dict:
        """Get database statistics"""
        try:
            # Get total count
            result = self.supabase.table('nsw_documents').select('count', count='exact').execute()
            total_docs = result.count

            # Get revenue types
            revenue_types = self.get_revenue_types()

            # Get sample documents
            sample_result = self.supabase.table('nsw_documents').select('act_name,revenue_type').limit(5).execute()

            return {
                'total_documents': total_docs,
                'revenue_types': len(revenue_types),
                'revenue_breakdown': revenue_types[:10],  # Top 10
                'sample_documents': sample_result.data,
                'database_url': self.supabase_url
            }

        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}

# Global search engine instance (for memory efficiency)
search_engine = None

def get_search_engine() -> SupabaseSearchEngine:
    """Get or create search engine instance"""
    global search_engine
    if search_engine is None:
        search_engine = SupabaseSearchEngine()
    return search_engine