"""
RAG Document Retrieval System
Data Engineering Agent Implementation (KAN-4)
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime
import re

from supabase_client import SupabaseVectorClient, DocumentChunk, SearchResult
from query_classifier import NSWRevenueQueryClassifier, QueryType, ClassificationResult

logger = logging.getLogger(__name__)


@dataclass
class RetrievalContext:
    """Context for document retrieval with relevance scoring"""
    query: str
    query_type: QueryType
    classification_confidence: float
    retrieved_chunks: List[DocumentChunk]
    total_search_time: float
    context_text: str
    relevance_score: float


@dataclass
class CitationInfo:
    """Citation information extracted from documents"""
    act_name: str
    section_number: Optional[str]
    subsection: Optional[str]
    page_reference: Optional[str]
    confidence: float


class NSWLegalDocumentRetriever:
    """
    Advanced document retrieval system for NSW Revenue legislation
    Integrates vector search with legal document understanding
    """

    def __init__(self, supabase_client: SupabaseVectorClient):
        self.supabase_client = supabase_client
        self.query_classifier = NSWRevenueQueryClassifier()

        # Retrieval parameters
        self.max_chunks_per_query = 5
        self.min_similarity_threshold = 0.7
        self.context_window_size = 2000  # Max tokens for context

        # Legal citation patterns
        self.citation_patterns = [
            r'([A-Z][a-z\s]+Act\s+\d{4})\s+s\.?\s*(\d+[A-Z]*)',  # Act Year s123
            r'([A-Z][a-z\s]+Act\s+\d{4})\s+section\s+(\d+[A-Z]*)',  # Act Year section 123
            r's\.?\s*(\d+[A-Z]*)\s+of\s+the\s+([A-Z][a-z\s]+Act\s+\d{4})',  # s123 of the Act Year
            r'section\s+(\d+[A-Z]*)\s+of\s+the\s+([A-Z][a-z\s]+Act\s+\d{4})',  # section 123 of the Act Year
        ]

    def retrieve_documents(self, query: str) -> RetrievalContext:
        """
        Retrieve relevant documents for a query using advanced RAG

        Args:
            query: User query

        Returns:
            RetrievalContext with retrieved documents and metadata
        """
        start_time = datetime.now()

        try:
            # Step 1: Classify query
            classification = self.query_classifier.classify_query(query)
            logger.info(f"Query classified as {classification.query_type.value} (confidence: {classification.confidence:.2f})")

            # Step 2: Enhanced document search
            search_result = self._enhanced_document_search(query, classification)

            # Step 3: Re-rank and filter chunks
            relevant_chunks = self._rerank_chunks(query, search_result.chunks, classification.query_type)

            # Step 4: Build context window
            context_text = self._build_context_window(relevant_chunks)

            # Step 5: Calculate overall relevance
            relevance_score = self._calculate_relevance_score(relevant_chunks, classification.confidence)

            total_time = (datetime.now() - start_time).total_seconds()

            logger.info(f"Retrieved {len(relevant_chunks)} chunks in {total_time:.2f}s, relevance: {relevance_score:.3f}")

            return RetrievalContext(
                query=query,
                query_type=classification.query_type,
                classification_confidence=classification.confidence,
                retrieved_chunks=relevant_chunks,
                total_search_time=total_time,
                context_text=context_text,
                relevance_score=relevance_score
            )

        except Exception as e:
            logger.error(f"Document retrieval failed: {e}")
            raise

    def _enhanced_document_search(self, query: str, classification: ClassificationResult) -> SearchResult:
        """
        Perform enhanced document search with multiple strategies

        Args:
            query: Search query
            classification: Query classification result

        Returns:
            SearchResult with relevant documents
        """
        # Primary search with query type
        primary_result = self.supabase_client.search_by_metadata(
            query=query,
            query_type=classification.query_type.value,
            limit=self.max_chunks_per_query
        )

        # If primary search has low results, try fallback strategies
        if len(primary_result.chunks) < 3 or primary_result.avg_similarity < 0.8:
            logger.info("Primary search yielded few results, trying fallback strategies")

            # Strategy 1: Broader similarity threshold
            fallback_result = self.supabase_client.similarity_search(
                query=query,
                limit=self.max_chunks_per_query,
                similarity_threshold=max(0.5, self.min_similarity_threshold - 0.2)
            )

            # Strategy 2: Keyword-based search for important terms
            keyword_results = self._keyword_based_search(query, classification)

            # Combine results intelligently
            all_chunks = primary_result.chunks + fallback_result.chunks + keyword_results
            unique_chunks = self._deduplicate_chunks(all_chunks)

            return SearchResult(
                chunks=unique_chunks[:self.max_chunks_per_query],
                total_results=len(unique_chunks),
                avg_similarity=primary_result.avg_similarity,
                search_time=primary_result.search_time
            )

        return primary_result

    def _keyword_based_search(self, query: str, classification: ClassificationResult) -> List[DocumentChunk]:
        """
        Perform keyword-based search as fallback

        Args:
            query: Search query
            classification: Query classification

        Returns:
            List of relevant chunks
        """
        # Extract key terms from query
        key_terms = self._extract_key_terms(query, classification.query_type)

        # Search for each key term
        keyword_chunks = []
        for term in key_terms[:3]:  # Limit to top 3 terms
            term_result = self.supabase_client.similarity_search(
                query=term,
                limit=2,
                similarity_threshold=0.6
            )
            keyword_chunks.extend(term_result.chunks)

        return keyword_chunks

    def _extract_key_terms(self, query: str, query_type: QueryType) -> List[str]:
        """
        Extract key terms from query for keyword search

        Args:
            query: Query text
            query_type: Classified query type

        Returns:
            List of key terms
        """
        # Remove common words
        stop_words = {
            'the', 'is', 'at', 'which', 'on', 'what', 'how', 'do', 'i',
            'a', 'an', 'and', 'or', 'but', 'in', 'with', 'to', 'for'
        }

        words = query.lower().split()
        key_terms = [word for word in words if word not in stop_words and len(word) > 2]

        # Add type-specific terms
        type_specific_terms = {
            QueryType.PAYROLL_TAX: ['payroll', 'wages', 'employer'],
            QueryType.LAND_TAX: ['land', 'property', 'unimproved'],
            QueryType.DUTIES: ['duty', 'stamp', 'conveyance'],
            QueryType.FINES: ['penalty', 'fine', 'enforcement'],
            QueryType.GRANTS: ['grant', 'first home', 'eligible'],
            QueryType.ADMINISTRATION: ['assessment', 'review', 'appeal']
        }

        if query_type in type_specific_terms:
            key_terms.extend(type_specific_terms[query_type])

        return list(set(key_terms))

    def _rerank_chunks(self, query: str, chunks: List[DocumentChunk], query_type: QueryType) -> List[DocumentChunk]:
        """
        Re-rank chunks based on relevance to query and type

        Args:
            query: Original query
            chunks: Retrieved chunks
            query_type: Query type

        Returns:
            Re-ranked list of chunks
        """
        scored_chunks = []

        for chunk in chunks:
            # Base score from similarity
            score = chunk.similarity_score

            # Boost for query type match
            if self._chunk_matches_query_type(chunk, query_type):
                score += 0.2

            # Boost for having calculations (if query needs calculations)
            if self.query_classifier.is_calculation_query(query) and self._chunk_has_calculations(chunk):
                score += 0.15

            # Boost for recent/current information
            if self._chunk_is_current(chunk):
                score += 0.1

            # Penalty for very short chunks
            if len(chunk.content.split()) < 50:
                score -= 0.1

            scored_chunks.append((chunk, score))

        # Sort by score and return top chunks
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return [chunk for chunk, score in scored_chunks[:self.max_chunks_per_query]]

    def _chunk_matches_query_type(self, chunk: DocumentChunk, query_type: QueryType) -> bool:
        """Check if chunk matches the query type"""
        type_act_mapping = {
            QueryType.PAYROLL_TAX: ['Payroll Tax Act'],
            QueryType.LAND_TAX: ['Land Tax Act', 'Land Tax Management Act'],
            QueryType.DUTIES: ['Duties Act', 'Stamp Duties Act'],
            QueryType.FINES: ['Fines Act', 'Penalty Notices'],
            QueryType.GRANTS: ['First Home Owner Grant'],
            QueryType.ADMINISTRATION: ['Revenue Administration Act']
        }

        relevant_acts = type_act_mapping.get(query_type, [])
        return any(act.lower() in chunk.act_name.lower() for act in relevant_acts)

    def _chunk_has_calculations(self, chunk: DocumentChunk) -> bool:
        """Check if chunk contains calculation-related content"""
        calc_indicators = [
            'rate', 'percentage', 'calculate', 'formula', 'amount',
            '$', '%', 'multiply', 'divide', 'total', 'sum'
        ]
        content_lower = chunk.content.lower()
        return any(indicator in content_lower for indicator in calc_indicators)

    def _chunk_is_current(self, chunk: DocumentChunk) -> bool:
        """Check if chunk contains current/recent information"""
        current_year = datetime.now().year
        recent_years = [str(year) for year in range(current_year - 2, current_year + 1)]

        return any(year in chunk.content for year in recent_years)

    def _build_context_window(self, chunks: List[DocumentChunk]) -> str:
        """
        Build context window from retrieved chunks

        Args:
            chunks: Retrieved document chunks

        Returns:
            Formatted context text
        """
        context_parts = []
        current_tokens = 0

        for i, chunk in enumerate(chunks):
            # Estimate token count (rough approximation)
            chunk_tokens = len(chunk.content.split()) * 1.3  # Approximate token count

            if current_tokens + chunk_tokens > self.context_window_size:
                break

            # Format chunk with metadata
            chunk_header = f"[{chunk.act_name}"
            if chunk.section_number:
                chunk_header += f" Section {chunk.section_number}"
            chunk_header += "]"

            context_parts.append(f"{chunk_header}\n{chunk.content}\n")
            current_tokens += chunk_tokens

        return "\n".join(context_parts)

    def _calculate_relevance_score(self, chunks: List[DocumentChunk], classification_confidence: float) -> float:
        """
        Calculate overall relevance score for retrieval

        Args:
            chunks: Retrieved chunks
            classification_confidence: Query classification confidence

        Returns:
            Overall relevance score
        """
        if not chunks:
            return 0.0

        # Average similarity score
        avg_similarity = sum(chunk.similarity_score for chunk in chunks) / len(chunks)

        # Number of chunks factor
        chunk_factor = min(len(chunks) / self.max_chunks_per_query, 1.0)

        # Classification confidence factor
        classification_factor = classification_confidence

        # Combined relevance score
        relevance = (avg_similarity * 0.5) + (chunk_factor * 0.3) + (classification_factor * 0.2)

        return min(relevance, 1.0)

    def _deduplicate_chunks(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Remove duplicate chunks based on content similarity

        Args:
            chunks: List of chunks

        Returns:
            Deduplicated list
        """
        unique_chunks = []
        seen_content = set()

        for chunk in chunks:
            # Use first 100 characters as similarity key
            content_key = chunk.content[:100].strip()

            if content_key not in seen_content:
                unique_chunks.append(chunk)
                seen_content.add(content_key)

        return unique_chunks

    def extract_citations(self, context: RetrievalContext) -> List[CitationInfo]:
        """
        Extract legal citations from retrieved context

        Args:
            context: Retrieval context

        Returns:
            List of citation information
        """
        citations = []

        for chunk in context.retrieved_chunks:
            # Extract from chunk metadata
            if chunk.act_name and chunk.section_number:
                citation = CitationInfo(
                    act_name=chunk.act_name,
                    section_number=chunk.section_number,
                    subsection=None,
                    page_reference=None,
                    confidence=chunk.similarity_score
                )
                citations.append(citation)

            # Extract from content using patterns
            for pattern in self.citation_patterns:
                matches = re.finditer(pattern, chunk.content, re.IGNORECASE)
                for match in matches:
                    groups = match.groups()
                    if len(groups) >= 2:
                        citation = CitationInfo(
                            act_name=groups[1] if len(groups) > 1 else groups[0],
                            section_number=groups[0] if len(groups) > 1 else groups[1],
                            subsection=None,
                            page_reference=None,
                            confidence=0.8  # High confidence for pattern matches
                        )
                        citations.append(citation)

        # Deduplicate citations
        unique_citations = []
        seen_citations = set()

        for citation in citations:
            citation_key = f"{citation.act_name}_{citation.section_number}"
            if citation_key not in seen_citations:
                unique_citations.append(citation)
                seen_citations.add(citation_key)

        return unique_citations[:5]  # Limit to top 5 citations


