"""
Dual-Agent Orchestrator - Coordinates Primary and Approver Agents
Backend Agent Implementation (KAN-5)
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import time
import json

from primary_agent import PrimaryResponseAgent, PrimaryResponse
from approver_agent import ApproverAgent, ApprovalDecision, FinalResponse

logger = logging.getLogger(__name__)


@dataclass
class DualAgentResponse:
    """Complete dual-agent response with all metadata"""
    query: str
    primary_response: PrimaryResponse
    approval_decision: ApprovalDecision
    final_response: FinalResponse
    total_processing_time: float
    agent_coordination_metadata: Dict
    timestamp: datetime

    def to_dict(self) -> Dict:
        """Convert to dictionary for API responses"""
        return {
            'query': self.query,
            'answer': self.final_response.final_answer,
            'citations': self.final_response.final_citations,
            'confidence': self.final_response.final_confidence,
            'validation_summary': self.final_response.validation_summary,
            'enhancements_applied': self.final_response.enhancements_applied,
            'processing_time': self.total_processing_time,
            'approved': self.approval_decision.approved,
            'timestamp': self.timestamp.isoformat(),
            'metadata': {
                'primary_processing_time': self.primary_response.processing_time,
                'approval_processing_time': self.final_response.processing_metadata.get('approval_processing_time', 0),
                'query_type': self.primary_response.query_type,
                'source_document_count': len(self.primary_response.source_documents),
                'validation_components': self.final_response.processing_metadata.get('validation_components', []),
                'coordination_metadata': self.agent_coordination_metadata
            }
        }


class DualAgentOrchestrator:
    """
    Orchestrates Primary Response Agent and Approver Agent
    Provides unified interface for dual-agent NSW Revenue query processing
    """

    def __init__(self,
                 supabase_url: str = None,
                 supabase_key: str = None,
                 openai_api_key: str = None):

        # Initialize both agents
        self.primary_agent = PrimaryResponseAgent(
            supabase_url=supabase_url,
            supabase_key=supabase_key,
            openai_api_key=openai_api_key
        )

        self.approver_agent = ApproverAgent(
            openai_api_key=openai_api_key
        )

        # Orchestration settings
        self.enable_approval = True  # Can be disabled for faster responses
        self.max_processing_time = 15.0  # Maximum total processing time
        self.retry_on_failure = True

        logger.info("Dual-Agent Orchestrator initialized successfully")

    def process_query(self, query: str,
                     enable_approval: bool = None,
                     include_metadata: bool = True) -> DualAgentResponse:
        """
        Process query through dual-agent system

        Args:
            query: User query
            enable_approval: Override approval setting
            include_metadata: Include detailed metadata in response

        Returns:
            DualAgentResponse with complete processing results
        """
        start_time = time.time()
        timestamp = datetime.now()

        # Use instance setting if not overridden
        if enable_approval is None:
            enable_approval = self.enable_approval

        coordination_metadata = {
            'approval_enabled': enable_approval,
            'include_metadata': include_metadata,
            'orchestrator_version': '1.0'
        }

        try:
            logger.info(f"Processing query with dual-agent system: {query}")

            # Phase 1: Primary Response Generation
            primary_start = time.time()
            primary_response = self.primary_agent.generate_response(query)
            primary_duration = time.time() - primary_start

            coordination_metadata['primary_agent'] = {
                'processing_time': primary_duration,
                'confidence': primary_response.confidence,
                'query_type': primary_response.query_type,
                'citations_count': len(primary_response.citations)
            }

            logger.info(f"Primary agent completed in {primary_duration:.2f}s "
                       f"with confidence {primary_response.confidence:.2f}")

            # Phase 2: Approval Process (if enabled)
            if enable_approval:
                approval_start = time.time()

                # Check if we have time remaining
                elapsed_time = time.time() - start_time
                if elapsed_time > self.max_processing_time * 0.8:
                    logger.warning("Approaching time limit, skipping approval")
                    enable_approval = False
                    coordination_metadata['approval_skipped'] = 'time_limit'

            if enable_approval:
                try:
                    approval_decision, final_response = self.approver_agent.review_response(
                        primary_response, query
                    )
                    approval_duration = time.time() - approval_start

                    coordination_metadata['approver_agent'] = {
                        'processing_time': approval_duration,
                        'approval_score': approval_decision.overall_approval_score,
                        'approved': approval_decision.approved,
                        'issues_count': len(approval_decision.issues_found)
                    }

                    logger.info(f"Approver agent completed in {approval_duration:.2f}s "
                               f"with approval: {approval_decision.approved}")

                except Exception as e:
                    logger.error(f"Approval failed, using primary response: {e}")
                    approval_decision, final_response = self._create_fallback_approval(primary_response)
                    coordination_metadata['approval_fallback'] = str(e)
            else:
                # No approval - create direct final response
                approval_decision, final_response = self._create_direct_final_response(primary_response)
                coordination_metadata['approval_skipped'] = 'disabled'

            # Phase 3: Quality Assurance
            final_response = self._quality_assurance_check(final_response, coordination_metadata)

            total_processing_time = time.time() - start_time
            coordination_metadata['total_processing_time'] = total_processing_time

            # Construct dual-agent response
            dual_response = DualAgentResponse(
                query=query,
                primary_response=primary_response,
                approval_decision=approval_decision,
                final_response=final_response,
                total_processing_time=total_processing_time,
                agent_coordination_metadata=coordination_metadata,
                timestamp=timestamp
            )

            logger.info(f"Dual-agent processing completed in {total_processing_time:.2f}s")
            return dual_response

        except Exception as e:
            logger.error(f"Dual-agent processing failed: {e}")
            return self._create_error_response(query, str(e), timestamp, start_time)

    def _create_fallback_approval(self, primary_response: PrimaryResponse) -> Tuple[ApprovalDecision, FinalResponse]:
        """Create fallback approval when approver agent fails"""

        fallback_approval = ApprovalDecision(
            approved=True,  # Approve by default on fallback
            confidence_adjustment=-0.1,  # Small penalty for fallback
            issues_found=["Approver agent unavailable - using fallback approval"],
            enhancements_made=[],
            validation_notes="Fallback approval due to approver agent failure",
            citation_validation_score=0.7,  # Conservative estimate
            fact_check_score=0.7,
            overall_approval_score=0.7
        )

        fallback_final = FinalResponse(
            original_response=primary_response,
            approval_decision=fallback_approval,
            final_answer=primary_response.answer,
            final_citations=primary_response.citations,
            final_confidence=max(0.1, primary_response.confidence - 0.1),
            validation_summary="⚠️ Fallback Approval (Approver Agent Unavailable)",
            enhancements_applied=["Fallback processing applied"],
            processing_metadata={'fallback_mode': True},
            timestamp=datetime.now()
        )

        return fallback_approval, fallback_final

    def _create_direct_final_response(self, primary_response: PrimaryResponse) -> Tuple[ApprovalDecision, FinalResponse]:
        """Create final response without approval process"""

        direct_approval = ApprovalDecision(
            approved=True,  # Direct approval
            confidence_adjustment=0.0,  # No adjustment
            issues_found=[],
            enhancements_made=["Direct processing - no approval validation"],
            validation_notes="Direct processing without approval validation",
            citation_validation_score=0.8,  # Optimistic estimate
            fact_check_score=0.8,
            overall_approval_score=0.8
        )

        direct_final = FinalResponse(
            original_response=primary_response,
            approval_decision=direct_approval,
            final_answer=primary_response.answer,
            final_citations=primary_response.citations,
            final_confidence=primary_response.confidence,
            validation_summary="✅ Direct Processing (No Validation)",
            enhancements_applied=["Direct processing applied"],
            processing_metadata={'direct_mode': True},
            timestamp=datetime.now()
        )

        return direct_approval, direct_final

    def _quality_assurance_check(self, final_response: FinalResponse, metadata: Dict) -> FinalResponse:
        """Perform final quality assurance checks"""

        qa_issues = []

        # Check response length
        if len(final_response.final_answer) < 20:
            qa_issues.append("Response too short")
        elif len(final_response.final_answer) > 2000:
            qa_issues.append("Response too long")

        # Check confidence bounds
        if final_response.final_confidence < 0.0 or final_response.final_confidence > 1.0:
            final_response.final_confidence = max(0.0, min(1.0, final_response.final_confidence))
            qa_issues.append("Confidence score corrected to valid range")

        # Check citations
        if not final_response.final_citations and 'calculation' not in final_response.final_answer.lower():
            qa_issues.append("No citations provided for legal response")

        # Update metadata if issues found
        if qa_issues:
            metadata['qa_issues'] = qa_issues
            logger.warning(f"QA issues found: {qa_issues}")

        return final_response

    def _create_error_response(self, query: str, error_msg: str,
                             timestamp: datetime, start_time: float) -> DualAgentResponse:
        """Create error response for dual-agent system failures"""

        processing_time = time.time() - start_time

        # Create minimal error responses
        error_primary = PrimaryResponse(
            answer="An error occurred while processing your query. Please try again.",
            citations=[],
            confidence=0.0,
            query_type='error',
            source_documents=[],
            timestamp=timestamp,
            processing_time=processing_time
        )

        error_approval = ApprovalDecision(
            approved=False,
            confidence_adjustment=0.0,
            issues_found=[f"System error: {error_msg}"],
            enhancements_made=[],
            validation_notes="Error during processing",
            citation_validation_score=0.0,
            fact_check_score=0.0,
            overall_approval_score=0.0
        )

        error_final = FinalResponse(
            original_response=error_primary,
            approval_decision=error_approval,
            final_answer="I encountered an error while processing your query. Please try rephrasing your question or contact support if the issue persists.",
            final_citations=[],
            final_confidence=0.0,
            validation_summary="❌ System Error",
            enhancements_applied=[],
            processing_metadata={'error': error_msg},
            timestamp=timestamp
        )

        return DualAgentResponse(
            query=query,
            primary_response=error_primary,
            approval_decision=error_approval,
            final_response=error_final,
            total_processing_time=processing_time,
            agent_coordination_metadata={'error': error_msg, 'system_failure': True},
            timestamp=timestamp
        )

    def health_check(self) -> Dict:
        """Perform comprehensive health check on dual-agent system"""

        status = {
            'orchestrator_status': 'healthy',
            'agents': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Check Primary Agent
            primary_health = self.primary_agent.health_check()
            status['agents']['primary'] = primary_health

            # Check Approver Agent
            approver_health = self.approver_agent.health_check()
            status['agents']['approver'] = approver_health

            # Overall system status
            agent_statuses = [
                primary_health.get('agent_status', 'unhealthy'),
                approver_health.get('agent_status', 'unhealthy')
            ]

            if all(s == 'healthy' for s in agent_statuses):
                status['orchestrator_status'] = 'healthy'
            elif any(s == 'healthy' for s in agent_statuses):
                status['orchestrator_status'] = 'degraded'
            else:
                status['orchestrator_status'] = 'unhealthy'

            # Coordination capabilities
            status['capabilities'] = {
                'dual_agent_processing': True,
                'approval_validation': True,
                'fallback_mode': True,
                'health_monitoring': True
            }

        except Exception as e:
            status['orchestrator_status'] = 'unhealthy'
            status['error'] = str(e)

        return status

    def configure_orchestration(self,
                              enable_approval: bool = True,
                              max_processing_time: float = 15.0,
                              retry_on_failure: bool = True) -> Dict:
        """Configure orchestration parameters"""

        self.enable_approval = enable_approval
        self.max_processing_time = max_processing_time
        self.retry_on_failure = retry_on_failure

        config = {
            'enable_approval': self.enable_approval,
            'max_processing_time': self.max_processing_time,
            'retry_on_failure': self.retry_on_failure,
            'configured_at': datetime.now().isoformat()
        }

        logger.info(f"Orchestration configured: {config}")
        return config

    def get_processing_statistics(self) -> Dict:
        """Get processing statistics for monitoring"""

        # This would be enhanced with actual metrics collection
        stats = {
            'total_queries_processed': 0,  # Would track in production
            'average_processing_time': 0.0,
            'approval_rate': 0.0,
            'error_rate': 0.0,
            'last_updated': datetime.now().isoformat()
        }

        return stats


def main():
    """
    Test the Dual-Agent Orchestrator
    """
    print("🤖 Dual-Agent Orchestrator initialized")

    # Initialize orchestrator
    orchestrator = DualAgentOrchestrator()

    # Health check
    health = orchestrator.health_check()
    print(f"🏥 Orchestrator Health: {health['orchestrator_status']}")
    for agent, status in health.get('agents', {}).items():
        print(f"  - {agent}: {status.get('agent_status', 'unknown')}")

    # Configuration test
    config = orchestrator.configure_orchestration(
        enable_approval=True,
        max_processing_time=10.0
    )
    print(f"⚙️ Configuration: {config}")

    # Test query (would need full environment to actually run)
    print("\n🔍 Ready for dual-agent query processing")
    print("📊 Supports: Primary Response + Approval Validation")
    print("🚀 Features: Fallback mode, QA checks, Health monitoring")


if __name__ == "__main__":
    main()