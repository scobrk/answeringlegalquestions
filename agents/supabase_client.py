"""
Supabase Vector Search Integration
Backend Agent Implementation (KAN-4)
"""

import os
from typing import List, Dict, Optional, Tuple
import numpy as np
from supabase import create_client, Client
from openai import OpenAI
import logging
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Document chunk with metadata for retrieval"""
    id: str
    content: str
    act_name: str
    section_number: Optional[str]
    keywords: List[str]
    metadata: Dict
    similarity_score: float = 0.0


@dataclass
class SearchResult:
    """Vector search result with relevance scoring"""
    chunks: List[DocumentChunk]
    total_results: int
    avg_similarity: float
    search_time: float


class SupabaseVectorClient:
    """
    Supabase vector search client for NSW legislation retrieval
    Integrates with pgvector for similarity search
    """

    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        # Initialize Supabase client
        self.supabase_url = supabase_url or os.getenv('SUPABASE_URL')
        self.supabase_key = supabase_key or os.getenv('SUPABASE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase URL and key must be provided")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

        # Initialize OpenAI for embeddings
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimension = 1536

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for query text

        Args:
            text: Query text to embed

        Returns:
            List of embedding values
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text.strip()
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def store_document_chunk(self, chunk_data: Dict) -> str:
        """
        Store document chunk with embedding in Supabase

        Args:
            chunk_data: Document chunk information

        Returns:
            ID of stored chunk
        """
        try:
            # Generate embedding for chunk content
            embedding = self.generate_embedding(chunk_data['content'])

            # Prepare data for insertion
            insert_data = {
                'content': chunk_data['content'],
                'act_name': chunk_data['act_name'],
                'section_number': chunk_data.get('section_number'),
                'keywords': chunk_data.get('keywords', []),
                'metadata': chunk_data.get('metadata', {}),
                'embedding': embedding
            }

            # Insert into documents table
            result = self.supabase.table('documents').insert(insert_data).execute()

            if result.data:
                chunk_id = result.data[0]['id']
                logger.info(f"Stored document chunk: {chunk_id}")
                return chunk_id
            else:
                raise Exception("No data returned from insert")

        except Exception as e:
            logger.error(f"Failed to store document chunk: {e}")
            raise

    def similarity_search(self,
                         query: str,
                         limit: int = 5,
                         similarity_threshold: float = 0.7,
                         act_filter: Optional[str] = None) -> SearchResult:
        """
        Perform vector similarity search for relevant documents

        Args:
            query: Search query
            limit: Maximum number of results
            similarity_threshold: Minimum similarity score
            act_filter: Filter by specific act name

        Returns:
            SearchResult with ranked document chunks
        """
        start_time = datetime.now()

        try:
            # Generate embedding for query
            query_embedding = self.generate_embedding(query)

            # Build SQL query for vector search
            sql_query = """
            SELECT
                id,
                content,
                act_name,
                section_number,
                keywords,
                metadata,
                1 - (embedding <=> %s::vector) as similarity
            FROM documents
            WHERE 1 - (embedding <=> %s::vector) > %s
            """

            params = [query_embedding, query_embedding, similarity_threshold]

            # Add act filter if specified
            if act_filter:
                sql_query += " AND act_name ILIKE %s"
                params.append(f"%{act_filter}%")

            sql_query += """
            ORDER BY similarity DESC
            LIMIT %s
            """
            params.append(limit)

            # Execute vector search
            result = self.supabase.rpc('similarity_search', {
                'query_embedding': query_embedding,
                'similarity_threshold': similarity_threshold,
                'match_count': limit,
                'act_filter': act_filter
            }).execute()

            # Process results
            chunks = []
            similarities = []

            for row in result.data or []:
                chunk = DocumentChunk(
                    id=row['id'],
                    content=row['content'],
                    act_name=row['act_name'],
                    section_number=row.get('section_number'),
                    keywords=row.get('keywords', []),
                    metadata=row.get('metadata', {}),
                    similarity_score=row.get('similarity', 0.0)
                )
                chunks.append(chunk)
                similarities.append(chunk.similarity_score)

            # Calculate metrics
            search_time = (datetime.now() - start_time).total_seconds()
            avg_similarity = np.mean(similarities) if similarities else 0.0

            logger.info(f"Vector search: {len(chunks)} results in {search_time:.2f}s, avg similarity: {avg_similarity:.3f}")

            return SearchResult(
                chunks=chunks,
                total_results=len(chunks),
                avg_similarity=avg_similarity,
                search_time=search_time
            )

        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            raise

    def search_by_metadata(self,
                          query: str,
                          query_type: str,
                          limit: int = 5) -> SearchResult:
        """
        Enhanced search with metadata filtering

        Args:
            query: Search query
            query_type: Type of query (payroll_tax, duties, etc.)
            limit: Maximum results

        Returns:
            SearchResult with relevant chunks
        """
        try:
            # Map query types to act preferences
            act_preferences = {
                'duties': ['Duties Act 1997', 'Stamp Duties Act'],
                'payroll_tax': ['Payroll Tax Act 2007'],
                'land_tax': ['Land Tax Act 1956', 'Land Tax Management Act 1956'],
                'fines': ['Fines Act', 'Penalty Notices Enforcement Act'],
                'administration': ['Revenue Administration Act 1996'],
                'grants': ['First Home Owner Grant'],
                'general': None  # No specific preference
            }

            preferred_acts = act_preferences.get(query_type)

            # Try searching with act preference first
            if preferred_acts:
                for act in preferred_acts:
                    result = self.similarity_search(
                        query=query,
                        limit=limit,
                        act_filter=act
                    )
                    if result.chunks:
                        return result

            # Fallback to general search
            return self.similarity_search(query=query, limit=limit)

        except Exception as e:
            logger.error(f"Metadata search failed: {e}")
            raise

    def get_document_statistics(self) -> Dict:
        """
        Get statistics about stored documents

        Returns:
            Dictionary with document statistics
        """
        try:
            # Get total document count
            count_result = self.supabase.table('documents').select('id', count='exact').execute()
            total_docs = count_result.count or 0

            # Get act distribution
            act_result = self.supabase.table('documents').select('act_name').execute()
            act_counts = {}
            for row in act_result.data or []:
                act_name = row['act_name']
                act_counts[act_name] = act_counts.get(act_name, 0) + 1

            return {
                'total_documents': total_docs,
                'act_distribution': act_counts,
                'embedding_dimension': self.embedding_dimension,
                'embedding_model': self.embedding_model
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy

        Returns:
            True if connection is working
        """
        try:
            # Simple query to test connection
            result = self.supabase.table('documents').select('id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False


def create_similarity_search_function():
    """
    SQL function for vector similarity search in Supabase

    This should be executed in the Supabase SQL editor to create
    the similarity_search RPC function
    """
    return """
    CREATE OR REPLACE FUNCTION similarity_search(
        query_embedding vector(1536),
        similarity_threshold float DEFAULT 0.7,
        match_count int DEFAULT 5,
        act_filter text DEFAULT NULL
    )
    RETURNS TABLE (
        id uuid,
        content text,
        act_name text,
        section_number text,
        keywords text[],
        metadata jsonb,
        similarity float
    )
    LANGUAGE sql
    AS $$
        SELECT
            d.id,
            d.content,
            d.act_name,
            d.section_number,
            d.keywords,
            d.metadata,
            1 - (d.embedding <=> query_embedding) as similarity
        FROM documents d
        WHERE 1 - (d.embedding <=> query_embedding) > similarity_threshold
        AND (act_filter IS NULL OR d.act_name ILIKE '%' || act_filter || '%')
        ORDER BY similarity DESC
        LIMIT match_count;
    $$;
    """


def main():
    """
    Test the Supabase vector client
    """
    # Initialize client
    client = SupabaseVectorClient()

    # Health check
    if not client.health_check():
        print("❌ Supabase connection failed")
        return

    print("✅ Supabase connection successful")

    # Get statistics
    stats = client.get_document_statistics()
    print(f"📊 Documents: {stats.get('total_documents', 0)}")
    print(f"📊 Acts: {list(stats.get('act_distribution', {}).keys())}")

    # Test search
    test_query = "What is the payroll tax rate for wages over $1.2 million?"
    result = client.search_by_metadata(test_query, 'payroll_tax')

    print(f"\n🔍 Search Results for: '{test_query}'")
    print(f"📄 Found: {result.total_results} chunks")
    print(f"⏱️ Search time: {result.search_time:.2f}s")
    print(f"📈 Avg similarity: {result.avg_similarity:.3f}")

    for i, chunk in enumerate(result.chunks[:2]):
        print(f"\n--- Result {i+1} ---")
        print(f"Act: {chunk.act_name}")
        print(f"Section: {chunk.section_number}")
        print(f"Similarity: {chunk.similarity_score:.3f}")
        print(f"Content: {chunk.content[:200]}...")


if __name__ == "__main__":
    main()