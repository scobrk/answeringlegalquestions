"""
NSW Revenue AI Assistant - FastAPI Server
Implements the ACTUAL designed architecture with dual-agent system
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Dict, List, Optional
import os
import sys
from pathlib import Path
import logging

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import the ACTUAL designed agents
from agents.dual_agent_orchestrator import DualAgentOrchestrator
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

app = FastAPI(title="NSW Revenue AI Assistant", version="1.0.0")

# Configure CORS for web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the ACTUAL dual agent orchestrator as designed
try:
    # Try to use the full Supabase orchestrator first
    orchestrator = DualAgentOrchestrator()
    logging.info("Initialized DualAgentOrchestrator with Supabase")
except Exception as e:
    # Fallback to local orchestrator if Supabase not available
    orchestrator = LocalDualAgentOrchestrator()
    logging.info(f"Fell back to LocalDualAgentOrchestrator: {e}")

class QueryRequest(BaseModel):
    query: str
    enable_approval: bool = True
    include_metadata: bool = True

class QueryResponse(BaseModel):
    content: str
    confidence_score: float
    citations: List[str]
    source_documents: List[Dict]
    review_status: str
    specific_information_required: Optional[str] = None
    processing_metadata: Optional[Dict] = None

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "NSW Revenue AI Assistant", "status": "operational", "version": "1.0.0"}

@app.get("/health")
async def health():
    """Health check for monitoring"""
    return {"status": "healthy", "orchestrator": type(orchestrator).__name__}

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process NSW Revenue query through the ACTUAL dual-agent system
    As designed in architecture diagrams
    """
    try:
        # Process through the ACTUAL dual-agent orchestrator
        result = orchestrator.process_query(
            query=request.query,
            enable_approval=request.enable_approval,
            include_metadata=request.include_metadata
        )

        # Return structured response matching the designed interface
        response_data = {
            "content": result.final_response.content,
            "confidence_score": result.final_response.confidence_score,
            "citations": result.final_response.citations,
            "source_documents": result.final_response.source_documents,
            "review_status": result.final_response.review_status,
            "specific_information_required": result.final_response.specific_information_required
        }

        # Add processing metadata if requested
        if request.include_metadata and hasattr(result, 'processing_metadata'):
            response_data["processing_metadata"] = {
                "primary_confidence": result.primary_response.confidence,
                "approval_decision": result.approval_decision.is_approved,
                "processing_time": result.total_processing_time,
                "timestamp": result.timestamp.isoformat(),
                "query_classification": getattr(result, 'classification_result', None)
            }

        return QueryResponse(**response_data)

    except Exception as e:
        logging.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Processing error",
                "message": str(e),
                "content": "I apologize, but I encountered an error processing your query. Please try again.",
                "confidence_score": 0,
                "citations": [],
                "source_documents": [],
                "review_status": "error"
            }
        )

# Serve the static web interface
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/index.html")
@app.get("/chat")
async def serve_index():
    """Serve the main web interface"""
    return FileResponse("index.html")

# Additional endpoints for the designed system
@app.get("/api/health/detailed")
async def detailed_health():
    """Detailed health check including agent status"""
    try:
        # Test orchestrator
        test_result = orchestrator.process_query(
            query="What is NSW payroll tax?",
            enable_approval=False,
            include_metadata=False
        )

        return {
            "status": "healthy",
            "orchestrator": type(orchestrator).__name__,
            "agents_operational": True,
            "test_query_confidence": test_result.final_response.confidence_score,
            "vector_store_status": "operational"
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "orchestrator": type(orchestrator).__name__,
            "agents_operational": False
        }

if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(level=logging.INFO)

    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))

    print(f"🚀 Starting NSW Revenue AI Assistant on port {port}")
    print(f"📊 Using orchestrator: {type(orchestrator).__name__}")
    print(f"🌐 Web interface: http://localhost:{port}")
    print(f"📡 API endpoint: http://localhost:{port}/api/query")

    uvicorn.run(app, host="0.0.0.0", port=port)