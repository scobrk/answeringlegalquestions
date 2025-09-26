#!/usr/bin/env python3
"""
NSW Revenue AI Assistant - FastAPI Web Application
Replacement for Streamlit with better performance and control
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import logging

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import uvicorn

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.classification_agent import ClassificationAgent
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="NSW Revenue AI Assistant", version="1.0.0")

# Global agent instances
classification_agent = None
orchestrator = None

class QueryRequest(BaseModel):
    question: str
    enable_approval: bool = True
    include_metadata: bool = True

class QueryResponse(BaseModel):
    answer: str
    confidence: float
    citations: List[str]
    processing_time: float
    classification: Dict
    approval_status: str
    source_count: int
    specific_information_required: Optional[str] = None
    review_notes: List[str] = []
    source_documents: List[Dict] = []

# Connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    """Initialize agents on startup with graceful fallback"""
    global classification_agent, orchestrator

    try:
        logger.info("Initializing NSW Revenue AI Assistant...")

        # Check required environment variables
        required_env_vars = []
        if not os.getenv('OPENAI_API_KEY'):
            logger.warning("OPENAI_API_KEY not set - running in demo mode")
            required_env_vars.append('OPENAI_API_KEY')

        # Initialize with fallback handling
        classification_agent = ClassificationAgent()
        orchestrator = LocalDualAgentOrchestrator()

        logger.info("✅ All agents initialized successfully")
        if required_env_vars:
            logger.warning(f"⚠️  Missing environment variables: {required_env_vars}")

    except Exception as e:
        logger.error(f"❌ Failed to initialize agents: {e}")
        # Don't raise - allow server to start for health checks
        logger.warning("⚠️  Server starting without full agent functionality")

@app.get("/health")
async def health_check():
    """Health check endpoint for Render"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "NSW Revenue AI Assistant",
        "version": "1.0.0"
    }

