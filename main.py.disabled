#!/usr/bin/env python3

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = int(os.environ.get('PORT', 8080))

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"status": "healthy", "service": "NSW Revenue AI"}')

        elif self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = b'''<!DOCTYPE html>
<html><head><title>NSW Revenue AI Assistant</title></head>
<body style="font-family: Arial; max-width: 800px; margin: 0 auto; padding: 20px;">
<h1>NSW Revenue AI Assistant</h1>
<p><strong>Status:</strong> Online and working!</p>
<h2>Ask a Question:</h2>
<input type="text" id="q" placeholder="Ask about NSW taxes..." style="width: 70%; padding: 10px;">
<button onclick="ask()" style="padding: 10px 20px;">Ask</button>
<div id="answer" style="margin-top: 20px; padding: 20px; background: #f0f0f0; border-radius: 5px;"></div>

<script>
function ask() {
    var q = document.getElementById('q').value;
    var ans = 'NSW Revenue Information:\\n\\n';

    if (q.toLowerCase().includes('payroll')) {
        ans += 'Payroll Tax: 5.45% rate for payroll over $1.2 million annually.';
    } else if (q.toLowerCase().includes('land')) {
        ans += 'Land Tax: Tax-free threshold is $755,000. Premium rates over $4 million.';
    } else if (q.toLowerCase().includes('stamp')) {
        ans += 'Stamp Duty: Varies by property value. First home buyer concessions available.';
    } else {
        ans += 'I can help with payroll tax, land tax, and stamp duty questions.';
    }

    document.getElementById('answer').innerHTML = '<h3>Answer:</h3><p>' + ans + '</p>';
}
</script>
</body></html>'''
            self.wfile.write(html)

        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def do_POST(self):
        if self.path == '/chat':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"answer": "NSW Revenue system is online", "status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress request logs

if __name__ == '__main__':
    print(f"Starting NSW Revenue AI on port {PORT}")
    server = HTTPServer(('0.0.0.0', PORT), Handler)
    server.serve_forever()