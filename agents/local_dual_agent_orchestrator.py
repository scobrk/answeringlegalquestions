"""
Local Dual Agent Orchestrator - Simplified for Local Vector Store
Coordinates Local Primary Agent with simplified approval process
"""

import os
import sys
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.local_primary_agent import LocalPrimaryResponseAgent, LocalPrimaryResponse
from agents.interpretation_agent import InterpretationAgent

logger = logging.getLogger(__name__)


@dataclass
class LocalApprovalDecision:
    """Approval decision structure"""
    is_approved: bool
    confidence_adjustment: float
    feedback: str
    review_notes: List[str]


@dataclass
class LocalFinalResponse:
    """Final response after approval process"""
    content: str
    confidence_score: float
    citations: List[str]
    source_documents: List[Dict]
    review_status: str
    processing_metadata: Dict
    specific_information_required: Optional[str] = None


@dataclass
class LocalDualAgentResponse:
    """Complete dual agent response"""
    primary_response: LocalPrimaryResponse
    approval_decision: LocalApprovalDecision
    final_response: LocalFinalResponse
    total_processing_time: float
    timestamp: datetime


class LocalDualAgentOrchestrator:
    """
    Local Dual Agent Orchestrator
    Simplified version using local vector store and basic approval logic
    """

    def __init__(self):
        self.primary_agent = LocalPrimaryResponseAgent()
        self.interpretation_agent = InterpretationAgent()

        # Approval settings
        self.auto_approve_threshold = 0.7
        self.min_approval_threshold = 0.3

    def process_query(self, query: str, enable_approval: bool = True, include_metadata: bool = True, classification_result=None) -> LocalDualAgentResponse:
        """
        Process query through dual agent system using local vector store

        Args:
            query: User query
            enable_approval: Whether to run approval process
            include_metadata: Whether to include processing metadata
            classification_result: Classification result from classification agent

        Returns:
            Complete dual agent response
        """
        # Get context from local vector store
        context_docs = self._get_local_context(query)
        return self._process_with_context(query, context_docs, enable_approval, include_metadata, classification_result)

    def process_query_with_hf_context(self, query: str, hf_docs: List[Dict], enable_approval: bool = True, include_metadata: bool = True) -> LocalDualAgentResponse:
        """
        Process query through dual agent system with Hugging Face context

        Args:
            query: User query
            hf_docs: Documents from Hugging Face corpus
            enable_approval: Whether to run approval process
            include_metadata: Whether to include processing metadata

        Returns:
            Complete dual agent response
        """
        return self._process_with_context(query, hf_docs, enable_approval, include_metadata)

    def _process_with_context(self, query: str, context_docs: List[Dict], enable_approval: bool = True, include_metadata: bool = True, classification_result=None) -> LocalDualAgentResponse:
        """
        Internal method to process query with given context documents
        """
        start_time = datetime.now()

        try:
            logger.info(f"Processing query with dual agent system: {query}")

            # Step 1: Interpretation Analysis
            interpretation_result = self.interpretation_agent.interpret_sources(
                query=query,
                sources=context_docs
            )

            # Step 2: Primary Response Generation (with interpretation insights)
            primary_response = self.primary_agent.generate_response(
                query,
                context_docs,
                classification_result,
                interpretation_result
            )

            # Step 3: Approval Process (if enabled)
            if enable_approval:
                approval_decision = self._simple_approval_process(primary_response, query)
            else:
                approval_decision = LocalApprovalDecision(
                    is_approved=True,
                    confidence_adjustment=0.0,
                    feedback="Auto-approved (approval disabled)",
                    review_notes=[]
                )

            # Step 4: Generate Final Response
            final_response = self._generate_final_response(
                primary_response,
                approval_decision,
                include_metadata
            )

            # Step 5: Calculate total processing time
            total_time = (datetime.now() - start_time).total_seconds()

            return LocalDualAgentResponse(
                primary_response=primary_response,
                approval_decision=approval_decision,
                final_response=final_response,
                total_processing_time=total_time,
                timestamp=start_time
            )

        except Exception as e:
            logger.error(f"Error in dual agent processing: {e}")
            return self._generate_error_response(query, str(e), start_time)

    def _get_local_context(self, query: str) -> List[Dict]:
        """Get context documents using dynamic context layer"""
        try:
            from data.dynamic_context_layer import DynamicContextLayer
            context_layer = DynamicContextLayer()
            context_docs = context_layer.get_relevant_context(query, max_docs=5)  # Improved for quality

            # Convert ContextDocument objects to dict format expected by primary agent
            formatted_docs = []
            for doc in context_docs:
                formatted_doc = {
                    'act_name': doc.act_name or doc.title,
                    'section_number': doc.section or 'N/A',
                    'content': doc.content,
                    'similarity_score': doc.relevance_score,
                    'source': doc.source,
                    'title': doc.title
                }
                formatted_docs.append(formatted_doc)

            return formatted_docs
        except Exception as e:
            logger.warning(f"Error retrieving dynamic context: {e}")
            # Fallback to local vector store
            try:
                from data.local_vector_store import LocalVectorStore
                vector_store = LocalVectorStore()
                return vector_store.search(query, k=5, threshold=0.2)
            except Exception as e2:
                logger.warning(f"Error retrieving local context fallback: {e2}")
                return []

    def _simple_approval_process(self, primary_response: LocalPrimaryResponse, query: str) -> LocalApprovalDecision:
        """
        Simplified approval process based on confidence and basic checks
        """
        review_notes = []
        confidence_adjustment = 0.0
        is_approved = True

        # Check 1: Confidence threshold
        if primary_response.confidence < self.min_approval_threshold:
            is_approved = False
            review_notes.append(f"Low confidence score: {primary_response.confidence:.2f}")

        # Check 2: Answer completeness
        if len(primary_response.answer) < 50:
            confidence_adjustment -= 0.1
            review_notes.append("Response appears too brief")

        # Check 3: Citations availability
        if not primary_response.citations:
            confidence_adjustment -= 0.05
            review_notes.append("No citations provided")

        # Check 4: Error indicators in response
        error_indicators = ['error', 'unable', 'cannot', 'insufficient']
        if any(indicator in primary_response.answer.lower() for indicator in error_indicators):
            confidence_adjustment -= 0.1
            review_notes.append("Response contains error indicators")

        # Check 5: Auto-approve high confidence responses
        if primary_response.confidence >= self.auto_approve_threshold:
            is_approved = True
            feedback = "Auto-approved due to high confidence"
        elif is_approved:
            feedback = "Approved after review"
        else:
            feedback = "Requires manual review"

        return LocalApprovalDecision(
            is_approved=is_approved,
            confidence_adjustment=confidence_adjustment,
            feedback=feedback,
            review_notes=review_notes
        )

    def _generate_final_response(
        self,
        primary_response: LocalPrimaryResponse,
        approval_decision: LocalApprovalDecision,
        include_metadata: bool
    ) -> LocalFinalResponse:
        """Generate the final response"""

        # Adjust confidence based on approval
        final_confidence = primary_response.confidence + approval_decision.confidence_adjustment
        final_confidence = max(0.0, min(1.0, final_confidence))

        # Determine response content
        if approval_decision.is_approved:
            content = primary_response.answer
        else:
            content = (
                f"{primary_response.answer}\n\n"
                f"**Note:** This response requires additional review. "
                f"Confidence: {final_confidence:.2f}. "
                f"Please verify information independently."
            )

        # Add metadata if requested
        if include_metadata and approval_decision.review_notes:
            content += f"\n\n**Review Notes:** {'; '.join(approval_decision.review_notes)}"

        # Processing metadata
        processing_metadata = {
            'primary_processing_time': primary_response.processing_time,
            'query_type': primary_response.query_type,
            'approval_status': approval_decision.feedback,
            'source_document_count': len(primary_response.source_documents)
        }

        return LocalFinalResponse(
            content=content,
            confidence_score=final_confidence,
            citations=primary_response.citations,
            source_documents=primary_response.source_documents,
            review_status="approved" if approval_decision.is_approved else "pending_review",
            processing_metadata=processing_metadata,
            specific_information_required=primary_response.specific_information_required
        )

    def _generate_error_response(
        self,
        query: str,
        error_msg: str,
        start_time: datetime
    ) -> LocalDualAgentResponse:
        """Generate error response"""

        error_primary = LocalPrimaryResponse(
            answer=f"Error processing query: {error_msg}",
            citations=[],
            confidence=0.0,
            query_type='error',
            source_documents=[],
            timestamp=start_time,
            processing_time=0.0
        )

        error_approval = LocalApprovalDecision(
            is_approved=False,
            confidence_adjustment=0.0,
            feedback="Error occurred during processing",
            review_notes=[f"Error: {error_msg}"]
        )

        error_final = LocalFinalResponse(
            content="I encountered an error while processing your query. Please try again or rephrase your question.",
            confidence_score=0.0,
            citations=[],
            source_documents=[],
            review_status="error",
            processing_metadata={'error': error_msg},
            specific_information_required=None
        )

        total_time = (datetime.now() - start_time).total_seconds()

        return LocalDualAgentResponse(
            primary_response=error_primary,
            approval_decision=error_approval,
            final_response=error_final,
            total_processing_time=total_time,
            timestamp=start_time
        )

    def health_check(self) -> Dict:
        """Perform health check on dual agent system"""
        status = {
            'orchestrator_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Test primary agent
            test_response = self.primary_agent.generate_response("test query", [])
            status['components']['primary_agent'] = 'healthy'

            # Test vector store
            try:
                from data.local_vector_store import LocalVectorStore
                vector_store = LocalVectorStore()
                acts = vector_store.list_available_acts()
                status['components']['vector_store'] = 'healthy'
                status['available_acts'] = len(acts)
            except Exception:
                status['components']['vector_store'] = 'unhealthy'

            # Overall status
            if all(comp == 'healthy' for comp in status['components'].values()):
                status['orchestrator_status'] = 'healthy'
            else:
                status['orchestrator_status'] = 'degraded'

        except Exception as e:
            status['orchestrator_status'] = 'unhealthy'
            status['error'] = str(e)

        return status


def main():
    """Test the Local Dual Agent Orchestrator"""
    orchestrator = LocalDualAgentOrchestrator()

    # Health check
    health = orchestrator.health_check()
    print(f"🏥 Orchestrator Health: {health['orchestrator_status']}")
    for component, status in health.get('components', {}).items():
        print(f"  - {component}: {status}")

    # Test queries
    test_queries = [
        "What is the current payroll tax rate in NSW?",
        "How do I calculate land tax?",
        "What are the stamp duty concessions for first home buyers?"
    ]

    for query in test_queries:
        print(f"\n🔍 Testing: '{query}'")

        try:
            response = orchestrator.process_query(query, enable_approval=True)

            print(f"📊 Primary Confidence: {response.primary_response.confidence:.2f}")
            print(f"📊 Final Confidence: {response.final_response.confidence_score:.2f}")
            print(f"✅ Approved: {response.approval_decision.is_approved}")
            print(f"⏱️ Total Processing: {response.total_processing_time:.2f}s")

            print(f"\n💬 Final Answer:")
            print(response.final_response.content)

            if response.final_response.citations:
                print(f"\n📖 Citations:")
                for citation in response.final_response.citations:
                    print(f"  - {citation}")

        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()