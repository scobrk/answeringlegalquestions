#!/usr/bin/env python3
"""
NSW Revenue AI Assistant - Zero Dependency Version
Uses only Python standard library - guaranteed to work on any Python 3.x
"""

import os
import json
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get port from environment or default
PORT = int(os.environ.get('PORT', 8080))

class NSWRevenueHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for NSW Revenue AI Assistant"""

    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/health':
            self.send_health_check()
        elif parsed_path.path == '/':
            self.send_home_page()
        else:
            self.send_404()

    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/chat':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                question = data.get('question', '')
                response = self.process_question(question)
                self.send_json_response(200, response)
            except Exception as e:
                logger.error(f"Error processing chat: {e}")
                self.send_json_response(500, {"error": str(e)})
        else:
            self.send_404()

    def send_health_check(self):
        """Send health check response"""
        response = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "NSW Revenue AI Assistant",
            "version": "1.0.0-zero-deps"
        }
        self.send_json_response(200, response)

    def send_json_response(self, status_code, data):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def send_home_page(self):
        """Send the main HTML page"""
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSW Revenue AI Assistant</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 90%;
        }
        h1 {
            color: #2d3748;
            text-align: center;
            margin-bottom: 10px;
            font-size: 28px;
        }
        .status {
            text-align: center;
            color: #10b981;
            margin-bottom: 30px;
            font-weight: 600;
        }
        .chat-box {
            background: #f7fafc;
            border-radius: 10px;
            padding: 20px;
            height: 300px;
            overflow-y: auto;
            margin-bottom: 20px;
            border: 1px solid #e2e8f0;
        }
        .message {
            margin: 10px 0;
            padding: 10px 15px;
            border-radius: 10px;
        }
        .user {
            background: #667eea;
            color: white;
            text-align: right;
            margin-left: 20%;
        }
        .bot {
            background: #e2e8f0;
            color: #2d3748;
            margin-right: 20%;
        }
        .input-group {
            display: flex;
            gap: 10px;
        }
        input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #e2e8f0;
            border-radius: 10px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        input:focus {
            border-color: #667eea;
        }
        button {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
        }
        button:hover {
            background: #5a67d8;
        }
        button:disabled {
            background: #cbd5e0;
            cursor: not-allowed;
        }
        .info {
            margin-top: 20px;
            padding: 15px;
            background: #fef3c7;
            border-radius: 10px;
            color: #92400e;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ NSW Revenue AI Assistant</h1>
        <div class="status">✅ System Online - Zero Dependencies</div>

        <div class="chat-box" id="chatBox">
            <div class="message bot">
                Welcome! I can help with NSW Revenue questions about:
                <br>• Payroll Tax (5.45% rate, $1.2M threshold)
                <br>• Land Tax ($755,000 threshold)
                <br>• Stamp Duty (property transfers)
            </div>
        </div>

        <div class="input-group">
            <input type="text" id="question" placeholder="Ask about NSW taxes..."
                   onkeypress="if(event.key==='Enter')sendQuestion()">
            <button onclick="sendQuestion()" id="sendBtn">Send</button>
        </div>

        <div class="info">
            💡 <strong>Running in minimal mode:</strong> This deployment uses zero external dependencies
            for maximum reliability. Basic NSW Revenue information is available.
        </div>
    </div>

    <script>
        function sendQuestion() {
            const input = document.getElementById('question');
            const chatBox = document.getElementById('chatBox');
            const sendBtn = document.getElementById('sendBtn');

            const question = input.value.trim();
            if (!question) return;

            // Add user message
            chatBox.innerHTML += '<div class="message user">' + question + '</div>';

            // Clear input and disable button
            input.value = '';
            sendBtn.disabled = true;

            // Scroll to bottom
            chatBox.scrollTop = chatBox.scrollHeight;

            // Send request
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: question})
            })
            .then(r => r.json())
            .then(data => {
                const answer = data.answer || 'Error processing question';
                chatBox.innerHTML += '<div class="message bot">' + answer + '</div>';
                chatBox.scrollTop = chatBox.scrollHeight;
            })
            .catch(e => {
                chatBox.innerHTML += '<div class="message bot">Error: ' + e.message + '</div>';
            })
            .finally(() => {
                sendBtn.disabled = false;
            });
        }
    </script>
</body>
</html>"""

        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')

    def process_question(self, question):
        """Process a question and return response"""
        q = question.lower()

        # Simple keyword-based responses
        if 'payroll' in q:
            answer = "NSW Payroll Tax: Rate is 5.45% for annual payroll over $1.2 million. Businesses below this threshold are generally exempt."
        elif 'land' in q or 'property tax' in q:
            answer = "NSW Land Tax: Tax-free threshold is $755,000. Premium rates apply over $4 million. Primary residences are exempt."
        elif 'stamp' in q or 'duty' in q:
            answer = "NSW Stamp Duty: Rates vary by property value. First home buyers may get concessions. Check revenue.nsw.gov.au for calculators."
        elif 'rate' in q or 'threshold' in q:
            answer = "Key NSW Revenue rates: Payroll tax 5.45% (threshold $1.2M), Land tax threshold $755,000, Stamp duty varies by property value."
        else:
            answer = "I can help with NSW Revenue questions about payroll tax, land tax, and stamp duty. Please ask about specific taxes or rates."

        return {
            "answer": answer,
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }

    def log_message(self, format, *args):
        """Override to reduce noise in logs"""
        if '/health' not in args[0]:
            logger.info(f"{self.address_string()} - {args[0]}")

def main():
    """Main server function"""
    print(f"""
╔════════════════════════════════════════════════════╗
║     NSW Revenue AI Assistant - Zero Dependencies   ║
║                                                    ║
║     Status: STARTING                               ║
║     Port: {PORT}                                       ║
║     Health: http://0.0.0.0:{PORT}/health              ║
║     Web UI: http://0.0.0.0:{PORT}/                    ║
╚════════════════════════════════════════════════════╝
    """)

    server = HTTPServer(('0.0.0.0', PORT), NSWRevenueHandler)
    logger.info(f"Server running on port {PORT}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down server")
        server.shutdown()

if __name__ == '__main__':
    main()