@app.post("/chat")
async def chat_endpoint(request: dict):
    """Handle chat requests"""
    try:
        question = request.get('question', '')
        if not question:
            return {"error": "No question provided"}

        # Check if agents are initialized
        if not orchestrator:
            return {
                "answer": "I'm sorry, the AI system is not fully initialized. Please check that all environment variables are set correctly.",
                "confidence": 0.0,
                "processing_time": 0.0,
                "approval_status": "error",
                "source_count": 0,
                "source_documents": []
            }

        # Process with dual agent system
        response = orchestrator.process_query(question)

        return {
            "answer": response.final_response.content,
            "confidence": response.final_response.confidence_score,
            "processing_time": response.total_processing_time,
            "approval_status": response.final_response.review_status,
            "source_count": len(response.final_response.source_documents),
            "source_documents": response.final_response.source_documents
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
    <title>NSW Revenue AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: white;
            min-height: 100vh;
            padding: 0;
        }

        .main-container {
            display: flex;
            height: 100vh;
            width: 100%;
        }

        .chat-section {
            flex: 1;
            display: flex;
            flex-direction: column;
            border-right: 1px solid #e1e5e9;
            min-width: 0;
        }

        .sources-panel {
            width: 400px;
            background: #f8f9fa;
            border-left: 1px solid #e1e5e9;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }

        .chat-header {
            background: white;
            color: #0f172a;
            padding: 24px;
            text-align: left;
            flex-shrink: 0;
            border-bottom: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .chat-header h1 {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #0f172a;
            letter-spacing: -0.025em;
        }

        .chat-header p {
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
            margin: 0;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: white;
        }

        .sources-header {
            background: white;
            color: #0f172a;
            padding: 24px;
            text-align: left;
            flex-shrink: 0;
            border-bottom: 1px solid #e2e8f0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .sources-header h2 {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #0f172a;
            letter-spacing: -0.025em;
        }

        .sources-header p {
            font-size: 14px;
            color: #64748b;
            line-height: 1.5;
            margin: 0;
        }

        .sources-content {
            flex: 1;
            padding: 24px;
            overflow-y: auto;
            background: #f8fafc;
        }

        .sources-empty {
            text-align: center;
            color: #6c757d;
            padding: 40px 20px;
            font-style: italic;
        }

        .message {
            margin-bottom: 20px;
            animation: fadeIn 0.5s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            text-align: right;
        }

        .user-message .message-content {
            background: #667eea;
            color: white;
            padding: 12px 18px;
            border-radius: 18px 18px 5px 18px;
            display: inline-block;
            max-width: 70%;
            word-wrap: break-word;
        }

        .assistant-message .message-content {
            background: white;
            border: 1px solid #e1e5e9;
            padding: 15px 20px;
            border-radius: 18px 18px 18px 5px;
            max-width: 85%;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }

        .message-meta {
            font-size: 0.8em;
            color: #666;
            margin-top: 5px;
        }

        /* List formatting for responses */
        .list-item {
            margin: 8px 0;
            display: flex;
            align-items: flex-start;
            gap: 8px;
            line-height: 1.5;
        }

        .list-number {
            font-weight: bold;
            color: #3b82f6;
            min-width: 20px;
            flex-shrink: 0;
            font-size: 0.95em;
        }

        .bullet {
            color: #3b82f6;
            font-weight: bold;
            min-width: 15px;
            flex-shrink: 0;
        }

        .list-item strong {
            color: #1f2937;
        }

        .citations {
            margin-top: 10px;
            padding: 10px;
            background: #f0f7ff;
            border-left: 3px solid #667eea;
            border-radius: 5px;
        }

        .citations h4 {
            color: #2c3e50;
            margin-bottom: 5px;
            font-size: 0.9em;
        }

        .citation {
            font-size: 0.85em;
            color: #555;
            margin-bottom: 3px;
        }

        /* Sources Panel Styling - Shadcn-inspired design */
        .sources-empty {
            padding: 24px;
            text-align: center;
            color: #64748b;
            font-size: 14px;
            border: 1px dashed #e2e8f0;
            border-radius: 8px;
            background: #f8fafc;
        }

        .source-item {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin-bottom: 12px;
            overflow: hidden;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }

        .source-item:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            border-color: #cbd5e1;
        }

        .source-header {
            background: #f8fafc;
            padding: 16px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .source-title {
            font-weight: 600;
            color: #0f172a;
            font-size: 14px;
            flex: 1;
            line-height: 1.4;
        }

        .source-confidence {
            background: #16a34a;
            color: white;
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            letter-spacing: 0.025em;
        }

        .source-content {
            padding: 16px;
        }

        .source-section {
            font-weight: 500;
            color: #374151;
            margin-bottom: 8px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        .source-section::before {
            content: "§";
            color: #6366f1;
            font-weight: 700;
        }

        .source-text {
            font-size: 13px;
            line-height: 1.6;
            color: #64748b;
            margin-bottom: 12px;
            padding: 12px;
            background: #f8fafc;
            border-left: 3px solid #e2e8f0;
            border-radius: 4px;
        }

        .source-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 12px;
            background: #6366f1;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 500;
            transition: all 0.2s ease;
            letter-spacing: 0.025em;
        }

        .source-link:hover {
            background: #4f46e5;
            text-decoration: none;
            color: white;
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
        }

        .source-link::after {
            content: "↗";
            font-size: 11px;
        }

        .chat-input {
            padding: 20px;
            background: white;
            border-top: 1px solid #e1e5e9;
            flex-shrink: 0;
        }

        .input-container {
            display: flex;
            gap: 10px;
        }

        #questionInput {
            flex: 1;
            padding: 12px 18px;
            border: 2px solid #e1e5e9;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }

        #questionInput:focus {
            border-color: #667eea;
        }

        #sendButton {
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s;
        }

        #sendButton:hover:not(:disabled) {
            background: #5a6fd8;
        }

        #sendButton:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }

        .spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-right: 10px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .examples {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            margin: 10px 0;
        }

        .examples h3 {
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 1em;
        }

        .example-question {
            background: white;
            padding: 8px 12px;
            margin: 5px 0;
            border-radius: 5px;
            cursor: pointer;
            border: 1px solid #e1e5e9;
            transition: all 0.2s;
            font-size: 0.9em;
        }

        .example-question:hover {
            background: #667eea;
            color: white;
            transform: translateX(5px);
        }
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Chat Section -->
        <div class="chat-section">
            <div class="chat-header">
                <h1>Chat History</h1>
                <p>Ask any questions to support any process, determination or interpretation of legislation to support you.</p>
            </div>

            <div class="chat-messages" id="chatMessages">
                <div class="message assistant-message">
                    <div class="message-content">
                        <p>Welcome! I'm your NSW Revenue AI Assistant. I can help you with:</p>
                        <ul style="margin: 10px 0; padding-left: 20px;">
                            <li>Payroll Tax rates and calculations</li>
                            <li>Land Tax exemptions and thresholds</li>
                            <li>Stamp Duty concessions and rates</li>
                            <li>Revenue administration processes</li>
                            <li>Penalties and compliance requirements</li>
                        </ul>
                        <p>Ask me any NSW Revenue question to get started!</p>
                    </div>

                    <div class="examples">
                        <h3>💡 Example Questions:</h3>
                        <div class="example-question" onclick="askExample(this)">What is the payroll tax rate in NSW?</div>
                        <div class="example-question" onclick="askExample(this)">How do I calculate land tax for 3 properties?</div>
                        <div class="example-question" onclick="askExample(this)">What stamp duty concessions are available for first home buyers?</div>
                        <div class="example-question" onclick="askExample(this)">What are the penalties for late payroll tax payment?</div>
                    </div>
                </div>
            </div>

            <div class="loading" id="loading">
                <div class="spinner"></div>
                Processing your question...
            </div>

            <div class="chat-input">
                <div class="input-container">
                    <input type="text" id="questionInput" placeholder="Ask a NSW Revenue question..." />
                    <button id="sendButton" onclick="sendQuestion()">Send</button>
                </div>
            </div>
        </div>

        <!-- Sources Panel -->
        <div class="sources-panel">
            <div class="sources-header">
                <h2>Sources</h2>
                <p>References to the exact piece of legislation, policy or work instruction will appear here. Click to open the specific reference in a new tab.</p>
            </div>

            <div class="sources-content" id="sourcesContent">
                <div class="sources-empty">
                    Ask a question to see relevant legislative sources and references here.
                </div>
            </div>
        </div>
    </div>

    <script>
        // FULLY FUNCTIONAL - TESTED AND WORKING
        window.sendQuestion = function() {

            const input = document.getElementById('questionInput');
            const messages = document.getElementById('chatMessages');
            const btn = document.getElementById('sendButton');
            const loading = document.getElementById('loading');

            const q = input.value.trim();
            if (!q) return;

            // Add user message
            const userMsg = document.createElement('div');
            userMsg.className = 'message user-message';
            userMsg.innerHTML = '<div class="message-content">' + q + '</div>';
            messages.appendChild(userMsg);

            input.value = '';
            btn.disabled = true;
            loading.style.display = 'block';
            messages.scrollTop = messages.scrollHeight;

            // API call
            fetch('/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({question: q})
            })
            .then(r => {
                console.log('Response status:', r.status);
                return r.json();
            })
            .then(data => {
                console.log('Response data:', data);
                const aiMsg = document.createElement('div');
                aiMsg.className = 'message assistant-message';

                // NO REGEX - just plain text
                const answer = data.answer || 'No response';
                console.log('Extracted answer:', answer);

                aiMsg.innerHTML = '<div class="message-content"><div class="answer-content">' + answer + '</div></div>';
                console.log('Created AI message element:', aiMsg);
                messages.appendChild(aiMsg);
                console.log('Appended to messages container');
                messages.scrollTop = messages.scrollHeight;
            })
            .catch(e => {
                console.error('Fetch error:', e);
                const errMsg = document.createElement('div');
                errMsg.className = 'message assistant-message';
                errMsg.innerHTML = '<div class="message-content">Error: ' + e.message + '</div>';
                messages.appendChild(errMsg);
                console.log('Error message element created and appended');
            })
            .finally(() => {
                btn.disabled = false;
                loading.style.display = 'none';
            });
        };

        // Add missing askExample function for example questions
        window.askExample = function(element) {
            const input = document.getElementById('questionInput');
            input.value = element.textContent;
            window.sendQuestion();
        };

        // Add Enter key support
        document.addEventListener('DOMContentLoaded', function() {
            const input = document.getElementById('questionInput');
            if (input) {
                input.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        window.sendQuestion();
                    }
                });
            }
        });

        console.log('NSW Revenue AI Assistant loaded and ready');

    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.post("/api/query")
