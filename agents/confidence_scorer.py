"""
Advanced Confidence Scoring and Citation Extraction
Backend Agent Implementation (KAN-4)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import logging
import math

from document_retriever import RetrievalContext, CitationInfo

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceMetrics:
    """Detailed confidence scoring metrics"""
    overall_confidence: float
    retrieval_confidence: float
    classification_confidence: float
    citation_confidence: float
    content_quality_score: float
    legal_precision_score: float
    factors: Dict[str, float]


@dataclass
class LegalCitation:
    """Enhanced legal citation with validation"""
    act_name: str
    year: Optional[int]
    section: Optional[str]
    subsection: Optional[str]
    clause: Optional[str]
    reference_type: str  # 'direct', 'indirect', 'implied'
    confidence: float
    context: str
    is_current: bool


class AdvancedConfidenceScorer:
    """
    Advanced confidence scoring system for NSW Revenue responses
    Combines multiple signals for accurate confidence assessment
    """

    def __init__(self):
        # Legal citation patterns for NSW Acts
        self.nsw_act_patterns = [
            # Full citations
            r'([A-Z][a-z\s]+Act)\s+(\d{4})\s+(?:\(NSW\)\s+)?[Ss]ection\s+(\d+[A-Z]*(?:\([a-z0-9]+\))*)',
            r'([A-Z][a-z\s]+Act)\s+(\d{4})\s+(?:\(NSW\)\s+)?[Ss]\.?\s*(\d+[A-Z]*(?:\([a-z0-9]+\))*)',

            # Act with section
            r'([A-Z][a-z\s]+Act\s+\d{4})\s+[Ss]ection\s+(\d+[A-Z]*)',
            r'([A-Z][a-z\s]+Act\s+\d{4})\s+[Ss]\.?\s*(\d+[A-Z]*)',

            # Section references
            r'[Ss]ection\s+(\d+[A-Z]*)\s+of\s+the\s+([A-Z][a-z\s]+Act\s+\d{4})',
            r'[Ss]\.?\s*(\d+[A-Z]*)\s+of\s+the\s+([A-Z][a-z\s]+Act\s+\d{4})',

            # Subsection patterns
            r'[Ss]ection\s+(\d+[A-Z]*)\s*\((\d+[a-z]*)\)',
            r'[Ss]\.?\s*(\d+[A-Z]*)\s*\((\d+[a-z]*)\)',
        ]

        # NSW Revenue Acts validation
        self.valid_nsw_acts = {
            'Duties Act 1997': {'current': True, 'revenue': True},
            'Payroll Tax Act 2007': {'current': True, 'revenue': True},
            'Land Tax Act 1956': {'current': True, 'revenue': True},
            'Land Tax Management Act 1956': {'current': True, 'revenue': True},
            'Revenue Administration Act 1996': {'current': True, 'revenue': True},
            'Fines Act 1996': {'current': True, 'revenue': True},
            'Penalty Notices Enforcement Act 2022': {'current': True, 'revenue': True},
            'Stamp Duties Act 1920': {'current': False, 'revenue': True},  # Superseded
        }

        # Confidence scoring weights
        self.scoring_weights = {
            'retrieval_quality': 0.25,
            'classification_accuracy': 0.15,
            'citation_validity': 0.25,
            'content_coherence': 0.15,
            'legal_precision': 0.20
        }

    def calculate_comprehensive_confidence(self,
                                         retrieval_context: RetrievalContext,
                                         llm_response: str,
                                         parsed_response: Dict) -> ConfidenceMetrics:
        """
        Calculate comprehensive confidence score

        Args:
            retrieval_context: Document retrieval context
            llm_response: Raw LLM response
            parsed_response: Parsed structured response

        Returns:
            ConfidenceMetrics with detailed scoring
        """
        try:
            # Individual confidence components
            retrieval_conf = self._calculate_retrieval_confidence(retrieval_context)
            classification_conf = retrieval_context.classification_confidence
            citation_conf = self._calculate_citation_confidence(llm_response, parsed_response)
            content_quality = self._calculate_content_quality_score(llm_response, parsed_response)
            legal_precision = self._calculate_legal_precision_score(llm_response, retrieval_context)

            # Additional factors
            factors = self._calculate_additional_factors(retrieval_context, parsed_response)

            # Weighted overall confidence
            overall_confidence = (
                retrieval_conf * self.scoring_weights['retrieval_quality'] +
                classification_conf * self.scoring_weights['classification_accuracy'] +
                citation_conf * self.scoring_weights['citation_validity'] +
                content_quality * self.scoring_weights['content_coherence'] +
                legal_precision * self.scoring_weights['legal_precision']
            )

            # Apply factor adjustments
            for factor_name, factor_value in factors.items():
                if factor_name.startswith('boost_'):
                    overall_confidence = min(1.0, overall_confidence + factor_value)
                elif factor_name.startswith('penalty_'):
                    overall_confidence = max(0.0, overall_confidence - factor_value)

            logger.info(f"Confidence calculated: {overall_confidence:.3f}")

            return ConfidenceMetrics(
                overall_confidence=overall_confidence,
                retrieval_confidence=retrieval_conf,
                classification_confidence=classification_conf,
                citation_confidence=citation_conf,
                content_quality_score=content_quality,
                legal_precision_score=legal_precision,
                factors=factors
            )

        except Exception as e:
            logger.error(f"Confidence calculation failed: {e}")
            return self._get_default_confidence()

    def _calculate_retrieval_confidence(self, context: RetrievalContext) -> float:
        """Calculate confidence from document retrieval quality"""
        if not context.retrieved_chunks:
            return 0.0

        # Average similarity score
        avg_similarity = sum(chunk.similarity_score for chunk in context.retrieved_chunks) / len(context.retrieved_chunks)

        # Number of high-quality chunks
        high_quality_chunks = sum(1 for chunk in context.retrieved_chunks if chunk.similarity_score > 0.8)
        chunk_quality_factor = high_quality_chunks / len(context.retrieved_chunks)

        # Diversity of sources (different acts/sections)
        unique_acts = set(chunk.act_name for chunk in context.retrieved_chunks)
        diversity_factor = min(len(unique_acts) / 3, 1.0)  # Bonus for multiple relevant acts

        # Combined retrieval confidence
        retrieval_confidence = (avg_similarity * 0.6) + (chunk_quality_factor * 0.3) + (diversity_factor * 0.1)

        return min(retrieval_confidence, 1.0)

    def _calculate_citation_confidence(self, llm_response: str, parsed_response: Dict) -> float:
        """Calculate confidence based on citation quality"""
        citations = self.extract_advanced_citations(llm_response)

        if not citations:
            return 0.2  # Low confidence for no citations

        valid_citation_count = 0
        total_citation_confidence = 0.0

        for citation in citations:
            # Validate citation
            is_valid = self._validate_citation(citation)
            if is_valid:
                valid_citation_count += 1

            total_citation_confidence += citation.confidence

        # Calculate citation confidence
        if citations:
            avg_citation_confidence = total_citation_confidence / len(citations)
            validity_ratio = valid_citation_count / len(citations)
            citation_confidence = avg_citation_confidence * validity_ratio
        else:
            citation_confidence = 0.2

        return min(citation_confidence, 1.0)

    def _calculate_content_quality_score(self, llm_response: str, parsed_response: Dict) -> float:
        """Calculate content quality and coherence score"""
        quality_score = 0.0

        # Check for structured response
        if 'answer' in parsed_response and parsed_response['answer']:
            quality_score += 0.3

        # Check for specific legal terminology
        legal_terms = [
            'section', 'subsection', 'act', 'regulation', 'clause',
            'pursuant to', 'in accordance with', 'as prescribed',
            'threshold', 'rate', 'exemption', 'assessment'
        ]
        term_count = sum(1 for term in legal_terms if term.lower() in llm_response.lower())
        terminology_score = min(term_count / 10, 0.2)
        quality_score += terminology_score

        # Check for numerical precision
        numbers_pattern = r'\$[\d,]+|\d+\.?\d*%|\d+[\.,]\d+'
        has_numbers = bool(re.search(numbers_pattern, llm_response))
        if has_numbers:
            quality_score += 0.2

        # Check response length (not too short, not too long)
        response_length = len(llm_response.split())
        if 50 <= response_length <= 500:
            quality_score += 0.2
        elif response_length < 20:
            quality_score -= 0.1

        # Check for hedging language (appropriate uncertainty)
        hedging_patterns = [
            r'may be', r'could be', r'generally', r'typically',
            r'depending on', r'subject to', r'unless'
        ]
        hedging_count = sum(1 for pattern in hedging_patterns
                          if re.search(pattern, llm_response, re.IGNORECASE))
        hedging_score = min(hedging_count / 5, 0.1)
        quality_score += hedging_score

        return min(quality_score, 1.0)

    def _calculate_legal_precision_score(self, llm_response: str, context: RetrievalContext) -> float:
        """Calculate legal precision and accuracy score"""
        precision_score = 0.0

        # Check for NSW-specific references
        nsw_indicators = ['NSW', 'New South Wales', 'Revenue NSW']
        nsw_mentions = sum(1 for indicator in nsw_indicators if indicator in llm_response)
        if nsw_mentions > 0:
            precision_score += 0.2

        # Check for query type alignment
        query_type_keywords = {
            'payroll_tax': ['payroll', 'wages', 'employer'],
            'land_tax': ['land', 'property', 'unimproved'],
            'duties': ['duty', 'stamp', 'conveyance'],
            'fines': ['fine', 'penalty', 'enforcement'],
            'grants': ['grant', 'eligible', 'first home'],
            'administration': ['assessment', 'review', 'appeal']
        }

        type_keywords = query_type_keywords.get(context.query_type.value, [])
        keyword_matches = sum(1 for keyword in type_keywords if keyword.lower() in llm_response.lower())
        if type_keywords:
            keyword_alignment = keyword_matches / len(type_keywords)
            precision_score += keyword_alignment * 0.3

        # Check for calculation indicators (if needed)
        if context.query_type.value in ['payroll_tax', 'duties', 'land_tax']:
            calc_indicators = ['calculate', 'rate', 'amount', '%', '$']
            calc_matches = sum(1 for indicator in calc_indicators if indicator in llm_response)
            if calc_matches > 0:
                precision_score += 0.2

        # Check for appropriate disclaimers
        disclaimer_patterns = [
            r'subject to.*conditions',
            r'professional.*advice',
            r'specific.*circumstances',
            r'current.*rates'
        ]
        has_disclaimers = any(re.search(pattern, llm_response, re.IGNORECASE)
                            for pattern in disclaimer_patterns)
        if has_disclaimers:
            precision_score += 0.1

        return min(precision_score, 1.0)

    def _calculate_additional_factors(self, context: RetrievalContext, parsed_response: Dict) -> Dict[str, float]:
        """Calculate additional confidence factors"""
        factors = {}

        # Boost for multiple relevant documents
        if len(context.retrieved_chunks) >= 3:
            factors['boost_multiple_sources'] = 0.05

        # Boost for recent documents
        current_year = datetime.now().year
        recent_docs = sum(1 for chunk in context.retrieved_chunks
                         if str(current_year) in chunk.content or str(current_year-1) in chunk.content)
        if recent_docs > 0:
            factors['boost_recent_info'] = 0.03

        # Penalty for very low similarity
        low_similarity_chunks = sum(1 for chunk in context.retrieved_chunks
                                  if chunk.similarity_score < 0.7)
        if low_similarity_chunks > len(context.retrieved_chunks) / 2:
            factors['penalty_low_similarity'] = 0.1

        # Boost for assumptions acknowledgment
        if parsed_response.get('assumptions'):
            factors['boost_transparency'] = 0.02

        # Penalty for generic responses
        generic_phrases = ['it depends', 'varies', 'consult', 'contact']
        generic_count = sum(1 for phrase in generic_phrases
                          if phrase.lower() in parsed_response.get('answer', '').lower())
        if generic_count > 1:
            factors['penalty_generic'] = 0.05

        return factors

    def extract_advanced_citations(self, text: str) -> List[LegalCitation]:
        """Extract and validate legal citations from text"""
        citations = []

        for pattern in self.nsw_act_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()

                # Parse citation components
                if len(groups) >= 2:
                    act_name = groups[0] if 'Act' in groups[0] else groups[1]
                    section = groups[1] if len(groups) > 1 and groups[1].isdigit() else None

                    # Extract year if present
                    year_match = re.search(r'(\d{4})', act_name)
                    year = int(year_match.group(1)) if year_match else None

                    # Determine reference type
                    ref_type = 'direct' if 'section' in match.group().lower() else 'indirect'

                    # Calculate citation confidence
                    confidence = self._calculate_citation_confidence_single(act_name, section, ref_type)

                    # Check if act is current
                    is_current = self._is_current_act(act_name)

                    citation = LegalCitation(
                        act_name=act_name,
                        year=year,
                        section=section,
                        subsection=None,
                        clause=None,
                        reference_type=ref_type,
                        confidence=confidence,
                        context=match.group(),
                        is_current=is_current
                    )
                    citations.append(citation)

        return citations

    def _validate_citation(self, citation: LegalCitation) -> bool:
        """Validate a legal citation against known NSW Acts"""
        # Check if act exists in our validation set
        for valid_act, properties in self.valid_nsw_acts.items():
            if valid_act.lower() in citation.act_name.lower():
                return properties.get('current', False) and properties.get('revenue', False)

        # If not in our set, apply heuristic validation
        return (citation.year and citation.year >= 1950 and
                'act' in citation.act_name.lower() and
                len(citation.act_name) > 5)

    def _calculate_citation_confidence_single(self, act_name: str, section: str, ref_type: str) -> float:
        """Calculate confidence for a single citation"""
        confidence = 0.5  # Base confidence

        # Boost for known NSW Revenue acts
        if any(known_act.lower() in act_name.lower() for known_act in self.valid_nsw_acts.keys()):
            confidence += 0.3

        # Boost for specific section reference
        if section:
            confidence += 0.2

        # Boost for direct references
        if ref_type == 'direct':
            confidence += 0.1

        return min(confidence, 1.0)

    def _is_current_act(self, act_name: str) -> bool:
        """Check if an act is current (not superseded)"""
        for valid_act, properties in self.valid_nsw_acts.items():
            if valid_act.lower() in act_name.lower():
                return properties.get('current', False)
        return True  # Assume current if not in our superseded list

    def _get_default_confidence(self) -> ConfidenceMetrics:
        """Return default confidence metrics for error cases"""
        return ConfidenceMetrics(
            overall_confidence=0.3,
            retrieval_confidence=0.3,
            classification_confidence=0.3,
            citation_confidence=0.3,
            content_quality_score=0.3,
            legal_precision_score=0.3,
            factors={}
        )


def main():
    """
    Test the confidence scorer
    """
    scorer = AdvancedConfidenceScorer()

    # Test citation extraction
    test_text = """
    According to section 31 of the Duties Act 1997 (NSW), the stamp duty rate is 5.5%.
    The Payroll Tax Act 2007 section 15 provides that wages over $1.2 million are subject to payroll tax.
    """

    citations = scorer.extract_advanced_citations(test_text)
    print(f"📚 Extracted {len(citations)} citations:")
    for citation in citations:
        print(f"  - {citation.act_name} s{citation.section} (confidence: {citation.confidence:.2f})")

    # Test confidence calculation would require full context
    print(f"\n📊 Confidence scoring system ready")
    print(f"🏷️ Known NSW Acts: {len(scorer.valid_nsw_acts)}")
    print(f"🔍 Citation patterns: {len(scorer.nsw_act_patterns)}")


if __name__ == "__main__":
    main()