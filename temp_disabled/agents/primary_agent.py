"""
Primary Response Agent - Core Implementation
Backend Agent Implementation (KAN-4)
"""

import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import time
import json

from openai import OpenAI
from supabase_client import SupabaseVectorClient
from document_retriever import NSWLegalDocumentRetriever, RetrievalContext, CitationInfo
from query_classifier import QueryType

logger = logging.getLogger(__name__)


@dataclass
class PrimaryResponse:
    """Primary response structure from the agent"""
    answer: str
    citations: List[str]
    confidence: float
    query_type: str
    source_documents: List[Dict]
    calculations: Optional[Dict] = None
    assumptions: List[str] = None
    limitations: List[str] = None
    timestamp: datetime = None
    processing_time: float = 0.0
    raw_llm_response: str = ""


class PrimaryResponseAgent:
    """
    Primary Response Agent for NSW Revenue queries
    Integrates retrieval, classification, and LLM generation
    """

    def __init__(self,
                 supabase_url: str = None,
                 supabase_key: str = None,
                 openai_api_key: str = None):

        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=openai_api_key or os.getenv('OPENAI_API_KEY')
        )
        # Cost-optimized model selection
        self.llm_model = os.getenv('DEFAULT_MODEL', "gpt-4o-mini")  # Use main processing model
        self.temperature = 0.0  # Zero temperature for deterministic calculations

        # Initialize document retrieval system
        supabase_client = SupabaseVectorClient(supabase_url, supabase_key)
        self.document_retriever = NSWLegalDocumentRetriever(supabase_client)

        # Response generation settings with cost controls
        self.max_response_tokens = int(os.getenv('MAX_TOKENS_PER_REQUEST', 1500))  # Increased for complex calculations
        self.min_confidence_threshold = 0.3

        # System prompt template
        self.system_prompt = """You are an expert NSW Revenue legislation assistant. Your role is to provide accurate, helpful information about NSW taxation and revenue matters.

CRITICAL INSTRUCTIONS:
1. Use ONLY the provided context from NSW legislation
2. Include specific section references for all legal claims
3. Show step-by-step calculations when needed
4. State any assumptions clearly
5. If information is insufficient, clearly state what's missing
6. Be precise with legal terminology and rates

RESPONSE FORMAT:
ANSWER: [Direct, clear answer to the query]
CITATIONS: [List specific acts and sections referenced]
CALCULATIONS: [If applicable, show step-by-step calculations]
ASSUMPTIONS: [Any assumptions made in the response]
CONFIDENCE: [High/Medium/Low based on source quality and completeness]

Remember: Accuracy is paramount. If you're uncertain, indicate this clearly rather than guessing."""

    def generate_response(self, query: str) -> PrimaryResponse:
        """
        Generate primary response for NSW Revenue query

        Args:
            query: User query

        Returns:
            PrimaryResponse with comprehensive information
        """
        start_time = time.time()
        timestamp = datetime.now()

        try:
            logger.info(f"Processing query: {query}")

            # Step 1: Retrieve relevant documents
            retrieval_context = self.document_retriever.retrieve_documents(query)

            # Step 2: Check if sufficient context was retrieved
            if retrieval_context.relevance_score < self.min_confidence_threshold:
                return self._generate_insufficient_context_response(query, retrieval_context, timestamp)

            # Step 3: Generate LLM response
            llm_response = self._generate_llm_response(query, retrieval_context)

            # Step 4: Parse and structure response
            structured_response = self._parse_llm_response(llm_response, retrieval_context)

            # Step 5: Extract citations
            citations = self._extract_citations(retrieval_context, structured_response)

            # Step 6: Calculate confidence score
            confidence = self._calculate_response_confidence(retrieval_context, structured_response)

            # Step 7: Build final response
            processing_time = time.time() - start_time

            response = PrimaryResponse(
                answer=structured_response.get('answer', 'Unable to provide a complete answer.'),
                citations=citations,
                confidence=confidence,
                query_type=retrieval_context.query_type.value,
                source_documents=self._format_source_documents(retrieval_context.retrieved_chunks),
                calculations=structured_response.get('calculations'),
                assumptions=structured_response.get('assumptions', []),
                limitations=structured_response.get('limitations', []),
                timestamp=timestamp,
                processing_time=processing_time,
                raw_llm_response=llm_response
            )

            logger.info(f"Response generated in {processing_time:.2f}s with confidence {confidence:.2f}")
            return response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_error_response(query, str(e), timestamp)

    def _generate_llm_response(self, query: str, context: RetrievalContext) -> str:
        """
        Generate response using OpenAI LLM

        Args:
            query: User query
            context: Retrieved document context

        Returns:
            Raw LLM response
        """
        try:
            # Build prompt with context
            user_prompt = f"""Query: {query}

Context from NSW Revenue Legislation:
{context.context_text}

Based on the provided context, please provide a comprehensive answer following the specified format."""

            # Call OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_response_tokens,
                temperature=self.temperature
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    def _parse_llm_response(self, llm_response: str, context: RetrievalContext) -> Dict:
        """
        Parse structured response from LLM

        Args:
            llm_response: Raw LLM response
            context: Retrieval context

        Returns:
            Parsed response dictionary
        """
        response_parts = {}
        current_section = None
        content_lines = []

        for line in llm_response.split('\n'):
            line = line.strip()

            # Check for section headers
            if line.startswith('ANSWER:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'answer'
                content_lines = [line[7:].strip()]
            elif line.startswith('CITATIONS:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'citations'
                content_lines = [line[10:].strip()]
            elif line.startswith('CALCULATIONS:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'calculations'
                content_lines = [line[13:].strip()]
            elif line.startswith('ASSUMPTIONS:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'assumptions'
                content_lines = [line[12:].strip()]
            elif line.startswith('CONFIDENCE:'):
                if current_section:
                    response_parts[current_section] = '\n'.join(content_lines).strip()
                current_section = 'confidence'
                content_lines = [line[11:].strip()]
            elif current_section and line:
                content_lines.append(line)

        # Add final section
        if current_section and content_lines:
            response_parts[current_section] = '\n'.join(content_lines).strip()

        # Process specific sections
        if 'assumptions' in response_parts:
            assumptions_text = response_parts['assumptions']
            response_parts['assumptions'] = [
                item.strip('- ').strip() for item in assumptions_text.split('\n')
                if item.strip() and item.strip() != 'None'
            ]

        if 'calculations' in response_parts and response_parts['calculations']:
            # Keep calculations as structured text for now
            calc_text = response_parts['calculations']
            if calc_text and calc_text.lower() not in ['none', 'n/a', 'not applicable']:
                response_parts['calculations'] = {'steps': calc_text}
            else:
                response_parts['calculations'] = None

        return response_parts

    def _extract_citations(self, context: RetrievalContext, structured_response: Dict) -> List[str]:
        """
        Extract and format citations

        Args:
            context: Retrieval context
            structured_response: Parsed LLM response

        Returns:
            List of formatted citations
        """
        citations = []

        # Extract from LLM response
        if 'citations' in structured_response:
            llm_citations = structured_response['citations']
            if llm_citations and llm_citations.lower() not in ['none', 'n/a']:
                # Split and clean citations
                citation_lines = [line.strip('- ').strip() for line in llm_citations.split('\n') if line.strip()]
                citations.extend(citation_lines)

        # Extract from document retriever
        document_citations = self.document_retriever.extract_citations(context)
        for citation in document_citations:
            citation_text = citation.act_name
            if citation.section_number:
                citation_text += f" s{citation.section_number}"
            citations.append(citation_text)

        # Deduplicate and format
        unique_citations = list(set(citations))

        # Clean up citations
        cleaned_citations = []
        for citation in unique_citations:
            if citation and len(citation) > 5:  # Filter out very short citations
                cleaned_citations.append(citation)

        return cleaned_citations[:5]  # Limit to top 5 citations

    def _calculate_response_confidence(self, context: RetrievalContext, structured_response: Dict) -> float:
        """
        Calculate overall response confidence

        Args:
            context: Retrieval context
            structured_response: Parsed response

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence from retrieval
        retrieval_confidence = context.relevance_score * 0.4

        # Classification confidence
        classification_confidence = context.classification_confidence * 0.2

        # LLM confidence (if provided)
        llm_confidence = 0.3  # Default
        if 'confidence' in structured_response:
            confidence_text = structured_response['confidence'].lower()
            if 'high' in confidence_text:
                llm_confidence = 0.9
            elif 'medium' in confidence_text:
                llm_confidence = 0.6
            elif 'low' in confidence_text:
                llm_confidence = 0.3

        llm_confidence *= 0.3

        # Citation quality bonus
        citation_bonus = min(len(structured_response.get('citations', [])) * 0.05, 0.1)

        total_confidence = retrieval_confidence + classification_confidence + llm_confidence + citation_bonus

        return min(max(total_confidence, 0.0), 1.0)

    def _format_source_documents(self, chunks: List) -> List[Dict]:
        """
        Format source documents for response

        Args:
            chunks: Document chunks

        Returns:
            List of formatted document info
        """
        formatted_docs = []

        for chunk in chunks:
            doc_info = {
                'id': chunk.id,
                'act_name': chunk.act_name,
                'section_number': chunk.section_number,
                'similarity_score': chunk.similarity_score,
                'content_preview': chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            }
            formatted_docs.append(doc_info)

        return formatted_docs

    def _generate_insufficient_context_response(self, query: str, context: RetrievalContext, timestamp: datetime) -> PrimaryResponse:
        """Generate response when insufficient context is available"""
        return PrimaryResponse(
            answer="I don't have sufficient information in the NSW Revenue legislation database to provide a complete answer to your query. This may be because the query is outside the scope of NSW Revenue matters or requires information not currently in the database.",
            citations=[],
            confidence=0.1,
            query_type=context.query_type.value if context else 'unknown',
            source_documents=[],
            limitations=["Insufficient relevant documents found", "Query may be outside NSW Revenue scope"],
            timestamp=timestamp,
            processing_time=0.0
        )

    def _generate_error_response(self, query: str, error_msg: str, timestamp: datetime) -> PrimaryResponse:
        """Generate response when an error occurs"""
        return PrimaryResponse(
            answer="I encountered an error while processing your query. Please try rephrasing your question or contact support if the issue persists.",
            citations=[],
            confidence=0.0,
            query_type='error',
            source_documents=[],
            limitations=[f"Processing error: {error_msg}"],
            timestamp=timestamp,
            processing_time=0.0
        )

    def health_check(self) -> Dict:
        """
        Perform health check on agent components

        Returns:
            Health status dictionary
        """
        status = {
            'agent_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check Supabase connection
            supabase_healthy = self.document_retriever.supabase_client.health_check()
            status['components']['supabase'] = 'healthy' if supabase_healthy else 'unhealthy'

            # Check OpenAI API (simple call)
            try:
                test_response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=1
                )
                status['components']['openai'] = 'healthy'
            except:
                status['components']['openai'] = 'unhealthy'

            # Overall status
            if all(comp == 'healthy' for comp in status['components'].values()):
                status['agent_status'] = 'healthy'
            else:
                status['agent_status'] = 'degraded'

        except Exception as e:
            status['agent_status'] = 'unhealthy'
            status['error'] = str(e)

        return status


def main():
    """
    Test the Primary Response Agent
    """
    # Initialize agent
    agent = PrimaryResponseAgent()

    # Health check
    health = agent.health_check()
    print(f"🏥 Agent Health: {health['agent_status']}")
    for component, status in health.get('components', {}).items():
        print(f"  - {component}: {status}")

    # Test queries
    test_queries = [
        "What is the current payroll tax rate for wages over $1.2 million?",
        "How do I calculate stamp duty on an $800,000 residential property?",
        "What are the land tax exemptions for primary residence?"
    ]

    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")

        try:
            response = agent.generate_response(query)

            print(f"📂 Type: {response.query_type}")
            print(f"📊 Confidence: {response.confidence:.2f}")
            print(f"⏱️ Processing time: {response.processing_time:.2f}s")
            print(f"📚 Citations: {len(response.citations)}")

            print(f"\n💬 Answer:")
            print(response.answer)

            if response.citations:
                print(f"\n📖 Citations:")
                for citation in response.citations:
                    print(f"  - {citation}")

            if response.assumptions:
                print(f"\n⚠️ Assumptions:")
                for assumption in response.assumptions:
                    print(f"  - {assumption}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()