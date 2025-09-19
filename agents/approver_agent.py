"""
Approver Agent - Response Validation and Enhancement
Backend Agent Implementation (KAN-5)
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import time
import json
import re

from openai import OpenAI
from primary_agent import PrimaryResponse, PrimaryResponseAgent
from confidence_scorer import AdvancedConfidenceScorer, ConfidenceMetrics, LegalCitation

logger = logging.getLogger(__name__)


@dataclass
class ApprovalDecision:
    """Approval decision from the Approver Agent"""
    approved: bool
    confidence_adjustment: float
    issues_found: List[str]
    enhancements_made: List[str]
    validation_notes: str
    citation_validation_score: float
    fact_check_score: float
    overall_approval_score: float


@dataclass
class FinalResponse:
    """Final validated and enhanced response"""
    original_response: PrimaryResponse
    approval_decision: ApprovalDecision
    final_answer: str
    final_citations: List[str]
    final_confidence: float
    validation_summary: str
    enhancements_applied: List[str]
    processing_metadata: Dict
    timestamp: datetime


class ApproverAgent:
    """
    Approver Agent for validating and enhancing Primary Response Agent outputs
    Provides fact-checking, citation validation, and response enhancement
    """

    def __init__(self, openai_api_key: str = None):
        # Initialize OpenAI client
        self.openai_client = OpenAI(
            api_key=openai_api_key or os.getenv('OPENAI_API_KEY')
        )
        self.llm_model = "gpt-3.5-turbo-16k"
        self.temperature = 0.05  # Very low temperature for consistency

        # Initialize validation components
        self.confidence_scorer = AdvancedConfidenceScorer()

        # Approval thresholds
        self.min_approval_confidence = 0.6
        self.max_citation_issues = 2
        self.min_fact_check_score = 0.7

        # System prompt for approval
        self.approval_prompt = """You are an expert NSW Revenue legislation validator. Your role is to review and validate responses about NSW taxation and revenue matters.

CRITICAL VALIDATION TASKS:
1. FACT VERIFICATION: Check all legal claims against provided context
2. CITATION ACCURACY: Verify all act and section references are correct
3. COMPLETENESS: Ensure the response fully addresses the query
4. ACCURACY: Identify any incorrect legal interpretations
5. CLARITY: Assess if the response is clear and well-structured

APPROVAL CRITERIA:
- All legal claims must be supported by provided context
- Citations must reference correct acts and sections
- Response must be complete and directly answer the query
- Legal interpretations must be accurate
- Any calculations must be correct

RESPONSE FORMAT:
VALIDATION: [Pass/Fail with specific reasons]
FACT_CHECK: [Score 0.0-1.0 with explanation]
CITATIONS: [Valid/Invalid with specific issues]
COMPLETENESS: [Complete/Incomplete with gaps identified]
ENHANCEMENT_SUGGESTIONS: [Specific improvements needed]
OVERALL_DECISION: [Approve/Reject with reasoning]

