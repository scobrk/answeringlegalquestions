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

# Import the ACTUAL COMPLETE dual-agent system
try:
    from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator
    orchestrator = LocalDualAgentOrchestrator()
    print("Successfully loaded LocalDualAgentOrchestrator")
except ImportError as e:
    print(f"LocalDualAgentOrchestrator import error: {e}")
    # Fallback to Vercel-compatible orchestrator
    try:
        from agents.vercel_dual_agent_orchestrator import VercelDualAgentOrchestrator
        orchestrator = VercelDualAgentOrchestrator()
        print("Successfully loaded VercelDualAgentOrchestrator")
    except ImportError as e2:
        print(f"VercelDualAgentOrchestrator import error: {e2}")
        # Final fallback to basic orchestrator
        try:
            from agents.dual_agent_orchestrator import DualAgentOrchestrator
            orchestrator = DualAgentOrchestrator()
            print("Successfully loaded DualAgentOrchestrator")
        except Exception as e3:
            print(f"Failed to load any orchestrator: {e3}")
            orchestrator = None

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
                # Process through the ACTUAL dual-agent system
                result = orchestrator.process_query(
                    query=query,
                    enable_approval=data.get('enable_approval', True),
                    include_metadata=data.get('include_metadata', True)
                )

                response = {
                    'content': result.final_response.content,
                    'confidence_score': result.final_response.confidence_score,
                    'citations': result.final_response.citations,
                    'source_documents': result.final_response.source_documents,
                    'review_status': result.final_response.review_status,
                    'specific_information_required': result.final_response.specific_information_required,
                    'processing_metadata': {
                        'primary_confidence': result.primary_response.confidence,
                        'approval_decision': result.approval_decision.is_approved,
                        'processing_time': result.total_processing_time,
                        'timestamp': result.timestamp.isoformat()
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