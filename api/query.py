"""
Vercel Serverless Function for NSW Revenue AI Assistant
Minimal test version
"""

import json
from http.server import BaseHTTPRequestHandler

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
            else:
                # Minimal test response
                response = {
                    'content': f'Test response for: {query}. NSW Revenue AI Assistant is being deployed.',
                    'confidence_score': 0.5,
                    'citations': ['Test citation'],
                    'source_documents': ['Test deployment'],
                    'review_status': 'test'
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