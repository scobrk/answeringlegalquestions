"""
Vercel-Compatible Dual Agent Orchestrator
Simplified version for Vercel deployment that maintains the same API
Fallback implementation without heavy ML dependencies
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class VercelApprovalDecision:
    is_approved: bool
    reasoning: str
    confidence: float
    timestamp: datetime

@dataclass
class VercelPrimaryResponse:
    content: str
    confidence: float
    citations: List[str]
    source_documents: List[str]
    timestamp: datetime

@dataclass
class VercelFinalResponse:
    content: str
    confidence_score: float
    citations: List[str]
    source_documents: List[str]
    review_status: str
    specific_information_required: Optional[str] = None

@dataclass
class VercelDualAgentResult:
    primary_response: VercelPrimaryResponse
    approval_decision: VercelApprovalDecision
    final_response: VercelFinalResponse
    total_processing_time: float
    timestamp: datetime

class VercelDualAgentOrchestrator:
    """
    Simplified dual-agent orchestrator for Vercel deployment
    Maintains the same API as the full system but uses lightweight implementations
    """

    def __init__(self):
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            logger.warning("No OpenAI API key found")

    def process_query(self, query: str, enable_approval: bool = True, include_metadata: bool = True) -> VercelDualAgentResult:
        """
        Process query through simplified dual-agent system
        """
        start_time = datetime.now()

        try:
            # Simulate primary agent processing
            primary_response = self._process_primary_agent(query)

            # Simulate approval agent processing
            if enable_approval:
                approval_decision = self._process_approval_agent(primary_response, query)
            else:
                approval_decision = VercelApprovalDecision(
                    is_approved=True,
                    reasoning="Approval bypassed",
                    confidence=1.0,
                    timestamp=datetime.now()
                )

            # Generate final response
            final_response = self._generate_final_response(
                primary_response,
                approval_decision,
                query
            )

            processing_time = (datetime.now() - start_time).total_seconds()

            return VercelDualAgentResult(
                primary_response=primary_response,
                approval_decision=approval_decision,
                final_response=final_response,
                total_processing_time=processing_time,
                timestamp=start_time
            )

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            # Return error response in expected format
            error_response = VercelPrimaryResponse(
                content="I encountered an error processing your query. Please try again.",
                confidence=0.0,
                citations=[],
                source_documents=[],
                timestamp=datetime.now()
            )

            error_approval = VercelApprovalDecision(
                is_approved=False,
                reasoning="Error in processing",
                confidence=0.0,
                timestamp=datetime.now()
            )

            error_final = VercelFinalResponse(
                content="Service temporarily unavailable. Please try again.",
                confidence_score=0.0,
                citations=[],
                source_documents=[],
                review_status="error"
            )

            return VercelDualAgentResult(
                primary_response=error_response,
                approval_decision=error_approval,
                final_response=error_final,
                total_processing_time=0.0,
                timestamp=start_time
            )

    def _process_primary_agent(self, query: str) -> VercelPrimaryResponse:
        """
        Simplified primary agent processing
        """
        try:
            if self.openai_api_key:
                # Use OpenAI for actual processing
                import openai
                client = openai.OpenAI(api_key=self.openai_api_key)

                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a NSW Revenue legislation expert assistant. Provide accurate, helpful responses about NSW revenue laws, taxes, and regulations."},
                        {"role": "user", "content": query}
                    ],
                    max_tokens=500,
                    temperature=0.1
                )

                content = response.choices[0].message.content
                confidence = 0.85  # Simplified confidence calculation

            else:
                # Fallback response
                content = f"I understand you're asking about: {query}. This is a simplified response as the full system is being deployed. Please check back soon for full NSW Revenue legislation assistance."
                confidence = 0.5

            return VercelPrimaryResponse(
                content=content,
                confidence=confidence,
                citations=["NSW Revenue Legislation"],
                source_documents=["Simplified deployment version"],
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Primary agent error: {e}")
            return VercelPrimaryResponse(
                content="I'm currently being deployed. Please try again in a few moments.",
                confidence=0.3,
                citations=[],
                source_documents=[],
                timestamp=datetime.now()
            )

    def _process_approval_agent(self, primary_response: VercelPrimaryResponse, query: str) -> VercelApprovalDecision:
        """
        Simplified approval agent processing
        """
        try:
            # Simplified approval logic
            is_approved = primary_response.confidence > 0.4
            reasoning = f"Response confidence {primary_response.confidence:.2f} {'meets' if is_approved else 'below'} approval threshold"

            return VercelApprovalDecision(
                is_approved=is_approved,
                reasoning=reasoning,
                confidence=primary_response.confidence,
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Approval agent error: {e}")
            return VercelApprovalDecision(
                is_approved=False,
                reasoning="Error in approval process",
                confidence=0.0,
                timestamp=datetime.now()
            )

    def _generate_final_response(self, primary_response: VercelPrimaryResponse, approval_decision: VercelApprovalDecision, query: str) -> VercelFinalResponse:
        """
        Generate final response based on primary response and approval
        """
        if approval_decision.is_approved:
            return VercelFinalResponse(
                content=primary_response.content,
                confidence_score=primary_response.confidence,
                citations=primary_response.citations,
                source_documents=primary_response.source_documents,
                review_status="approved"
            )
        else:
            return VercelFinalResponse(
                content="I need more specific information to provide an accurate response about NSW Revenue matters. Could you please rephrase your question with more details?",
                confidence_score=0.3,
                citations=[],
                source_documents=[],
                review_status="requires_clarification",
                specific_information_required="More specific query about NSW Revenue legislation"
            )