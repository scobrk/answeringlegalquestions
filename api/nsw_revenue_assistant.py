"""
NSW Revenue AI Assistant - Complete Integration
Memory-optimized dual-agent system with Supabase backend
"""

import json
import os
from http.server import BaseHTTPRequestHandler
import logging
from typing import Dict, List, Optional
import openai
from datetime import datetime

# Import our components
from .supabase_search import get_search_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NSWRevenueAssistant:
    """
    Complete NSW Revenue AI Assistant
    Combines lightweight search with AI-powered responses
    """

    def __init__(self):
        # Initialize search engine
        self.search_engine = get_search_engine()

        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY', 'REDACTED_API_KEY')
        self.model = os.getenv('DEFAULT_MODEL', 'gpt-4o-mini')

        logger.info("NSW Revenue Assistant initialized")

    def process_query(self,
                     query: str,
                     revenue_type_filter: Optional[str] = None,
                     top_k: int = 5) -> Dict:
        """
        Complete query processing with dual-agent approach

        Args:
            query: User's question about NSW revenue
            revenue_type_filter: Optional filter for specific revenue type
            top_k: Number of documents to retrieve

        Returns:
            Complete response with content, citations, and metadata
        """
        try:
            start_time = datetime.now()

            # Step 1: Search relevant documents
            search_results = self.search_engine.search(
                query=query,
                top_k=top_k,
                revenue_type_filter=revenue_type_filter
            )

            if not search_results:
                return self._create_no_results_response(query)

            # Step 2: Generate primary response
            primary_response = self._generate_primary_response(query, search_results)

            # Step 3: Validate response (simplified approval)
            validation_result = self._validate_response(primary_response, search_results)

            # Step 4: Create final response
            processing_time = (datetime.now() - start_time).total_seconds()

            return {
                'content': primary_response['content'],
                'confidence_score': primary_response['confidence_score'],
                'citations': primary_response['citations'],
                'source_documents': self._format_source_documents(search_results),
                'review_status': validation_result['status'],
                'specific_information_required': validation_result.get('missing_info'),
                'revenue_type_filter': revenue_type_filter,
                'processing_metadata': {
                    'search_results_count': len(search_results),
                    'top_score': search_results[0]['combined_score'] if search_results else 0,
                    'processing_time_seconds': processing_time,
                    'timestamp': datetime.now().isoformat(),
                    'system': 'memory_optimized_supabase',
                    'model_used': self.model
                },
                'success': True
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return self._create_error_response(str(e))

    def _generate_primary_response(self, query: str, search_results: List[Dict]) -> Dict:
        """Generate primary AI response using search results"""

        # Prepare context from search results
        context_parts = []
        citations = []

        for i, result in enumerate(search_results[:3], 1):  # Use top 3 results
            context_parts.append(f"""
Document {i}: {result['act_name']} - {result['section_title']}
Revenue Type: {result['revenue_type']}
Content: {result['content'][:800]}...
Score: {result['combined_score']:.3f}
""")
            citations.append({
                'document_id': result['id'],
                'act_name': result['act_name'],
                'section_title': result['section_title'],
                'revenue_type': result['revenue_type'],
                'relevance_score': result['combined_score']
            })

        context = "\n".join(context_parts)

        # Create prompt for primary response
        prompt = f"""You are an expert NSW Revenue AI Assistant. Answer the user's question based on the provided NSW revenue legislation documents.

User Question: {query}

Relevant NSW Revenue Documents:
{context}

Instructions:
1. Provide a clear, accurate answer based on the documents
2. Be specific about rates, thresholds, and procedures
3. Mention relevant act names and sections
4. If information is incomplete, clearly state what additional details are needed
5. Use professional but accessible language

Answer:"""

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert NSW Revenue legislation assistant. Provide accurate, helpful responses based on official NSW revenue documents."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.1
            )

            content = response.choices[0].message.content

            # Calculate confidence based on search scores and response quality
            avg_search_score = sum(r['combined_score'] for r in search_results[:3]) / min(3, len(search_results))
            confidence_score = min(0.95, avg_search_score * 0.8 + 0.2)

            return {
                'content': content,
                'confidence_score': confidence_score,
                'citations': citations
            }

        except Exception as e:
            logger.error(f"Error generating primary response: {e}")
            return {
                'content': "I apologize, but I encountered an error generating a response. Please try again.",
                'confidence_score': 0.0,
                'citations': citations
            }

    def _validate_response(self, primary_response: Dict, search_results: List[Dict]) -> Dict:
        """Simplified response validation"""

        confidence = primary_response['confidence_score']
        content = primary_response['content']

        # Basic validation checks
        if confidence < 0.3:
            return {
                'status': 'needs_review',
                'reason': 'Low confidence score',
                'missing_info': 'More specific information may be required'
            }

        if len(content) < 50:
            return {
                'status': 'needs_review',
                'reason': 'Response too brief',
                'missing_info': 'Response lacks sufficient detail'
            }

        if not search_results:
            return {
                'status': 'needs_review',
                'reason': 'No supporting documents found',
                'missing_info': 'No relevant NSW revenue documents found for this query'
            }

        return {
            'status': 'approved',
            'reason': 'Response meets quality standards'
        }

    def _format_source_documents(self, search_results: List[Dict]) -> List[Dict]:
        """Format source documents for response"""
        return [
            {
                'id': result['id'],
                'title': f"{result['act_name']} - {result['section_title']}",
                'revenue_type': result['revenue_type'],
                'excerpt': result['content'][:200] + "..." if len(result['content']) > 200 else result['content'],
                'relevance_score': result['combined_score'],
                'bm25_score': result['bm25_rank'],
                'vector_score': result['vector_similarity']
            }
            for result in search_results
        ]

    def _create_no_results_response(self, query: str) -> Dict:
        """Create response when no documents found"""
        return {
            'content': f"I couldn't find specific NSW revenue legislation documents related to '{query}'. This might be because:\n\n1. The query is outside the scope of NSW revenue legislation\n2. More specific terminology might be needed\n3. The information might be in a different section\n\nPlease try rephrasing your question or provide more specific details about the NSW revenue matter you're asking about.",
            'confidence_score': 0.0,
            'citations': [],
            'source_documents': [],
            'review_status': 'no_results',
            'specific_information_required': 'More specific NSW revenue terminology or context needed',
            'processing_metadata': {
                'search_results_count': 0,
                'timestamp': datetime.now().isoformat(),
                'system': 'memory_optimized_supabase'
            },
            'success': True
        }

    def _create_error_response(self, error_message: str) -> Dict:
        """Create error response"""
        return {
            'content': "I apologize, but I encountered a technical error while processing your request. Please try again in a moment.",
            'confidence_score': 0.0,
            'citations': [],
            'source_documents': [],
            'review_status': 'error',
            'error': error_message,
            'processing_metadata': {
                'timestamp': datetime.now().isoformat(),
                'system': 'memory_optimized_supabase'
            },
            'success': False
        }

    def get_system_status(self) -> Dict:
        """Get system status and statistics"""
        try:
            stats = self.search_engine.get_database_stats()
            revenue_types = self.search_engine.get_revenue_types()

            return {
                'status': 'operational',
                'database': {
                    'total_documents': stats['total_documents'],
                    'revenue_types_count': stats['revenue_types'],
                    'revenue_types': [rt['revenue_type'] for rt in revenue_types]
                },
                'system': {
                    'architecture': 'memory_optimized_supabase',
                    'search_engine': 'hybrid_bm25_vector',
                    'ai_model': self.model,
                    'memory_footprint': 'low (~100MB)'
                },
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

# Global assistant instance
assistant = None

def get_assistant() -> NSWRevenueAssistant:
    """Get or create assistant instance"""
    global assistant
    if assistant is None:
        assistant = NSWRevenueAssistant()
    return assistant

class handler(BaseHTTPRequestHandler):
    """Vercel handler for the complete NSW Revenue Assistant"""

    def do_POST(self):
        """Handle POST requests"""
        try:
            # Parse request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            # Get assistant
            assistant = get_assistant()

            # Route request
            action = request_data.get('action', 'query')

            if action == 'query':
                response = assistant.process_query(
                    query=request_data.get('query', ''),
                    revenue_type_filter=request_data.get('revenue_type'),
                    top_k=request_data.get('top_k', 5)
                )
            elif action == 'status':
                response = assistant.get_system_status()
            else:
                response = {
                    'error': f'Unknown action: {action}',
                    'available_actions': ['query', 'status'],
                    'success': False
                }

            self.send_json_response(response)

        except Exception as e:
            logger.error(f"Error in handler: {e}")
            self.send_error_response(500, str(e))

    def do_GET(self):
        """Handle GET requests for status"""
        try:
            assistant = get_assistant()
            response = assistant.get_system_status()
            self.send_json_response(response)
        except Exception as e:
            self.send_error_response(500, str(e))

    def do_OPTIONS(self):
        """Handle CORS preflight"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json_response(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_response(status_code)
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': message,
            'success': False,
            'timestamp': datetime.now().isoformat()
        }).encode('utf-8'))

    def send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')