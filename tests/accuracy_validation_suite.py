#!/usr/bin/env python3
"""
Accuracy Validation and Scoring Suite for NSW Revenue AI System
Validates legal accuracy, calculation precision, and citation correctness
"""

import os
import sys
import asyncio
import json
import re
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
import logging
import requests
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_framework_architecture import TestFramework, TestCase, TestResult

logger = logging.getLogger(__name__)


@dataclass
class AccuracyTestCase:
    """Test case specifically for accuracy validation"""
    id: str
    name: str
    revenue_type: str
    question: str
    expected_answer_elements: List[str]  # Key elements that must be in the answer
    expected_calculations: Dict[str, float]  # Expected numerical results
    expected_citations: List[str]  # Expected legal citations
    legal_validation_criteria: Dict[str, Any]  # Specific legal accuracy requirements
    calculation_tolerance: float = 0.01  # Allowed variance in calculations
    must_not_contain: List[str] = None  # Elements that should not be in answer
    complexity_level: str = "moderate"


@dataclass
class AccuracyResult:
    """Result of accuracy validation"""
    test_case_id: str
    overall_accuracy_score: float
    legal_accuracy_score: float
    calculation_accuracy_score: float
    citation_accuracy_score: float
    content_completeness_score: float
    factual_accuracy_score: float
    passed_accuracy_threshold: bool
    detailed_analysis: Dict[str, Any]
    errors_found: List[str]
    warnings: List[str]
    recommendations: List[str]
    timestamp: datetime