def main():
    """
    Test the document retriever
    """
    # Initialize components
    supabase_client = SupabaseVectorClient()
    retriever = NSWLegalDocumentRetriever(supabase_client)

    # Test queries
    test_queries = [
        "What is the payroll tax rate for wages over $1.2 million?",
        "How do I calculate stamp duty on an $800,000 property?",
        "What are the land tax exemptions for primary residence?"
    ]

    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")

        try:
            context = retriever.retrieve_documents(query)

            print(f"📂 Query type: {context.query_type.value}")
            print(f"📊 Classification confidence: {context.classification_confidence:.2f}")
            print(f"📄 Retrieved chunks: {len(context.retrieved_chunks)}")
            print(f"⏱️ Search time: {context.total_search_time:.2f}s")
            print(f"📈 Relevance score: {context.relevance_score:.3f}")

            # Show citations
            citations = retriever.extract_citations(context)
            if citations:
                print(f"📚 Citations:")
                for citation in citations:
                    print(f"  - {citation.act_name} s{citation.section_number}")

            # Show first chunk summary
            if context.retrieved_chunks:
                first_chunk = context.retrieved_chunks[0]
                print(f"📋 Top result: {first_chunk.act_name} (similarity: {first_chunk.similarity_score:.3f})")
                print(f"📄 Content preview: {first_chunk.content[:150]}...")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()