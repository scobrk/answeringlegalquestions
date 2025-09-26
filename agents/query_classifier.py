"""
NSW Revenue Query Classification System
Backend Agent Implementation (KAN-4)
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """NSW Revenue query types"""
    PAYROLL_TAX = "payroll_tax"
    LAND_TAX = "land_tax"
    DUTIES = "duties"
    FINES = "fines"
    GRANTS = "grants"
    ADMINISTRATION = "administration"
    GENERAL = "general"


@dataclass
class ClassificationResult:
    """Query classification result with confidence"""
    query_type: QueryType
    confidence: float
    keywords_matched: List[str]
    secondary_types: List[Tuple[QueryType, float]]


class NSWRevenueQueryClassifier:
    """
    Classifies NSW Revenue queries into specific categories
    Uses pattern matching and keyword analysis for accurate classification
    """

    def __init__(self):
        # Query type patterns and keywords
        self.classification_patterns = {
            QueryType.PAYROLL_TAX: {
                "keywords": [
                    "payroll tax", "payroll", "wages", "salary", "employer",
                    "employee", "threshold", "1.2 million", "$1,200,000",
                    "monthly wages", "annual wages", "group employer"
                ],
                "patterns": [
                    r"payroll\s+tax",
                    r"wages.*tax",
                    r"employer.*tax",
                    r"payroll.*rate",
                    r"payroll.*threshold",
                    r"1\.2\s*million",
                    r"\$1,?200,?000"
                ],
                "calculation_terms": [
                    "rate", "calculate", "calculation", "amount", "percentage",
                    "5.45%", "rate of", "how much"
                ]
            },

            QueryType.LAND_TAX: {
                "keywords": [
                    "land tax", "property tax", "land value", "unimproved value",
                    "land tax threshold", "exemption", "primary residence",
                    "principal place of residence", "land tax assessment"
                ],
                "patterns": [
                    r"land\s+tax",
                    r"property.*tax",
                    r"land.*value",
                    r"unimproved.*value",
                    r"land.*assessment",
                    r"principal.*place.*residence",
                    r"primary.*residence"
                ],
                "calculation_terms": [
                    "assessment", "value", "exemption", "threshold",
                    "calculate", "amount owed"
                ]
            },

            QueryType.DUTIES: {
                "keywords": [
                    "stamp duty", "duty", "conveyance", "transfer duty",
                    "property purchase", "real estate", "conveyancing",
                    "first home buyer", "concession", "exemption"
                ],
                "patterns": [
                    r"stamp\s+duty",
                    r"transfer\s+duty",
                    r"conveyance.*duty",
                    r"property.*purchase",
                    r"real\s+estate.*duty",
                    r"first\s+home.*buyer",
                    r"duty.*rate"
                ],
                "calculation_terms": [
                    "rate", "calculate", "amount", "percentage", "cost",
                    "how much", "purchase price"
                ]
            },

            QueryType.FINES: {
                "keywords": [
                    "fine", "penalty", "infringement", "enforcement",
                    "penalty notice", "court", "appeal", "dispute",
                    "late payment", "penalty interest"
                ],
                "patterns": [
                    r"fine",
                    r"penalty",
                    r"infringement",
                    r"penalty.*notice",
                    r"late.*payment",
                    r"penalty.*interest",
                    r"court.*order"
                ],
                "calculation_terms": [
                    "amount", "interest", "additional", "late fee"
                ]
            },

            QueryType.GRANTS: {
                "keywords": [
                    "grant", "first home owner grant", "FHOG", "rebate",
                    "concession", "assistance", "eligible", "eligibility",
                    "first home buyer"
                ],
                "patterns": [
                    r"first\s+home.*grant",
                    r"FHOG",
                    r"grant.*eligible",
                    r"rebate",
                    r"first.*home.*buyer.*grant",
                    r"home.*buyer.*assistance"
                ],
                "calculation_terms": [
                    "eligible", "qualify", "amount", "how much"
                ]
            },

            QueryType.ADMINISTRATION: {
                "keywords": [
                    "assessment", "review", "objection", "appeal",
                    "audit", "investigation", "notice", "determination",
                    "administrative", "revenue nsw", "ruling"
                ],
                "patterns": [
                    r"assessment.*review",
                    r"objection",
                    r"appeal.*decision",
                    r"revenue.*nsw",
                    r"administrative.*decision",
                    r"tax.*ruling"
                ],
                "calculation_terms": [
                    "process", "procedure", "timeline", "deadline"
                ]
            }
        }

        # Calculation indicators
        self.calculation_indicators = [
            "calculate", "calculation", "how much", "what is the",
            "rate", "percentage", "amount", "cost", "price",
            "total", "sum", "value", "worth"
        ]

        # NSW jurisdiction indicators
        self.nsw_indicators = [
            "nsw", "new south wales", "revenue nsw", "state revenue"
        ]

    def classify_query(self, query: str) -> ClassificationResult:
        """
        Classify NSW Revenue query into appropriate category

        Args:
            query: User query text

        Returns:
            ClassificationResult with classification and confidence
        """
        query_lower = query.lower().strip()

        # Score each query type
        type_scores = {}
        all_matched_keywords = []

        for query_type, patterns in self.classification_patterns.items():
            score, matched_keywords = self._calculate_type_score(query_lower, patterns)
            type_scores[query_type] = score
            all_matched_keywords.extend(matched_keywords)

        # Find best match
        best_type = max(type_scores.keys(), key=lambda k: type_scores[k])
        best_score = type_scores[best_type]

        # Build secondary types (sorted by score)
        secondary_types = [
            (qtype, score) for qtype, score in type_scores.items()
            if qtype != best_type and score > 0.1
        ]
        secondary_types.sort(key=lambda x: x[1], reverse=True)

        # Adjust confidence based on various factors
        confidence = self._calculate_confidence(
            query_lower, best_score, type_scores, all_matched_keywords
        )

        # Default to GENERAL if confidence is too low
        if confidence < 0.3:
            best_type = QueryType.GENERAL
            confidence = 0.5

        logger.info(f"Query classified as {best_type.value} (confidence: {confidence:.2f})")

        return ClassificationResult(
            query_type=best_type,
            confidence=confidence,
            keywords_matched=list(set(all_matched_keywords)),
            secondary_types=secondary_types[:3]  # Top 3 alternatives
        )

    def _calculate_type_score(self, query: str, patterns: Dict) -> Tuple[float, List[str]]:
        """
        Calculate score for a specific query type

        Args:
            query: Query text (lowercase)
            patterns: Pattern dictionary for the type

        Returns:
            Tuple of (score, matched_keywords)
        """
        score = 0.0
        matched_keywords = []

        # Keyword matching
        for keyword in patterns["keywords"]:
            if keyword.lower() in query:
                score += 1.0
                matched_keywords.append(keyword)

        # Pattern matching
        for pattern in patterns["patterns"]:
            if re.search(pattern, query, re.IGNORECASE):
                score += 1.5  # Patterns get higher weight

        # Calculation terms bonus
        for calc_term in patterns.get("calculation_terms", []):
            if calc_term.lower() in query:
                score += 0.5

        # General calculation indicators
        for calc_indicator in self.calculation_indicators:
            if calc_indicator in query:
                score += 0.3

        return score, matched_keywords

    def _calculate_confidence(self,
                            query: str,
                            best_score: float,
                            all_scores: Dict,
                            matched_keywords: List[str]) -> float:
        """
        Calculate overall confidence in classification

        Args:
            query: Query text
            best_score: Score of best matching type
            all_scores: All type scores
            matched_keywords: All matched keywords

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence from best score
        base_confidence = min(best_score / 5.0, 1.0)  # Normalize to max 5 points

        # Boost for NSW indicators
        nsw_boost = 0.0
        for indicator in self.nsw_indicators:
            if indicator in query:
                nsw_boost = 0.2
                break

        # Penalty for competing scores
        sorted_scores = sorted(all_scores.values(), reverse=True)
        if len(sorted_scores) > 1 and sorted_scores[1] > 0:
            competition_penalty = min(sorted_scores[1] / sorted_scores[0] * 0.3, 0.3)
        else:
            competition_penalty = 0.0

        # Boost for multiple keyword matches
        keyword_boost = min(len(matched_keywords) * 0.1, 0.3)

        # Calculate final confidence
        confidence = base_confidence + nsw_boost + keyword_boost - competition_penalty

        return max(0.0, min(1.0, confidence))

    def is_calculation_query(self, query: str) -> bool:
        """
        Determine if query requires calculations

        Args:
            query: Query text

        Returns:
            True if query involves calculations
        """
        query_lower = query.lower()

        # Check for calculation indicators
        for indicator in self.calculation_indicators:
            if indicator in query_lower:
                return True

        # Check for numerical values
        number_patterns = [
            r'\$[\d,]+',  # Dollar amounts
            r'\d+\.?\d*%',  # Percentages
            r'\d+\.?\d*\s*million',  # Millions
            r'\d+,?\d*',  # General numbers
        ]

        for pattern in number_patterns:
            if re.search(pattern, query_lower):
                return True

        return False

    def extract_query_entities(self, query: str, query_type: QueryType) -> Dict:
        """
        Extract relevant entities from query based on type

        Args:
            query: Query text
            query_type: Classified query type

        Returns:
            Dictionary of extracted entities
        """
        entities = {}

        # Dollar amounts
        dollar_matches = re.findall(r'\$?([\d,]+(?:\.\d{2})?)', query)
        if dollar_matches:
            entities['amounts'] = [match.replace(',', '') for match in dollar_matches]

        # Percentages
        percent_matches = re.findall(r'(\d+\.?\d*)%', query)
        if percent_matches:
            entities['percentages'] = percent_matches

        # Dates
        date_patterns = [
            r'(\d{4})',  # Years
            r'(\d{1,2}/\d{1,2}/\d{4})',  # Dates
        ]
        for pattern in date_patterns:
            matches = re.findall(pattern, query)
            if matches:
                entities.setdefault('dates', []).extend(matches)

        # Type-specific extractions
        if query_type == QueryType.PAYROLL_TAX:
            # Extract wage-related terms
            wage_terms = ['monthly', 'annual', 'weekly', 'wages', 'salary']
            entities['wage_terms'] = [term for term in wage_terms if term in query.lower()]

        elif query_type == QueryType.DUTIES:
            # Extract property-related terms
            property_terms = ['residential', 'commercial', 'property', 'home', 'house']
            entities['property_terms'] = [term for term in property_terms if term in query.lower()]

        return entities

    def get_query_complexity(self, query: str) -> str:
        """
        Assess query complexity

        Args:
            query: Query text

        Returns:
            Complexity level: 'simple', 'moderate', 'complex'
        """
        # Simple indicators
        simple_patterns = [
            r'^what is',
            r'^how much',
            r'^current rate'
        ]

        # Complex indicators
        complex_patterns = [
            r'calculate.*if',
            r'assuming.*and',
            r'multiple.*scenarios',
            r'compare.*options'
        ]

        query_lower = query.lower()

        # Check for complex patterns
        for pattern in complex_patterns:
            if re.search(pattern, query_lower):
                return 'complex'

        # Check for simple patterns
        for pattern in simple_patterns:
            if re.search(pattern, query_lower):
                return 'simple'

        # Check length and structure
        word_count = len(query.split())
        if word_count > 20 or '?' in query[:-1]:  # Question mark not at end
            return 'complex'
        elif word_count < 8:
            return 'simple'

        return 'moderate'


def main():
    """
    Test the query classifier
    """
    classifier = NSWRevenueQueryClassifier()

    # Test queries
    test_queries = [
        "What is the current payroll tax rate for wages over $1.2 million?",
        "How do I calculate stamp duty on a $800,000 residential property?",
        "Am I eligible for the first home owner grant?",
        "What is the land tax threshold for 2024?",
        "How do I appeal a penalty notice?",
        "What are the current duty rates?",
        "Revenue NSW assessment review process"
    ]

    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")

        result = classifier.classify_query(query)

        print(f"📂 Type: {result.query_type.value}")
        print(f"📊 Confidence: {result.confidence:.2f}")
        print(f"🔑 Keywords: {result.keywords_matched}")
        print(f"🧮 Is calculation: {classifier.is_calculation_query(query)}")
        print(f"📈 Complexity: {classifier.get_query_complexity(query)}")

        entities = classifier.extract_query_entities(query, result.query_type)
        if entities:
            print(f"🏷️ Entities: {entities}")


if __name__ == "__main__":
    main()