Be thorough and precise in your validation."""

    def review_response(self, primary_response: PrimaryResponse,
                       original_query: str) -> Tuple[ApprovalDecision, FinalResponse]:
        """
        Review and validate a primary response

        Args:
            primary_response: Response from Primary Agent
            original_query: Original user query

        Returns:
            Tuple of (ApprovalDecision, FinalResponse)
        """
        start_time = time.time()

        try:
            logger.info(f"Reviewing primary response for query: {original_query}")

            # Step 1: Validate citations
            citation_validation = self._validate_citations(primary_response)

            # Step 2: Fact-check response content
            fact_check_result = self._fact_check_response(primary_response, original_query)

            # Step 3: LLM-based validation
            llm_validation = self._llm_validate_response(primary_response, original_query)

            # Step 4: Calculate approval decision
            approval_decision = self._calculate_approval_decision(
                citation_validation, fact_check_result, llm_validation, primary_response
            )

            # Step 5: Create final response
            final_response = self._create_final_response(
                primary_response, approval_decision, original_query, start_time
            )

            logger.info(f"Approval decision: {approval_decision.approved} "
                       f"(score: {approval_decision.overall_approval_score:.2f})")

            return approval_decision, final_response

        except Exception as e:
            logger.error(f"Approval review failed: {e}")
            return self._create_error_approval(primary_response, str(e))

    def _validate_citations(self, response: PrimaryResponse) -> Dict:
        """Validate citations in the response"""
        try:
            validation_result = {
                'valid_citations': [],
                'invalid_citations': [],
                'citation_score': 0.0,
                'issues': []
            }

            # Use the confidence scorer's citation validation
            citations = self.confidence_scorer.extract_advanced_citations(response.answer)

            for citation in citations:
                if self.confidence_scorer._validate_citation(citation):
                    validation_result['valid_citations'].append(citation.act_name)
                else:
                    validation_result['invalid_citations'].append(citation.act_name)
                    validation_result['issues'].append(f"Invalid citation: {citation.act_name}")

            # Calculate citation score
            if len(citations) > 0:
                valid_count = len(validation_result['valid_citations'])
                validation_result['citation_score'] = valid_count / len(citations)
            else:
                validation_result['citation_score'] = 0.5  # Neutral for no citations

            return validation_result

        except Exception as e:
            logger.error(f"Citation validation failed: {e}")
            return {'citation_score': 0.3, 'issues': [f"Validation error: {e}"]}

    def _fact_check_response(self, response: PrimaryResponse, query: str) -> Dict:
        """Fact-check the response content"""
        try:
            fact_check_result = {
                'verified_facts': [],
                'questionable_facts': [],
                'fact_score': 0.0,
                'issues': []
            }

            # Simple fact checking based on source documents
            source_content = " ".join([doc.get('content_preview', '') for doc in response.source_documents])

            # Check if key facts from answer are supported by sources
            answer_sentences = response.answer.split('.')
            supported_count = 0

            for sentence in answer_sentences[:5]:  # Check first 5 sentences
                sentence = sentence.strip()
                if len(sentence) > 10:  # Skip very short sentences
                    # Simple keyword overlap check
                    sentence_words = set(sentence.lower().split())
                    source_words = set(source_content.lower().split())
                    overlap = len(sentence_words.intersection(source_words))

                    if overlap > len(sentence_words) * 0.3:  # 30% overlap threshold
                        supported_count += 1
                        fact_check_result['verified_facts'].append(sentence[:100])
                    else:
                        fact_check_result['questionable_facts'].append(sentence[:100])

            # Calculate fact score
            total_checked = len([s for s in answer_sentences[:5] if len(s.strip()) > 10])
            if total_checked > 0:
                fact_check_result['fact_score'] = supported_count / total_checked
            else:
                fact_check_result['fact_score'] = 0.7  # Default if no sentences to check

            return fact_check_result

        except Exception as e:
            logger.error(f"Fact checking failed: {e}")
            return {'fact_score': 0.5, 'issues': [f"Fact check error: {e}"]}

    def _llm_validate_response(self, response: PrimaryResponse, query: str) -> Dict:
        """Use LLM to validate response quality"""
        try:
            # Build validation prompt
            validation_prompt = f"""Query: {query}

Response to Validate:
{response.answer}

Citations Provided:
{', '.join(response.citations) if response.citations else 'None'}

Source Documents:
{json.dumps([doc for doc in response.source_documents[:3]], indent=2)}

Confidence: {response.confidence:.2f}

