"""
Vercel Serverless Function for NSW Revenue AI Assistant
Uses the ACTUAL dual-agent orchestrator system
"""

import json
import sys
import os
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

# Import the COMPLETE dual-agent system with NSW Revenue vector store
orchestrator = None
orchestrator_type = "None"

try:
    # Progressive loading: First try ML dependencies with a timeout and memory check
    print("🔄 Attempting to load ML dependencies...")

    # Test memory-efficient loading
    import sys
    import gc

    # Force garbage collection before loading heavy dependencies
    gc.collect()

    # Try numpy first (lightest)
    import numpy
    print("  ✅ NumPy loaded")

    # Try FAISS (medium weight)
    import faiss
    print("  ✅ FAISS loaded")

    # Try sentence transformers (heaviest)
    from sentence_transformers import SentenceTransformer
    print("  ✅ SentenceTransformers loaded")

    print("✅ All ML dependencies loaded successfully")

    # Now load the full local dual-agent orchestrator
    from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator
    orchestrator = LocalDualAgentOrchestrator()
    orchestrator_type = "LocalDualAgentOrchestrator"
    print("✅ Successfully loaded LocalDualAgentOrchestrator with full NSW Revenue capabilities")

except (ImportError, MemoryError, OSError) as e:
    print(f"❌ ML Dependencies missing: {e}")
    try:
        # Fallback to Vercel-compatible orchestrator
        from agents.vercel_dual_agent_orchestrator import VercelDualAgentOrchestrator
        orchestrator = VercelDualAgentOrchestrator()
        orchestrator_type = "VercelDualAgentOrchestrator"
        print("⚠️ Using simplified VercelDualAgentOrchestrator (limited capability)")
    except ImportError as e2:
        print(f"❌ VercelDualAgentOrchestrator import error: {e2}")
        # Final fallback
        try:
            from agents.dual_agent_orchestrator import DualAgentOrchestrator
            orchestrator = DualAgentOrchestrator()
            orchestrator_type = "DualAgentOrchestrator"
            print("⚠️ Using basic DualAgentOrchestrator")
        except Exception as e3:
            print(f"❌ Failed to load any orchestrator: {e3}")
            orchestrator = None
            orchestrator_type = "None"

print(f"🔧 Active orchestrator: {orchestrator_type}")

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle POST requests to /api/query"""

        # Set CORS headers
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        try:
            # Parse request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            data = json.loads(body)

            query = data.get('query', '')

            if not query:
                response = {
                    'error': 'Query is required',
                    'content': 'Please provide a query.',
                    'confidence_score': 0,
                    'citations': [],
                    'source_documents': [],
                    'review_status': 'error'
                }
            elif orchestrator:
                # Process through the ACTUAL dual-agent system with full NSW Revenue capabilities
                result = orchestrator.process_query(
                    query=query,
                    enable_approval=data.get('enable_approval', True),
                    include_metadata=data.get('include_metadata', True)
                )

                # Format response based on orchestrator type
                if orchestrator_type == "LocalDualAgentOrchestrator":
                    # Full local system response format
                    response = {
                        'content': result.final_response.content,
                        'confidence_score': result.final_response.confidence_score,
                        'citations': result.final_response.citations,
                        'source_documents': result.final_response.source_documents,
                        'review_status': result.final_response.review_status,
                        'specific_information_required': result.final_response.specific_information_required,
                        'processing_metadata': {
                            'orchestrator': orchestrator_type,
                            'primary_confidence': result.primary_response.confidence,
                            'approval_decision': result.approval_decision.is_approved,
                            'processing_time': result.total_processing_time,
                            'timestamp': result.timestamp.isoformat(),
                            'has_vector_search': True,
                            'nsw_revenue_coverage': '67 revenue types'
                        }
                    }
                else:
                    # Fallback orchestrator response format
                    response = {
                        'content': result.final_response.content,
                        'confidence_score': result.final_response.confidence_score,
                        'citations': result.final_response.citations,
                        'source_documents': result.final_response.source_documents,
                        'review_status': result.final_response.review_status,
                        'specific_information_required': getattr(result.final_response, 'specific_information_required', None),
                        'processing_metadata': {
                            'orchestrator': orchestrator_type,
                            'primary_confidence': result.primary_response.confidence,
                            'approval_decision': result.approval_decision.is_approved,
                            'processing_time': result.total_processing_time,
                            'timestamp': result.timestamp.isoformat(),
                            'has_vector_search': False,
                            'note': 'Limited capability - missing ML dependencies'
                        }
                    }
            else:
                # Fallback if orchestrator fails to load
                response = {
                    'content': 'Service temporarily unavailable. Please try again.',
                    'confidence_score': 0,
                    'citations': [],
                    'source_documents': [],
                    'review_status': 'error'
                }

            self.wfile.write(json.dumps(response).encode())

        except Exception as e:
            error_response = {
                'error': str(e),
                'content': 'I encountered an error processing your query.',
                'confidence_score': 0,
                'citations': [],
                'source_documents': [],
                'review_status': 'error'
            }
            self.wfile.write(json.dumps(error_response).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()