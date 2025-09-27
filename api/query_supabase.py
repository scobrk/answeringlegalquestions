"""
Vercel serverless function for NSW Revenue legislation queries
Memory-optimized using Supabase backend
"""

import json
import os
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import logging

# Import our lightweight search engine
from .supabase_search import get_search_engine

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests for search"""
        try:
            # Parse query parameters
            parsed_url = urlparse(self.path)
            params = parse_qs(parsed_url.query)

            query = params.get('q', [''])[0]
            top_k = int(params.get('top_k', [5])[0])
            revenue_type = params.get('revenue_type', [None])[0]

            if not query:
                self.send_error_response(400, "Missing query parameter 'q'")
                return

            # Get search engine instance
            search_engine = get_search_engine()

            # Perform search
            results = search_engine.search(
                query=query,
                top_k=top_k,
                revenue_type_filter=revenue_type
            )

            # Return results
            self.send_json_response({
                'query': query,
                'results': results,
                'total_results': len(results),
                'revenue_type_filter': revenue_type
            })

        except Exception as e:
            logger.error(f"Error in query handler: {e}")
            self.send_error_response(500, str(e))

    def do_POST(self):
        """Handle POST requests for search"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))

            query = request_data.get('query', '')
            top_k = request_data.get('top_k', 5)
            revenue_type = request_data.get('revenue_type', None)

            if not query:
                self.send_error_response(400, "Missing 'query' field")
                return

            # Get search engine instance
            search_engine = get_search_engine()

            # Perform search
            results = search_engine.search(
                query=query,
                top_k=top_k,
                revenue_type_filter=revenue_type
            )

            # Return results
            self.send_json_response({
                'query': query,
                'results': results,
                'total_results': len(results),
                'revenue_type_filter': revenue_type,
                'success': True
            })

        except Exception as e:
            logger.error(f"Error in POST query handler: {e}")
            self.send_error_response(500, str(e))

    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_headers()
        self.end_headers()

    def send_json_response(self, data):
        """Send JSON response with CORS headers"""
        self.send_response(200)
        self.send_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode('utf-8'))

    def send_error_response(self, status_code, message):
        """Send error response"""
        self.send_response(status_code)
        self.send_headers()
        self.end_headers()
        self.wfile.write(json.dumps({
            'error': message,
            'success': False
        }).encode('utf-8'))

    def send_headers(self):
        """Send common headers"""
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')