class AccuracyValidationSuite:
    """
    Comprehensive accuracy validation suite for NSW Revenue AI system
    Validates legal accuracy, calculation precision, and citation correctness
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.accuracy_threshold = 0.95  # 95% accuracy required for production
        self.test_cases = []
        self.validation_results = []

        # Known legal facts for validation
        self.legal_facts_database = self._load_legal_facts_database()

        # Current rates and thresholds (would be loaded from authoritative source)
        self.current_rates = self._load_current_rates()

        # Load accuracy test cases
        self._load_accuracy_test_cases()

    def _load_legal_facts_database(self) -> Dict[str, Any]:
        """Load database of known legal facts for validation"""
        return {
            'payroll_tax': {
                'current_rate': 0.0525,  # 5.25%
                'threshold_2024': 1200000,  # $1.2M
                'act_name': 'Payroll Tax Act 2007',
                'key_sections': ['4', '8', '31', '54'],
                'exemptions': ['charitable_institutions', 'government_bodies'],
                'grouping_required': True
            },
            'land_tax': {
                'threshold_2024': 969000,  # $969,000
                'act_name': 'Land Tax Management Act 1956',
                'ppr_exempt': True,
                'aggregation_required': True,
                'premium_rate_threshold': 4616000,  # $4.616M
                'key_sections': ['3', '10', '15', '17']
            },
            'conveyance_duty': {
                'act_name': 'Duties Act 1997',
                'fhb_threshold': 800000,  # $800,000
                'fhb_sliding_scale_start': 650000,  # $650,000
                'foreign_purchaser_rate': 0.08,  # 8%
                'key_sections': ['31', '54', '104JA'],
                'commercial_rate': 0.055  # 5.5%
            },
            'parking_space_levy': {
                'act_name': 'Parking Space Levy Act 2009',
                'rate_per_space_2024': 3180,  # $3,180 per space
                'cbd_area_only': True,
                'exemption_threshold': 50  # spaces
            }
        }

    def _load_current_rates(self) -> Dict[str, Any]:
        """Load current tax rates and thresholds"""
        return {
            'payroll_tax_rate': 0.0525,
            'payroll_tax_threshold': 1200000,
            'land_tax_threshold': 969000,
            'land_tax_premium_threshold': 4616000,
            'conveyance_duty_fhb_threshold': 800000,
            'parking_space_levy_rate': 3180,
            'foreign_purchaser_duty_rate': 0.08
        }

    def _load_accuracy_test_cases(self):
        """Load test cases specifically designed for accuracy validation"""
        accuracy_test_cases = [
            AccuracyTestCase(
                id="ACC001",
                name="Payroll Tax Rate Accuracy",
                revenue_type="payroll_tax",
                question="What is the exact payroll tax rate in NSW for 2024?",
                expected_answer_elements=["5.25%", "payroll tax", "NSW", "2024"],
                expected_calculations={"rate": 0.0525},
                expected_citations=["Payroll Tax Act 2007"],
                legal_validation_criteria={
                    "must_state_exact_rate": True,
                    "must_reference_current_year": True,
                    "must_cite_legislation": True
                }
            ),
            AccuracyTestCase(
                id="ACC002",
                name="Payroll Tax Calculation Precision",
                revenue_type="payroll_tax",
                question="Calculate payroll tax for a business with exactly $2,500,000 in annual NSW wages",
                expected_answer_elements=["$68,250", "5.25%", "$1,300,000", "taxable"],
                expected_calculations={
                    "total_wages": 2500000,
                    "threshold": 1200000,
                    "taxable_amount": 1300000,
                    "tax_owed": 68250
                },
                expected_citations=["Payroll Tax Act 2007"],
                legal_validation_criteria={
                    "must_calculate_correctly": True,
                    "must_show_threshold_deduction": True,
                    "must_apply_correct_rate": True
                },
                calculation_tolerance=0.01
            ),
            AccuracyTestCase(
                id="ACC003",
                name="Land Tax Threshold Accuracy",
                revenue_type="land_tax",
                question="What is the land tax threshold in NSW for 2024?",
                expected_answer_elements=["$969,000", "threshold", "land tax", "2024"],
                expected_calculations={"threshold": 969000},
                expected_citations=["Land Tax Management Act 1956"],
                legal_validation_criteria={
                    "must_state_exact_threshold": True,
                    "must_reference_current_year": True
                }
            ),
            AccuracyTestCase(
                id="ACC004",
                name="Multi-Property Land Tax Calculation",
                revenue_type="land_tax",
                question="Calculate land tax for properties worth $1.2M, $850K, and $1.8M (all investment properties)",
                expected_answer_elements=["$3,850,000", "aggregated", "100", "progressive"],
                expected_calculations={
                    "total_value": 3850000,
                    "threshold": 969000,
                    "taxable_value": 2881000,
                    "approximate_tax": 23000  # Approximate due to progressive rates
                },
                expected_citations=["Land Tax Management Act 1956"],
                legal_validation_criteria={
                    "must_aggregate_values": True,
                    "must_apply_progressive_rates": True,
                    "must_explain_aggregation": True
                },
                calculation_tolerance=0.05  # 5% tolerance for progressive calculations
            ),
            AccuracyTestCase(
                id="ACC005",
                name="First Home Buyer Stamp Duty Exemption",
                revenue_type="conveyance_duty",
                question="What stamp duty exemption applies to a first home buyer purchasing a $750,000 property?",
                expected_answer_elements=["full exemption", "$750,000", "first home buyer", "$800,000"],
                expected_calculations={"savings": 27950},  # Approximate stamp duty saved
                expected_citations=["Duties Act 1997"],
                legal_validation_criteria={
                    "must_identify_full_exemption": True,
                    "must_reference_threshold": True,
                    "must_explain_eligibility": True
                }
            ),
            AccuracyTestCase(
                id="ACC006",
                name="Foreign Purchaser Additional Duty",
                revenue_type="foreign_purchaser_duty",
                question="What additional duty does a foreign purchaser pay on a $2,000,000 property?",
                expected_answer_elements=["8%", "$160,000", "additional", "foreign purchaser"],
                expected_calculations={
                    "property_value": 2000000,
                    "foreign_duty_rate": 0.08,
                    "additional_duty": 160000
                },
                expected_citations=["Duties Act 1997"],
                legal_validation_criteria={
                    "must_calculate_8_percent": True,
                    "must_specify_additional": True,
                    "must_reference_base_duty": True
                }
            ),
            AccuracyTestCase(
                id="ACC007",
                name="Parking Space Levy Calculation",
                revenue_type="parking_space_levy",
                question="What parking space levy applies to 150 parking spaces in Sydney CBD?",
                expected_answer_elements=["$477,000", "150", "$3,180", "CBD"],
                expected_calculations={
                    "spaces": 150,
                    "rate_per_space": 3180,
                    "total_levy": 477000
                },
                expected_citations=["Parking Space Levy Act 2009"],
                legal_validation_criteria={
                    "must_multiply_correctly": True,
                    "must_mention_cbd_requirement": True,
                    "must_state_per_space_rate": True
                }
            ),
            AccuracyTestCase(
                id="ACC008",
                name="Citation Accuracy - Legal References",
                revenue_type="conveyance_duty",
                question="What section of the Duties Act 1997 covers first home buyer exemptions?",
                expected_answer_elements=["section 54", "Duties Act 1997", "first home buyer"],
                expected_calculations={},
                expected_citations=["Duties Act 1997", "section 54"],
                legal_validation_criteria={
                    "must_cite_correct_section": True,
                    "must_cite_correct_act": True,
                    "must_be_specific": True
                }
            ),
            AccuracyTestCase(
                id="ACC009",
                name="Complex Multi-Tax Calculation Accuracy",
                revenue_type="multi_tax",
                question="For a business with $3.4M payroll and 12 properties worth $43.2M total including 240 parking spaces, calculate total NSW revenue obligations",
                expected_answer_elements=["payroll tax", "land tax", "parking space levy", "total"],
                expected_calculations={
                    "payroll_tax": 115500,  # ($3.4M - $1.2M) × 5.25%
                    "parking_levy": 763200,  # 240 × $3,180
                    "land_tax": 3500000,  # Approximate for $43.2M portfolio
                    "total_approximate": 4378700
                },
                expected_citations=["Payroll Tax Act 2007", "Land Tax Management Act 1956", "Parking Space Levy Act 2009"],
                legal_validation_criteria={
                    "must_calculate_all_taxes": True,
                    "must_provide_breakdown": True,
                    "must_sum_correctly": True
                },
                calculation_tolerance=0.1,  # 10% tolerance for complex calculations
                complexity_level="expert"
            ),
            AccuracyTestCase(
                id="ACC010",
                name="Rate Change Historical Accuracy",
                revenue_type="payroll_tax",
                question="What was the payroll tax rate before the current 5.25% rate?",
                expected_answer_elements=["4.85%", "increased", "July 2022"],
                expected_calculations={"previous_rate": 0.0485},
                expected_citations=["Payroll Tax Act 2007"],
                legal_validation_criteria={
                    "must_state_previous_rate": True,
                    "must_mention_change_date": True,
                    "must_be_historically_accurate": True
                },
                must_not_contain=["5.25%", "current rate"]  # Should not confuse with current rate
            )
        ]

        self.test_cases = accuracy_test_cases

    async def run_comprehensive_accuracy_validation(self) -> Dict[str, Any]:
        """
        Run comprehensive accuracy validation across all test cases
        """
        logger.info("🎯 Starting Comprehensive Accuracy Validation Suite")

        validation_results = {
            'suite_name': 'Comprehensive Accuracy Validation',
            'start_time': datetime.now(),
            'test_results': [],
            'overall_accuracy_scores': {},
            'critical_issues': [],
            'recommendations': [],
            'production_readiness': {}
        }

        # Run all accuracy test cases
        for test_case in self.test_cases:
            logger.info(f"Validating accuracy for: {test_case.name}")

            try:
                result = await self._validate_single_test_case(test_case)
                validation_results['test_results'].append(result)
                self.validation_results.append(result)

            except Exception as e:
                logger.error(f"Accuracy validation failed for {test_case.id}: {e}")
                error_result = self._create_error_accuracy_result(test_case, str(e))
                validation_results['test_results'].append(error_result)

        # Calculate overall accuracy scores
        validation_results['overall_accuracy_scores'] = self._calculate_overall_accuracy_scores()

        # Identify critical issues
        validation_results['critical_issues'] = self._identify_critical_accuracy_issues()

        # Generate recommendations
        validation_results['recommendations'] = self._generate_accuracy_recommendations()

        # Assess production readiness
        validation_results['production_readiness'] = self._assess_production_readiness()

        validation_results['end_time'] = datetime.now()
        validation_results['total_duration'] = (validation_results['end_time'] - validation_results['start_time']).total_seconds()

        # Generate detailed accuracy report
        self._generate_accuracy_report(validation_results)

        return validation_results

    async def _validate_single_test_case(self, test_case: AccuracyTestCase) -> AccuracyResult:
        """
        Validate accuracy for a single test case
        """
        # Get AI response
        response_data = await self._get_ai_response(test_case.question)

        if not response_data:
            return self._create_error_accuracy_result(test_case, "No response received")

        answer = response_data.get('answer', '')
        citations = response_data.get('citations', [])
        confidence = response_data.get('confidence', 0.0)

        # Perform multi-dimensional accuracy validation
        legal_accuracy = self._validate_legal_accuracy(test_case, answer, response_data)
        calculation_accuracy = self._validate_calculation_accuracy(test_case, answer)
        citation_accuracy = self._validate_citation_accuracy(test_case, citations, answer)
        content_completeness = self._validate_content_completeness(test_case, answer)
        factual_accuracy = self._validate_factual_accuracy(test_case, answer)

        # Calculate overall accuracy score
        overall_accuracy = (
            legal_accuracy * 0.3 +
            calculation_accuracy * 0.25 +
            citation_accuracy * 0.2 +
            content_completeness * 0.15 +
            factual_accuracy * 0.1
        )

        # Identify errors and recommendations
        errors_found = []
        warnings = []
        recommendations = []

        if legal_accuracy < 0.8:
            errors_found.append("Legal accuracy below acceptable threshold")
        if calculation_accuracy < 0.9:
            errors_found.append("Calculation accuracy below acceptable threshold")
        if citation_accuracy < 0.7:
            warnings.append("Citation accuracy could be improved")

        # Check for content that must not be present
        if test_case.must_not_contain:
            for forbidden_element in test_case.must_not_contain:
                if forbidden_element.lower() in answer.lower():
                    errors_found.append(f"Answer contains forbidden element: {forbidden_element}")

        return AccuracyResult(
            test_case_id=test_case.id,
            overall_accuracy_score=overall_accuracy,
            legal_accuracy_score=legal_accuracy,
            calculation_accuracy_score=calculation_accuracy,
            citation_accuracy_score=citation_accuracy,
            content_completeness_score=content_completeness,
            factual_accuracy_score=factual_accuracy,
            passed_accuracy_threshold=overall_accuracy >= self.accuracy_threshold,
            detailed_analysis={
                'answer_length': len(answer),
                'confidence': confidence,
                'response_data': response_data,
                'test_case_complexity': test_case.complexity_level
            },
            errors_found=errors_found,
            warnings=warnings,
            recommendations=recommendations,
            timestamp=datetime.now()
        )

    def _validate_legal_accuracy(self, test_case: AccuracyTestCase, answer: str, response_data: Dict) -> float:
        """
        Validate legal accuracy against known legal facts
        """
        score = 1.0
        answer_lower = answer.lower()

        # Get legal facts for this revenue type
        legal_facts = self.legal_facts_database.get(test_case.revenue_type, {})

        # Check specific legal validation criteria
        criteria = test_case.legal_validation_criteria

        if criteria.get('must_state_exact_rate'):
            # Check if exact rate is mentioned
            if test_case.revenue_type == 'payroll_tax':
                if '5.25%' not in answer and '0.0525' not in answer:
                    score -= 0.3

        if criteria.get('must_reference_current_year'):
            if '2024' not in answer:
                score -= 0.2

        if criteria.get('must_cite_legislation'):
            act_name = legal_facts.get('act_name', '')
            if act_name and act_name.lower() not in answer_lower:
                score -= 0.3

        if criteria.get('must_calculate_correctly'):
            # This is handled in calculation accuracy
            pass

        if criteria.get('must_apply_correct_rate'):
            expected_rate = legal_facts.get('current_rate')
            if expected_rate:
                rate_patterns = [f"{expected_rate*100:.2f}%", f"{expected_rate:.4f}"]
                if not any(pattern in answer for pattern in rate_patterns):
                    score -= 0.4

        return max(0.0, score)

    def _validate_calculation_accuracy(self, test_case: AccuracyTestCase, answer: str) -> float:
        """
        Validate calculation accuracy against expected results
        """
        if not test_case.expected_calculations:
            return 1.0  # No calculations to validate

        score = 1.0
        total_calculations = len(test_case.expected_calculations)
        correct_calculations = 0

        for calc_name, expected_value in test_case.expected_calculations.items():
            # Extract numbers from the answer
            numbers = self._extract_numbers_from_text(answer)

            # Check if expected value is present within tolerance
            tolerance = test_case.calculation_tolerance
            found_match = False

            for number in numbers:
                if abs(number - expected_value) / expected_value <= tolerance:
                    found_match = True
                    correct_calculations += 1
                    break

            if not found_match:
                logger.warning(f"Expected calculation {calc_name}={expected_value} not found in answer")

        if total_calculations > 0:
            score = correct_calculations / total_calculations

        return score

    def _validate_citation_accuracy(self, test_case: AccuracyTestCase, citations: List[str], answer: str) -> float:
        """
        Validate citation accuracy and completeness
        """
        if not test_case.expected_citations:
            return 1.0  # No citations required

        score = 1.0
        answer_lower = answer.lower()

        # Check if expected citations are present
        found_citations = 0
        total_expected = len(test_case.expected_citations)

        for expected_citation in test_case.expected_citations:
            citation_found = False

            # Check in formal citations list
            for citation in citations:
                if expected_citation.lower() in citation.lower():
                    citation_found = True
                    break

            # Check in answer text if not found in citations
            if not citation_found and expected_citation.lower() in answer_lower:
                citation_found = True

            if citation_found:
                found_citations += 1

        if total_expected > 0:
            score = found_citations / total_expected

        # Penalty for incorrect citations (hallucinated legal references)
        if self._contains_hallucinated_citations(citations + [answer]):
            score *= 0.5  # 50% penalty for hallucinated citations

        return score

    def _validate_content_completeness(self, test_case: AccuracyTestCase, answer: str) -> float:
        """
        Validate that answer contains all expected elements
        """
        if not test_case.expected_answer_elements:
            return 1.0

        answer_lower = answer.lower()
        found_elements = 0
        total_elements = len(test_case.expected_answer_elements)

        for element in test_case.expected_answer_elements:
            if element.lower() in answer_lower:
                found_elements += 1

        return found_elements / total_elements if total_elements > 0 else 1.0

    def _validate_factual_accuracy(self, test_case: AccuracyTestCase, answer: str) -> float:
        """
        Validate factual accuracy against known facts database
        """
        score = 1.0
        answer_lower = answer.lower()

        # Check for common factual errors
        factual_errors = [
            ("payroll tax rate is 4.85%", 0.3),  # Old rate
            ("land tax threshold is $755,000", 0.4),  # Old threshold
            ("stamp duty on first $14,000 is 1.25%", 0.2),  # Outdated information
            ("parking space levy is $2,960", 0.3),  # Old rate
        ]

        for error_text, penalty in factual_errors:
            if error_text in answer_lower:
                score -= penalty

        # Check for contradictory information
        if "payroll tax" in answer_lower and "land tax" in answer_lower:
            # Make sure these aren't confused
            if "payroll tax rate is" in answer_lower and "land tax rate is" in answer_lower:
                # Both rates mentioned - check they're not confused
                pass

        return max(0.0, score)

    def _extract_numbers_from_text(self, text: str) -> List[float]:
        """
        Extract all numerical values from text for calculation validation
        """
        numbers = []

        # Pattern for various number formats
        patterns = [
            r'\$([0-9,]+(?:\.[0-9]+)?)',  # Currency: $1,234.56
            r'([0-9,]+(?:\.[0-9]+)?)%',   # Percentage: 5.25%
            r'\b([0-9,]+(?:\.[0-9]+)?)\b',  # General numbers: 1,234.56
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    # Remove commas and convert to float
                    number = float(match.replace(',', ''))
                    numbers.append(number)
                except ValueError:
                    continue

        return numbers

    def _contains_hallucinated_citations(self, citation_texts: List[str]) -> bool:
        """
        Check if citations contain hallucinated legal references
        """
        # Known valid NSW acts
        valid_acts = [
            "payroll tax act 2007",
            "land tax management act 1956",
            "duties act 1997",
            "taxation administration act 1996",
            "parking space levy act 2009",
            "revenue laws amendment act"
        ]

        for citation_text in citation_texts:
            citation_lower = citation_text.lower()

            # Look for act references
            if " act " in citation_lower:
                # Check if it matches a known valid act
                is_valid = any(valid_act in citation_lower for valid_act in valid_acts)

                if not is_valid and ("nsw" in citation_lower or "new south wales" in citation_lower):
                    # Possible hallucinated NSW act
                    return True

        return False

    async def _get_ai_response(self, question: str) -> Optional[Dict[str, Any]]:
        """
        Get AI response for accuracy validation
        """
        try:
            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": question,
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"API request failed: {response.status_code}")
                return None

        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            return None

    def _create_error_accuracy_result(self, test_case: AccuracyTestCase, error_message: str) -> AccuracyResult:
        """
        Create error result for failed accuracy validation
        """
        return AccuracyResult(
            test_case_id=test_case.id,
            overall_accuracy_score=0.0,
            legal_accuracy_score=0.0,
            calculation_accuracy_score=0.0,
            citation_accuracy_score=0.0,
            content_completeness_score=0.0,
            factual_accuracy_score=0.0,
            passed_accuracy_threshold=False,
            detailed_analysis={'error': error_message},
            errors_found=[f"Test execution failed: {error_message}"],
            warnings=[],
            recommendations=["Fix test execution issues before assessing accuracy"],
            timestamp=datetime.now()
        )

    def _calculate_overall_accuracy_scores(self) -> Dict[str, float]:
        """
        Calculate overall accuracy scores across all test cases
        """
        if not self.validation_results:
            return {}

        scores = {
            'overall_accuracy': np.mean([r.overall_accuracy_score for r in self.validation_results]),
            'legal_accuracy': np.mean([r.legal_accuracy_score for r in self.validation_results]),
            'calculation_accuracy': np.mean([r.calculation_accuracy_score for r in self.validation_results]),
            'citation_accuracy': np.mean([r.citation_accuracy_score for r in self.validation_results]),
            'content_completeness': np.mean([r.content_completeness_score for r in self.validation_results]),
            'factual_accuracy': np.mean([r.factual_accuracy_score for r in self.validation_results]),
            'passed_tests': sum(1 for r in self.validation_results if r.passed_accuracy_threshold),
            'total_tests': len(self.validation_results),
            'pass_rate': sum(1 for r in self.validation_results if r.passed_accuracy_threshold) / len(self.validation_results)
        }

        return scores

    def _identify_critical_accuracy_issues(self) -> List[str]:
        """
        Identify critical accuracy issues that must be fixed
        """
        issues = []

        # Check for systematic accuracy problems
        overall_scores = self._calculate_overall_accuracy_scores()

        if overall_scores.get('legal_accuracy', 0) < 0.85:
            issues.append("Legal accuracy below 85% - critical for compliance")

        if overall_scores.get('calculation_accuracy', 0) < 0.9:
            issues.append("Calculation accuracy below 90% - critical for tax calculations")

        if overall_scores.get('pass_rate', 0) < 0.95:
            issues.append("Overall pass rate below 95% - not production ready")

        # Check for specific problematic test cases
        critical_failures = [r for r in self.validation_results if r.overall_accuracy_score < 0.7]
        if critical_failures:
            issues.append(f"{len(critical_failures)} test cases with critically low accuracy (<70%)")

        return issues

    def _generate_accuracy_recommendations(self) -> List[str]:
        """
        Generate recommendations to improve accuracy
        """
        recommendations = []

        overall_scores = self._calculate_overall_accuracy_scores()

        if overall_scores.get('citation_accuracy', 0) < 0.8:
            recommendations.append("Improve citation accuracy by validating against authoritative legal databases")

        if overall_scores.get('calculation_accuracy', 0) < 0.95:
            recommendations.append("Implement dedicated calculation validation module with unit tests")

        if overall_scores.get('factual_accuracy', 0) < 0.9:
            recommendations.append("Update knowledge base with current rates and legislation")

        # Check for common error patterns
        all_errors = []
        for result in self.validation_results:
            all_errors.extend(result.errors_found)

        if any("calculation" in error.lower() for error in all_errors):
            recommendations.append("Review and improve numerical calculation logic")

        if any("citation" in error.lower() for error in all_errors):
            recommendations.append("Implement citation validation against NSW legislation database")

        return recommendations

    def _assess_production_readiness(self) -> Dict[str, Any]:
        """
        Assess if system is ready for production based on accuracy metrics
        """
        overall_scores = self._calculate_overall_accuracy_scores()

        production_ready = (
            overall_scores.get('overall_accuracy', 0) >= 0.95 and
            overall_scores.get('legal_accuracy', 0) >= 0.9 and
            overall_scores.get('calculation_accuracy', 0) >= 0.95 and
            overall_scores.get('pass_rate', 0) >= 0.95
        )

        assessment = {
            'production_ready': production_ready,
            'accuracy_meets_threshold': overall_scores.get('overall_accuracy', 0) >= self.accuracy_threshold,
            'legal_accuracy_acceptable': overall_scores.get('legal_accuracy', 0) >= 0.9,
            'calculation_accuracy_acceptable': overall_scores.get('calculation_accuracy', 0) >= 0.95,
            'overall_scores': overall_scores,
            'critical_issues_count': len(self._identify_critical_accuracy_issues()),
            'recommendations_count': len(self._generate_accuracy_recommendations())
        }

        return assessment

    def _generate_accuracy_report(self, validation_results: Dict[str, Any]):
        """
        Generate detailed accuracy validation report
        """
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = reports_dir / f"accuracy_validation_report_{timestamp}.json"

        # Make results JSON serializable
        serializable_results = self._make_serializable(validation_results)

        with open(report_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)

        logger.info(f"Accuracy validation report generated: {report_path}")

    def _make_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, AccuracyResult):
            return asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, np.float64):
            return float(obj)
        else:
            return obj


async def main():
    """
    Run the accuracy validation suite
    """
    accuracy_suite = AccuracyValidationSuite()

    print("🎯 NSW Revenue AI Accuracy Validation Suite")
    print("="*60)

    # Run comprehensive accuracy validation
    results = await accuracy_suite.run_comprehensive_accuracy_validation()

    # Print summary
    scores = results['overall_accuracy_scores']
    readiness = results['production_readiness']

    print(f"\n📊 ACCURACY VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Overall Accuracy: {scores.get('overall_accuracy', 0)*100:.1f}%")
    print(f"Legal Accuracy: {scores.get('legal_accuracy', 0)*100:.1f}%")
    print(f"Calculation Accuracy: {scores.get('calculation_accuracy', 0)*100:.1f}%")
    print(f"Citation Accuracy: {scores.get('citation_accuracy', 0)*100:.1f}%")
    print(f"Pass Rate: {scores.get('pass_rate', 0)*100:.1f}%")
    print(f"Production Ready: {'✅' if readiness['production_ready'] else '❌'}")

    # Print critical issues
    if results['critical_issues']:
        print(f"\n⚠️ CRITICAL ISSUES:")
        for i, issue in enumerate(results['critical_issues'], 1):
            print(f"{i}. {issue}")

    # Print recommendations
    if results['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")

    return 0 if readiness['production_ready'] else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))