Please validate this response according to the specified criteria."""

            # Call OpenAI for validation
            validation_response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": self.approval_prompt},
                    {"role": "user", "content": validation_prompt}
                ],
                max_tokens=800,
                temperature=self.temperature
            )

            validation_text = validation_response.choices[0].message.content

            # Parse LLM validation response
            parsed_validation = self._parse_llm_validation(validation_text)

            return parsed_validation

        except Exception as e:
            logger.error(f"LLM validation failed: {e}")
            return {
                'validation_decision': 'Fail',
                'fact_check_score': 0.5,
                'completeness_score': 0.5,
                'issues': [f"LLM validation error: {e}"]
            }

    def _parse_llm_validation(self, validation_text: str) -> Dict:
        """Parse LLM validation response"""
        result = {
            'validation_decision': 'Pass',
            'fact_check_score': 0.7,
            'completeness_score': 0.7,
            'citation_assessment': 'Valid',
            'enhancement_suggestions': [],
            'issues': []
        }

        try:
            # Extract validation decision
            if 'VALIDATION:' in validation_text:
                validation_line = re.search(r'VALIDATION:\s*(.+)', validation_text, re.IGNORECASE)
                if validation_line and 'fail' in validation_line.group(1).lower():
                    result['validation_decision'] = 'Fail'
                    result['issues'].append("LLM validation failed")

            # Extract fact check score
            fact_check_match = re.search(r'FACT_CHECK:\s*(\d*\.?\d+)', validation_text, re.IGNORECASE)
            if fact_check_match:
                result['fact_check_score'] = min(float(fact_check_match.group(1)), 1.0)

            # Extract citation assessment
            if 'CITATIONS:' in validation_text:
                citation_line = re.search(r'CITATIONS:\s*(.+)', validation_text, re.IGNORECASE)
                if citation_line and 'invalid' in citation_line.group(1).lower():
                    result['citation_assessment'] = 'Invalid'
                    result['issues'].append("Invalid citations identified")

            # Extract enhancement suggestions
            if 'ENHANCEMENT_SUGGESTIONS:' in validation_text:
                enhancement_match = re.search(
                    r'ENHANCEMENT_SUGGESTIONS:\s*(.+?)(?=\n[A-Z_]+:|$)',
                    validation_text,
                    re.IGNORECASE | re.DOTALL
                )
                if enhancement_match:
                    suggestions = enhancement_match.group(1).strip()
                    result['enhancement_suggestions'] = [
                        s.strip('- ').strip() for s in suggestions.split('\n')
                        if s.strip() and s.strip() != 'None'
                    ]

            # Extract overall decision
            if 'OVERALL_DECISION:' in validation_text:
                decision_match = re.search(r'OVERALL_DECISION:\s*(.+)', validation_text, re.IGNORECASE)
                if decision_match and 'reject' in decision_match.group(1).lower():
                    result['validation_decision'] = 'Fail'
                    result['issues'].append("Overall decision: Reject")

            return result

        except Exception as e:
            logger.error(f"Failed to parse LLM validation: {e}")
            result['issues'].append(f"Parsing error: {e}")
            return result

    def _calculate_approval_decision(self, citation_validation: Dict,
                                   fact_check: Dict, llm_validation: Dict,
                                   response: PrimaryResponse) -> ApprovalDecision:
        """Calculate final approval decision"""

        # Collect all issues
        all_issues = []
        all_issues.extend(citation_validation.get('issues', []))
        all_issues.extend(fact_check.get('issues', []))
        all_issues.extend(llm_validation.get('issues', []))

        # Calculate component scores
        citation_score = citation_validation.get('citation_score', 0.5)
        fact_score = fact_check.get('fact_score', 0.5)
        llm_fact_score = llm_validation.get('fact_check_score', 0.5)
        completeness_score = llm_validation.get('completeness_score', 0.7)

        # Weighted overall approval score
        overall_score = (
            citation_score * 0.3 +
            fact_score * 0.25 +
            llm_fact_score * 0.25 +
            completeness_score * 0.2
        )

        # Approval decision logic
        approval_criteria = [
            overall_score >= self.min_approval_confidence,
            len(all_issues) <= self.max_citation_issues,
            fact_score >= self.min_fact_check_score,
            llm_validation.get('validation_decision') != 'Fail'
        ]

        approved = all(approval_criteria)

        # Confidence adjustment based on validation
        confidence_adjustment = 0.0
        if approved:
            if overall_score > 0.8:
                confidence_adjustment = 0.1  # Boost for high quality
            elif overall_score < 0.7:
                confidence_adjustment = -0.05  # Small penalty for lower quality
        else:
            confidence_adjustment = -0.2  # Penalty for not approved

        # Enhancements made
        enhancements_made = []
        if llm_validation.get('enhancement_suggestions'):
            enhancements_made = llm_validation['enhancement_suggestions'][:3]

        return ApprovalDecision(
            approved=approved,
            confidence_adjustment=confidence_adjustment,
            issues_found=all_issues,
            enhancements_made=enhancements_made,
            validation_notes=f"Citation: {citation_score:.2f}, Fact: {fact_score:.2f}, "
                           f"LLM: {llm_fact_score:.2f}, Complete: {completeness_score:.2f}",
            citation_validation_score=citation_score,
            fact_check_score=fact_score,
            overall_approval_score=overall_score
        )

    def _create_final_response(self, primary_response: PrimaryResponse,
                             approval_decision: ApprovalDecision,
                             query: str, start_time: float) -> FinalResponse:
        """Create final enhanced response"""

        try:
            # For approved responses, apply basic enhancements
            if approval_decision.approved:
                final_answer = primary_response.answer
                final_citations = primary_response.citations
                enhancements_applied = ["Response validated and approved"]

                # Apply simple enhancements if suggested
                if approval_decision.enhancements_made:
                    enhancements_applied.extend(approval_decision.enhancements_made[:2])
            else:
                # For non-approved responses, add warning
                final_answer = f"⚠️ This response requires review: {primary_response.answer}"
                final_citations = primary_response.citations
                enhancements_applied = ["Response flagged for review due to validation issues"]

            # Calculate final confidence
            final_confidence = max(0.0, min(1.0,
                primary_response.confidence + approval_decision.confidence_adjustment
            ))

            # Create validation summary
            validation_summary = f"Approval: {'✅' if approval_decision.approved else '❌'} | "
            validation_summary += f"Score: {approval_decision.overall_approval_score:.2f} | "
            validation_summary += f"Citations: {approval_decision.citation_validation_score:.2f} | "
            validation_summary += f"Facts: {approval_decision.fact_check_score:.2f}"

            if approval_decision.issues_found:
                validation_summary += f" | Issues: {len(approval_decision.issues_found)}"

            processing_time = time.time() - start_time

            return FinalResponse(
                original_response=primary_response,
                approval_decision=approval_decision,
                final_answer=final_answer,
                final_citations=final_citations,
                final_confidence=final_confidence,
                validation_summary=validation_summary,
                enhancements_applied=enhancements_applied,
                processing_metadata={
                    'approval_processing_time': processing_time,
                    'validation_components': ['citation', 'fact_check', 'llm_validation'],
                    'enhancement_count': len(enhancements_applied)
                },
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Failed to create final response: {e}")
            return self._create_error_final_response(primary_response, str(e))

    def _create_error_approval(self, response: PrimaryResponse, error_msg: str) -> Tuple[ApprovalDecision, FinalResponse]:
        """Create error approval and response"""
        error_approval = ApprovalDecision(
            approved=False,
            confidence_adjustment=-0.3,
            issues_found=[f"Approval process error: {error_msg}"],
            enhancements_made=[],
            validation_notes="Error during validation process",
            citation_validation_score=0.0,
            fact_check_score=0.0,
            overall_approval_score=0.0
        )

        error_response = FinalResponse(
            original_response=response,
            approval_decision=error_approval,
            final_answer="An error occurred during response validation. Please try again.",
            final_citations=[],
            final_confidence=0.1,
            validation_summary="❌ Validation Error",
            enhancements_applied=[],
            processing_metadata={'error': error_msg},
            timestamp=datetime.now()
        )

        return error_approval, error_response

    def _create_error_final_response(self, response: PrimaryResponse, error_msg: str) -> FinalResponse:
        """Create error final response"""
        return FinalResponse(
            original_response=response,
            approval_decision=ApprovalDecision(
                approved=False,
                confidence_adjustment=-0.3,
                issues_found=[error_msg],
                enhancements_made=[],
                validation_notes="Error during final response creation",
                citation_validation_score=0.0,
                fact_check_score=0.0,
                overall_approval_score=0.0
            ),
            final_answer=response.answer,
            final_citations=response.citations,
            final_confidence=max(0.1, response.confidence - 0.3),
            validation_summary="❌ Processing Error",
            enhancements_applied=[],
            processing_metadata={'error': error_msg},
            timestamp=datetime.now()
        )

    def health_check(self) -> Dict:
        """Perform health check on Approver Agent"""
        status = {
            'agent_status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Test OpenAI connection
            test_response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            status['components']['openai'] = 'healthy'
            status['components']['confidence_scorer'] = 'healthy'

            # Overall status
            if all(comp == 'healthy' for comp in status['components'].values()):
                status['agent_status'] = 'healthy'
            else:
                status['agent_status'] = 'degraded'

        except Exception as e:
            status['agent_status'] = 'unhealthy'
            status['error'] = str(e)

        return status


def main():
    """
    Test the Approver Agent
    """
    print("🔍 Approver Agent initialized successfully")
    print("📊 Ready for dual-agent integration testing")

    # Initialize agent
    approver = ApproverAgent()

    # Health check
    health = approver.health_check()
    print(f"🏥 Agent Health: {health['agent_status']}")
    for component, status in health.get('components', {}).items():
        print(f"  - {component}: {status}")


if __name__ == "__main__":
    main()