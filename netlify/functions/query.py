"""
Python Netlify Function for NSW Revenue AI Assistant
Uses the ACTUAL LocalDualAgentOrchestrator for contextual responses
"""

import json
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Import the actual dual agent orchestrator
from agents.local_dual_agent_orchestrator import LocalDualAgentOrchestrator

# Initialize orchestrator (cached for performance)
orchestrator = None

def handler(event, context):
    """Main handler for Netlify Function"""
    global orchestrator

    # CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    }

    # Handle preflight requests
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': ''
        }

    # Only accept POST requests
    if event.get('httpMethod') != 'POST':
        return {
            'statusCode': 405,
            'headers': headers,
            'body': json.dumps({'error': 'Method not allowed'})
        }

    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        query = body.get('query', '')

        if not query:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Query is required'})
            }

        # Initialize orchestrator if not already done
        if orchestrator is None:
            orchestrator = LocalDualAgentOrchestrator()

        # Process query through the ACTUAL dual-agent system
        result = orchestrator.process_query(
            query=query,
            enable_approval=True,
            include_metadata=True
        )

        # Return structured response matching the original format
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

        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(response)
        }

    except Exception as e:
        # Return error response
        error_response = {
            'error': f'Processing error: {str(e)}',
            'content': 'I apologize, but I encountered an error processing your query. Please try again.',
            'confidence_score': 0,
            'citations': [],
            'source_documents': [],
            'review_status': 'error'
        }

        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps(error_response)
        }