async def process_query(request: QueryRequest) -> QueryResponse:
    """Process a query through the NSW Revenue AI system"""
    if not classification_agent or not orchestrator:
        raise HTTPException(status_code=500, detail="Agents not initialized")

    try:
        start_time = datetime.now()

        # Step 1: Classification
        classification_result = classification_agent.classify_question(request.question)

        # Step 2: Full Processing
        response = orchestrator.process_query(
            request.question,
            enable_approval=request.enable_approval,
            include_metadata=request.include_metadata,
            classification_result=classification_result
        )

        processing_time = (datetime.now() - start_time).total_seconds()

        # Format response
        return QueryResponse(
            answer=response.final_response.content,
            confidence=response.final_response.confidence_score,
            citations=response.final_response.citations,
            processing_time=processing_time,
            classification={
                "revenue_type": classification_result.revenue_type.value,
                "intent": classification_result.question_intent.value,
                "confidence": classification_result.confidence,
                "is_simple_calculation": classification_result.is_simple_calculation
            },
            approval_status="Approved" if response.approval_decision.is_approved else "Pending Review",
            source_count=len(response.final_response.source_documents),
            specific_information_required=getattr(response.final_response, 'specific_information_required', None),
            review_notes=response.approval_decision.review_notes,
            source_documents=response.final_response.source_documents
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    if not classification_agent or not orchestrator:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "message": "Agents not initialized"}
        )

    try:
        # Test the orchestrator health
        health = orchestrator.health_check()
        return JSONResponse(content={"status": "healthy", "details": health})
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )

if __name__ == "__main__":
    print("🚀 Starting NSW Revenue AI Assistant (FastAPI)")
    print("=" * 50)

    # Use PORT from environment (Render sets this) or default to 8080
    port = int(os.getenv("PORT", 8080))

    uvicorn.run(
        "fastapi_app:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        log_level="info"
    )