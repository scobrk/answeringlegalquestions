#!/usr/bin/env python3
"""
NSW Revenue AI Assistant - Minimal FastAPI Version for Render
Reduces dependencies to absolute minimum while maintaining core functionality
"""

import os
import sys
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import uvicorn

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="NSW Revenue AI Assistant", version="1.0.0")

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    processing_time: float
    source_count: int

# Simple fallback responses for common NSW Revenue questions
FALLBACK_RESPONSES = {
    'payroll': {
        'answer': 'NSW Payroll Tax rate is 5.45% for employers with annual payroll above $1.2 million. Small businesses under this threshold are generally exempt.',
        'confidence': 0.8
    },
    'land': {
        'answer': 'NSW Land Tax has a tax-free threshold of $755,000. Premium rates apply to land valued over $4 million. Primary residences are exempt.',
        'confidence': 0.8
    },
    'stamp': {
        'answer': 'NSW Stamp Duty rates vary by property value. First home buyers may qualify for concessions. Commercial transactions have different rates.',
        'confidence': 0.8
    },
    'default': {
        'answer': 'I can help with NSW Revenue questions including payroll tax, land tax, and stamp duty. Please provide more specific details about your query.',
        'confidence': 0.7
    }
}

def get_simple_response(question: str) -> Dict:
    """Generate a simple response based on keywords in the question"""
    question_lower = question.lower()

    if 'payroll' in question_lower:
        return FALLBACK_RESPONSES['payroll']
    elif 'land' in question_lower or 'property' in question_lower:
        return FALLBACK_RESPONSES['land']
    elif 'stamp' in question_lower or 'duty' in question_lower:
        return FALLBACK_RESPONSES['stamp']
    else:
        return FALLBACK_RESPONSES['default']

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "NSW Revenue AI Assistant (Minimal)",
        "version": "1.0.0-minimal"
    }

@app.post("/chat")
async def chat_endpoint(request: dict):
    """Handle chat requests with minimal processing"""
    try:
        question = request.get('question', '')
        if not question:
            return {"error": "No question provided"}

        # Simple keyword-based response
        response = get_simple_response(question)

        return {
            "answer": response['answer'],
            "confidence": response['confidence'],
            "processing_time": 0.1,
            "approval_status": "auto-approved",
            "source_count": 1,
            "source_documents": []
        }

    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        return {
            "answer": f"I encountered an error processing your question: {str(e)}",
            "confidence": 0.0,
            "processing_time": 0.0,
            "approval_status": "error",
            "source_count": 0,
            "source_documents": []
        }

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main chat interface"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NSW Revenue AI Assistant (Minimal)</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f8f9fa;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #2c3e50;
            text-align: center;
            margin-bottom: 30px;
        }
        .status {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .chat-area {
            border: 1px solid #ddd;
            border-radius: 5px;
            height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: #f8f9fa;
            margin-bottom: 20px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px;
            border-radius: 5px;
        }
        .user-message {
            background: #007bff;
            color: white;
            text-align: right;
        }
        .bot-message {
            background: #e9ecef;
            color: #333;
        }
        .input-area {
            display: flex;
            gap: 10px;
        }
        #questionInput {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
        }
        #sendButton {
            padding: 12px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        #sendButton:hover:not(:disabled) {
            background: #0056b3;
        }
        #sendButton:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>NSW Revenue AI Assistant</h1>

        <div class="status">
            ✅ <strong>Minimal Mode:</strong> Basic NSW Revenue assistance available.
            This version provides simple responses for payroll tax, land tax, and stamp duty questions.
        </div>

        <div class="chat-area" id="chatArea">
            <div class="message bot-message">
                <strong>Assistant:</strong> Hello! I'm running in minimal mode and can help with basic NSW Revenue questions about:
                <ul>
                    <li>Payroll Tax rates and thresholds</li>
                    <li>Land Tax calculations</li>
                    <li>Stamp Duty information</li>
                </ul>
                Ask me a question to get started!
            </div>
        </div>

        <div class="input-area">
            <input type="text" id="questionInput" placeholder="Ask about NSW payroll tax, land tax, or stamp duty..." />
            <button id="sendButton" onclick="sendQuestion()">Send</button>
        </div>
    </div>

    <script>
        function sendQuestion() {
            const input = document.getElementById('questionInput');
            const chatArea = document.getElementById('chatArea');
            const button = document.getElementById('sendButton');

            const question = input.value.trim();
            if (!question) return;

            // Add user message
            const userMsg = document.createElement('div');
            userMsg.className = 'message user-message';
            userMsg.innerHTML = '<strong>You:</strong> ' + question;
            chatArea.appendChild(userMsg);

            // Clear input and disable button
            input.value = '';
            button.disabled = true;

            // Scroll to bottom
            chatArea.scrollTop = chatArea.scrollHeight;

            // Make API call
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: question})
            })
            .then(r => r.json())
            .then(data => {
                const botMsg = document.createElement('div');
                botMsg.className = 'message bot-message';
                botMsg.innerHTML = '<strong>Assistant:</strong> ' + data.answer;
                chatArea.appendChild(botMsg);
                chatArea.scrollTop = chatArea.scrollHeight;
            })
            .catch(e => {
                const errMsg = document.createElement('div');
                errMsg.className = 'message bot-message';
                errMsg.innerHTML = '<strong>Error:</strong> ' + e.message;
                chatArea.appendChild(errMsg);
            })
            .finally(() => {
                button.disabled = false;
            });
        }

        // Enter key support
        document.getElementById('questionInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendQuestion();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    print("🚀 Starting NSW Revenue AI Assistant (Minimal Mode)")
    print("=" * 60)

    # Use PORT from environment (Render sets this) or default to 8080
    port = int(os.getenv("PORT", 8080))

    uvicorn.run(
        "fastapi_minimal:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )