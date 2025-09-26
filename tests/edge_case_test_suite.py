#!/usr/bin/env python3
"""
Edge Case and Complex Scenario Test Suite for NSW Revenue AI System
Tests complex multi-tax scenarios, boundary conditions, and edge cases
"""

import os
import sys
import asyncio
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import logging
import random
import string

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_framework_architecture import TestFramework, TestCase, TestResult

logger = logging.getLogger(__name__)


@dataclass
class EdgeCaseTestCase:
    """Test case for edge cases and complex scenarios"""
    id: str
    name: str
    category: str  # boundary, multi_tax, invalid_input, extreme_values, etc.
    test_query: str
    expected_behavior: str  # How system should behave
    validation_criteria: Dict[str, Any]
    complexity_rating: int  # 1-10 scale
    should_fail_gracefully: bool = False
    expected_error_handling: Optional[str] = None
    stress_test: bool = False


@dataclass
class EdgeCaseResult:
    """Result of edge case testing"""
    test_case_id: str
    category: str
    passed: bool
    actual_behavior: str
    response_time: float
    error_handling_score: float
    robustness_score: float
    edge_case_coverage_score: float
    detailed_analysis: Dict[str, Any]
    issues_found: List[str]
    recommendations: List[str]
    timestamp: datetime


class EdgeCaseTestSuite:
    """
    Comprehensive edge case and complex scenario testing suite
    Tests system robustness, boundary conditions, and complex multi-tax scenarios
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.edge_case_test_cases = []
        self.test_results = []

        # Load edge case test scenarios
        self._load_edge_case_scenarios()

    def _load_edge_case_scenarios(self):
        """Load comprehensive edge case test scenarios"""
        edge_cases = [
            # Boundary Value Tests
            EdgeCaseTestCase(
                id="EDGE001",
                name="Payroll Tax Threshold Boundary",
                category="boundary",
                test_query="What payroll tax applies to wages of exactly $1,200,000?",
                expected_behavior="Handle threshold boundary precisely, explain no tax at threshold",
                validation_criteria={
                    "must_handle_exact_threshold": True,
                    "must_explain_threshold_rule": True,
                    "must_calculate_zero_tax": True
                },
                complexity_rating=6
            ),
            EdgeCaseTestCase(
                id="EDGE002",
                name="Payroll Tax Just Above Threshold",
                category="boundary",
                test_query="What payroll tax applies to wages of $1,200,001?",
                expected_behavior="Calculate minimal tax on $1 above threshold",
                validation_criteria={
                    "must_calculate_minimal_tax": True,
                    "must_show_calculation": True,
                    "tax_amount_should_be_small": True
                },
                complexity_rating=7
            ),
            EdgeCaseTestCase(
                id="EDGE003",
                name="Land Tax Zero Scenario",
                category="boundary",
                test_query="Do I pay land tax on my principal residence worth $2.5 million?",
                expected_behavior="Explain PPR exemption clearly, zero tax owed",
                validation_criteria={
                    "must_explain_ppr_exemption": True,
                    "must_state_zero_tax": True,
                    "must_not_calculate_tax": True
                },
                complexity_rating=5
            ),

            # Multi-Tax Complex Scenarios
            EdgeCaseTestCase(
                id="EDGE004",
                name="Massive Multi-Tax Scenario",
                category="multi_tax",
                test_query="For a mining conglomerate with $125M payroll, 847 properties worth $2.8B, 15,000 parking spaces, coal royalties on 45M tonnes, and petroleum royalties on offshore drilling, calculate total NSW revenue obligations",
                expected_behavior="Handle extremely complex multi-tax calculation systematically",
                validation_criteria={
                    "must_identify_all_tax_types": True,
                    "must_provide_breakdown": True,
                    "must_handle_large_numbers": True,
                    "must_not_crash": True
                },
                complexity_rating=10
            ),
            EdgeCaseTestCase(
                id="EDGE005",
                name="Foreign Investment Complex Portfolio",
                category="multi_tax",
                test_query="A foreign sovereign wealth fund purchases 450 commercial properties across NSW totaling $12.7 billion, establishing 25 subsidiaries with combined payroll of $89 million. What are all NSW revenue implications including ongoing obligations?",
                expected_behavior="Handle complex foreign investment scenario with multiple entities",
                validation_criteria={
                    "must_address_foreign_purchaser_duty": True,
                    "must_consider_ongoing_obligations": True,
                    "must_handle_entity_structures": True,
                    "must_calculate_multiple_taxes": True
                },
                complexity_rating=9
            ),
            EdgeCaseTestCase(
                id="EDGE006",
                name="Gaming and Entertainment Complex",
                category="multi_tax",
                test_query="A casino and entertainment complex has $250M gaming revenue, $45M payroll, 50 properties worth $380M, 2,500 parking spaces, liquor licenses, and entertainment venues. Calculate all NSW revenue obligations",
                expected_behavior="Handle specialized gaming taxes plus standard business taxes",
                validation_criteria={
                    "must_calculate_gaming_taxes": True,
                    "must_include_standard_taxes": True,
                    "must_handle_specialized_licenses": True,
                    "must_provide_comprehensive_total": True
                },
                complexity_rating=8
            ),

            # Invalid Input Handling
            EdgeCaseTestCase(
                id="EDGE007",
                name="Empty Query",
                category="invalid_input",
                test_query="",
                expected_behavior="Handle empty query gracefully with helpful message",
                validation_criteria={
                    "must_not_crash": True,
                    "must_provide_helpful_response": True,
                    "must_not_hallucinate": True
                },
                complexity_rating=3,
                should_fail_gracefully=True,
                expected_error_handling="polite_error_message"
            ),
            EdgeCaseTestCase(
                id="EDGE008",
                name="Non-English Query",
                category="invalid_input",
                test_query="¿Cuál es la tasa del impuesto sobre la nómina en NSW?",
                expected_behavior="Handle non-English query appropriately",
                validation_criteria={
                    "must_not_crash": True,
                    "should_indicate_language_limitation": True,
                    "may_attempt_translation": False
                },
                complexity_rating=4,
                should_fail_gracefully=True
            ),
            EdgeCaseTestCase(
                id="EDGE009",
                name="Special Characters and Emojis",
                category="invalid_input",
                test_query="What's the 💰 payroll tax 📊 for a business with $2.5M wages? 🤔",
                expected_behavior="Handle special characters and emojis, extract meaningful content",
                validation_criteria={
                    "must_extract_meaningful_content": True,
                    "must_ignore_emojis": True,
                    "must_calculate_correctly": True
                },
                complexity_rating=5
            ),
            EdgeCaseTestCase(
                id="EDGE010",
                name="Extremely Long Query",
                category="invalid_input",
                test_query="What is the payroll tax rate " + "for a business " * 500 + "with $2.5M in wages?",
                expected_behavior="Handle very long queries without performance degradation",
                validation_criteria={
                    "must_not_timeout": True,
                    "must_extract_key_information": True,
                    "response_time_reasonable": True
                },
                complexity_rating=6
            ),

            # Extreme Values
            EdgeCaseTestCase(
                id="EDGE011",
                name="Massive Dollar Amounts",
                category="extreme_values",
                test_query="Calculate payroll tax for a multinational with $847,392,485,273 in NSW wages",
                expected_behavior="Handle extremely large numbers correctly",
                validation_criteria={
                    "must_handle_large_numbers": True,
                    "must_calculate_correctly": True,
                    "must_not_overflow": True,
                    "must_format_result_readably": True
                },
                complexity_rating=7
            ),
            EdgeCaseTestCase(
                id="EDGE012",
                name="Tiny Dollar Amounts",
                category="extreme_values",
                test_query="What payroll tax applies to wages of $0.01?",
                expected_behavior="Handle tiny amounts correctly, likely below threshold",
                validation_criteria={
                    "must_handle_tiny_amounts": True,
                    "must_apply_threshold_correctly": True,
                    "must_explain_no_tax": True
                },
                complexity_rating=4
            ),
            EdgeCaseTestCase(
                id="EDGE013",
                name="Zero Values",
                category="extreme_values",
                test_query="What taxes apply to a business with $0 payroll and 0 properties?",
                expected_behavior="Handle zero scenarios appropriately",
                validation_criteria={
                    "must_handle_zero_values": True,
                    "must_explain_no_obligations": True,
                    "must_not_divide_by_zero": True
                },
                complexity_rating=5
            ),

            # Temporal Edge Cases
            EdgeCaseTestCase(
                id="EDGE014",
                name="Historical Rate Query",
                category="temporal",
                test_query="What was the payroll tax rate in NSW in 2019?",
                expected_behavior="Handle historical queries appropriately, may indicate current vs historical",
                validation_criteria={
                    "must_acknowledge_historical_nature": True,
                    "should_provide_current_rate": True,
                    "must_not_provide_incorrect_historical_data": True
                },
                complexity_rating=6
            ),
            EdgeCaseTestCase(
                id="EDGE015",
                name="Future Date Query",
                category="temporal",
                test_query="What will the land tax rates be in 2030?",
                expected_behavior="Handle future queries, explain limitations",
                validation_criteria={
                    "must_acknowledge_future_limitation": True,
                    "should_provide_current_rates": True,
                    "must_not_speculate": True
                },
                complexity_rating=5
            ),

            # Ambiguous Scenarios
            EdgeCaseTestCase(
                id="EDGE016",
                name="Ambiguous Property Type",
                category="ambiguous",
                test_query="What tax applies to my building?",
                expected_behavior="Request clarification or address multiple possibilities",
                validation_criteria={
                    "must_acknowledge_ambiguity": True,
                    "should_request_clarification": True,
                    "may_address_multiple_scenarios": True
                },
                complexity_rating=6
            ),
            EdgeCaseTestCase(
                id="EDGE017",
                name="Ambiguous Business Structure",
                category="ambiguous",
                test_query="We have employees in multiple states, what payroll tax applies?",
                expected_behavior="Focus on NSW obligations, acknowledge multi-state complexity",
                validation_criteria={
                    "must_focus_on_nsw": True,
                    "should_acknowledge_multi_state": True,
                    "may_suggest_professional_advice": True
                },
                complexity_rating=7
            ),

            # Calculation Edge Cases
            EdgeCaseTestCase(
                id="EDGE018",
                name="Rounding Edge Case",
                category="calculation",
                test_query="Calculate payroll tax for wages of $2,567,891.47",
                expected_behavior="Handle decimal precision correctly in calculations",
                validation_criteria={
                    "must_handle_decimals": True,
                    "must_round_appropriately": True,
                    "calculation_must_be_precise": True
                },
                complexity_rating=6
            ),
            EdgeCaseTestCase(
                id="EDGE019",
                name="Complex Percentage Calculations",
                category="calculation",
                test_query="If I own 33.33% of 3 properties worth $1.2M, $2.8M, and $945K respectively, what's my land tax obligation?",
                expected_behavior="Handle fractional ownership calculations correctly",
                validation_criteria={
                    "must_calculate_fractional_ownership": True,
                    "must_aggregate_correctly": True,
                    "must_apply_tax_rules_correctly": True
                },
                complexity_rating=8
            ),

            # Stress Tests
            EdgeCaseTestCase(
                id="EDGE020",
                name="Rapid Fire Questions",
                category="stress",
                test_query="What's payroll tax rate? Land tax threshold? Stamp duty rate? Parking levy? Foreign duty?",
                expected_behavior="Handle multiple questions in one query",
                validation_criteria={
                    "must_address_multiple_questions": True,
                    "must_organize_response_clearly": True,
                    "must_not_confuse_answers": True
                },
                complexity_rating=7,
                stress_test=True
            ),

            # Integration Edge Cases
            EdgeCaseTestCase(
                id="EDGE021",
                name="Cross-Reference Complex Scenario",
                category="integration",
                test_query="A company restructures from proprietary limited to trust structure while purchasing additional properties and expanding operations. What are the NSW revenue implications during and after the transition?",
                expected_behavior="Handle complex structural changes and their tax implications",
                validation_criteria={
                    "must_address_structural_changes": True,
                    "must_consider_transition_implications": True,
                    "must_address_ongoing_obligations": True,
                    "may_suggest_professional_advice": True
                },
                complexity_rating=9
            ),

            # Error Recovery Tests
            EdgeCaseTestCase(
                id="EDGE022",
                name="Self-Contradictory Query",
                category="error_recovery",
                test_query="I need to pay zero payroll tax on my $5 million payroll because I have no employees",
                expected_behavior="Identify contradiction and provide clarifying response",
                validation_criteria={
                    "must_identify_contradiction": True,
                    "must_provide_correct_information": True,
                    "must_be_diplomatic": True
                },
                complexity_rating=7
            ),
            EdgeCaseTestCase(
                id="EDGE023",
                name="Nonsensical Query",
                category="error_recovery",
                test_query="How much quantum payroll tax do I owe on my purple elephant property in the digital metaverse?",
                expected_behavior="Handle nonsensical query gracefully without hallucination",
                validation_criteria={
                    "must_not_hallucinate": True,
                    "must_indicate_cannot_answer": True,
                    "may_offer_help_with_real_questions": True
                },
                complexity_rating=8,
                should_fail_gracefully=True
            )
        ]

        self.edge_case_test_cases = edge_cases

    async def run_comprehensive_edge_case_testing(self) -> Dict[str, Any]:
        """
        Run comprehensive edge case and complex scenario testing
        """
        logger.info("🌪️ Starting Comprehensive Edge Case Testing Suite")

        results = {
            'suite_name': 'Comprehensive Edge Case Testing',
            'start_time': datetime.now(),
            'category_results': {},
            'stress_test_results': {},
            'robustness_assessment': {},
            'edge_case_coverage': {},
            'recommendations': []
        }

        # Group tests by category
        categorized_tests = {}
        for test_case in self.edge_case_test_cases:
            category = test_case.category
            if category not in categorized_tests:
                categorized_tests[category] = []
            categorized_tests[category].append(test_case)

        # Run tests by category
        for category, test_cases in categorized_tests.items():
            logger.info(f"🔍 Running {category.upper()} edge case tests...")
            category_results = await self._run_category_tests(category, test_cases)
            results['category_results'][category] = category_results

        # Run stress tests
        stress_tests = [tc for tc in self.edge_case_test_cases if tc.stress_test]
        if stress_tests:
            logger.info("💥 Running stress tests...")
            stress_results = await self._run_stress_tests(stress_tests)
            results['stress_test_results'] = stress_results

        # Assess overall robustness
        results['robustness_assessment'] = self._assess_system_robustness()

        # Calculate edge case coverage
        results['edge_case_coverage'] = self._calculate_edge_case_coverage()

        # Generate recommendations
        results['recommendations'] = self._generate_edge_case_recommendations()

        results['end_time'] = datetime.now()
        results['total_duration'] = (results['end_time'] - results['start_time']).total_seconds()

        # Generate detailed report
        self._generate_edge_case_report(results)

        return results

    async def _run_category_tests(self, category: str, test_cases: List[EdgeCaseTestCase]) -> Dict[str, Any]:
        """Run tests for a specific category"""
        category_results = {
            'category': category,
            'total_tests': len(test_cases),
            'test_results': [],
            'category_score': 0.0,
            'critical_issues': []
        }

        for test_case in test_cases:
            logger.info(f"Testing {test_case.name}...")

            try:
                result = await self._execute_edge_case_test(test_case)
                category_results['test_results'].append(result)
                self.test_results.append(result)

            except Exception as e:
                logger.error(f"Edge case test {test_case.id} failed: {e}")
                error_result = self._create_error_edge_case_result(test_case, str(e))
                category_results['test_results'].append(error_result)

        # Calculate category score
        if category_results['test_results']:
            scores = [r.robustness_score for r in category_results['test_results']]
            category_results['category_score'] = sum(scores) / len(scores)

        # Identify critical issues
        critical_issues = []
        for result in category_results['test_results']:
            if not result.passed and result.edge_case_coverage_score < 0.5:
                critical_issues.append(f"{result.test_case_id}: {', '.join(result.issues_found)}")

        category_results['critical_issues'] = critical_issues

        return category_results

    async def _execute_edge_case_test(self, test_case: EdgeCaseTestCase) -> EdgeCaseResult:
        """Execute a single edge case test"""
        start_time = time.time()

        try:
            # Make API request
            response = await self._make_edge_case_api_request(test_case.test_query)

            if response and response.status_code == 200:
                data = response.json()
                response_time = time.time() - start_time

                # Analyze edge case handling
                analysis = self._analyze_edge_case_response(test_case, data, response_time)

                return EdgeCaseResult(
                    test_case_id=test_case.id,
                    category=test_case.category,
                    passed=analysis['passed'],
                    actual_behavior=analysis['actual_behavior'],
                    response_time=response_time,
                    error_handling_score=analysis['error_handling_score'],
                    robustness_score=analysis['robustness_score'],
                    edge_case_coverage_score=analysis['edge_case_coverage_score'],
                    detailed_analysis=analysis['detailed_analysis'],
                    issues_found=analysis['issues_found'],
                    recommendations=analysis['recommendations'],
                    timestamp=datetime.now()
                )

            else:
                # Handle API failure
                error_code = response.status_code if response else "no_response"
                return self._create_api_failure_result(test_case, error_code, time.time() - start_time)

        except Exception as e:
            return self._create_error_edge_case_result(test_case, str(e))

    async def _make_edge_case_api_request(self, query: str) -> Optional[requests.Response]:
        """Make API request for edge case testing"""
        try:
            response = requests.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": query,
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=60  # Longer timeout for complex edge cases
            )
            return response

        except requests.exceptions.Timeout:
            logger.warning(f"API request timed out for query: {query[:100]}...")
            return None
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None

    def _analyze_edge_case_response(self, test_case: EdgeCaseTestCase, response_data: Dict, response_time: float) -> Dict[str, Any]:
        """Analyze how well the system handled the edge case"""
        analysis = {
            'passed': True,
            'actual_behavior': '',
            'error_handling_score': 1.0,
            'robustness_score': 1.0,
            'edge_case_coverage_score': 1.0,
            'detailed_analysis': {},
            'issues_found': [],
            'recommendations': []
        }

        answer = response_data.get('answer', '')
        confidence = response_data.get('confidence', 0.0)
        classification = response_data.get('classification', {})

        analysis['actual_behavior'] = answer[:200] + "..." if len(answer) > 200 else answer

        # Analyze based on test case category
        if test_case.category == 'boundary':
            analysis.update(self._analyze_boundary_case(test_case, response_data))
        elif test_case.category == 'multi_tax':
            analysis.update(self._analyze_multi_tax_case(test_case, response_data))
        elif test_case.category == 'invalid_input':
            analysis.update(self._analyze_invalid_input_case(test_case, response_data))
        elif test_case.category == 'extreme_values':
            analysis.update(self._analyze_extreme_values_case(test_case, response_data))
        elif test_case.category == 'temporal':
            analysis.update(self._analyze_temporal_case(test_case, response_data))
        elif test_case.category == 'ambiguous':
            analysis.update(self._analyze_ambiguous_case(test_case, response_data))
        elif test_case.category == 'calculation':
            analysis.update(self._analyze_calculation_case(test_case, response_data))
        elif test_case.category == 'error_recovery':
            analysis.update(self._analyze_error_recovery_case(test_case, response_data))

        # General robustness checks
        if response_time > 30:
            analysis['issues_found'].append("Response time excessive for edge case")
            analysis['robustness_score'] *= 0.8

        if confidence < 0.3 and not test_case.should_fail_gracefully:
            analysis['issues_found'].append("Very low confidence on answerable query")
            analysis['robustness_score'] *= 0.9

        # Check validation criteria
        for criterion, expected in test_case.validation_criteria.items():
            if not self._validate_criterion(criterion, expected, answer, response_data):
                analysis['issues_found'].append(f"Failed validation: {criterion}")
                analysis['passed'] = False
                analysis['edge_case_coverage_score'] *= 0.7

        return analysis

    def _analyze_boundary_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze boundary condition handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check if system handles exact threshold correctly
        if 'threshold' in test_case.test_query.lower():
            if 'threshold' not in answer.lower():
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Didn't acknowledge threshold in boundary case")
                analysis['robustness_score'] = 0.7

        # Check for precise calculations at boundaries
        if '$1,200,000' in test_case.test_query:
            # Should mention no tax or minimal tax
            if 'no tax' not in answer.lower() and '$0' not in answer:
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Boundary calculation may be incorrect")

        return analysis

    def _analyze_multi_tax_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze complex multi-tax scenario handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Count tax types mentioned
        tax_keywords = ['payroll', 'land tax', 'parking', 'stamp duty', 'royalties', 'gaming']
        mentioned_taxes = sum(1 for keyword in tax_keywords if keyword in answer.lower())

        if mentioned_taxes < 3:  # Complex scenarios should mention multiple taxes
            analysis['issues_found'] = analysis.get('issues_found', [])
            analysis['issues_found'].append("Complex multi-tax scenario not comprehensively addressed")
            analysis['edge_case_coverage_score'] = 0.6

        # Check for structured response
        if 'total' not in answer.lower() and '$' not in answer:
            analysis['issues_found'] = analysis.get('issues_found', [])
            analysis['issues_found'].append("No total calculation provided for multi-tax scenario")

        return analysis

    def _analyze_invalid_input_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze invalid input handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check for graceful error handling
        if test_case.should_fail_gracefully:
            error_indicators = ['sorry', 'unable', 'cannot', 'unclear', 'help clarify']
            if not any(indicator in answer.lower() for indicator in error_indicators):
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Didn't handle invalid input gracefully")
                analysis['error_handling_score'] = 0.5

        # Check for hallucination prevention
        if test_case.id == "EDGE023":  # Nonsensical query
            if any(word in answer.lower() for word in ['quantum', 'purple', 'elephant', 'metaverse']):
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("System may be hallucinating responses to nonsensical input")
                analysis['error_handling_score'] = 0.3

        return analysis

    def _analyze_extreme_values_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze extreme value handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check for number formatting
        if 'trillion' in test_case.test_query or len([c for c in test_case.test_query if c.isdigit()]) > 10:
            # Should handle large numbers gracefully
            if 'error' in answer.lower() or len(answer) < 50:
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Difficulty handling extreme values")
                analysis['robustness_score'] = 0.6

        return analysis

    def _analyze_temporal_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze temporal query handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check for temporal awareness
        if 'historical' in test_case.expected_behavior:
            if 'current' not in answer.lower():
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Didn't provide current information for historical query")

        if 'future' in test_case.expected_behavior:
            if 'cannot predict' not in answer.lower() and 'current' not in answer.lower():
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Didn't handle future query appropriately")

        return analysis

    def _analyze_ambiguous_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze ambiguous query handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check for ambiguity acknowledgment
        ambiguity_indicators = ['clarify', 'more information', 'depends', 'specific', 'unclear']
        if not any(indicator in answer.lower() for indicator in ambiguity_indicators):
            analysis['issues_found'] = analysis.get('issues_found', [])
            analysis['issues_found'].append("Didn't acknowledge ambiguity in query")
            analysis['edge_case_coverage_score'] = 0.7

        return analysis

    def _analyze_calculation_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze calculation precision in edge cases"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check for decimal handling
        if '.' in test_case.test_query and any(c.isdigit() for c in test_case.test_query.split('.')[-1]):
            # Should handle decimals appropriately
            if '$' not in answer:
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Calculation with decimals may not be handled correctly")

        return analysis

    def _analyze_error_recovery_case(self, test_case: EdgeCaseTestCase, response_data: Dict) -> Dict[str, Any]:
        """Analyze error recovery and contradiction handling"""
        analysis = {}
        answer = response_data.get('answer', '')

        # Check for contradiction identification
        if 'contradiction' in test_case.expected_behavior:
            contradiction_indicators = ['however', 'but', 'actually', 'incorrect', 'contradiction']
            if not any(indicator in answer.lower() for indicator in contradiction_indicators):
                analysis['issues_found'] = analysis.get('issues_found', [])
                analysis['issues_found'].append("Didn't identify contradiction in query")
                analysis['error_handling_score'] = 0.6

        return analysis

    def _validate_criterion(self, criterion: str, expected: Any, answer: str, response_data: Dict) -> bool:
        """Validate specific test criteria"""
        answer_lower = answer.lower()

        validation_map = {
            'must_not_crash': lambda: len(answer) > 0,
            'must_handle_exact_threshold': lambda: 'threshold' in answer_lower,
            'must_calculate_correctly': lambda: '$' in answer and any(c.isdigit() for c in answer),
            'must_explain_threshold_rule': lambda: 'threshold' in answer_lower,
            'must_identify_all_tax_types': lambda: sum(1 for tax in ['payroll', 'land', 'parking'] if tax in answer_lower) >= 2,
            'must_provide_breakdown': lambda: answer.count('$') >= 2,
            'must_handle_large_numbers': lambda: any(c.isdigit() for c in answer),
            'must_not_hallucinate': lambda: len([word for word in ['quantum', 'purple', 'elephant'] if word in answer_lower]) == 0,
            'must_acknowledge_ambiguity': lambda: any(word in answer_lower for word in ['clarify', 'specific', 'depends']),
            'must_not_timeout': lambda: True,  # If we got here, it didn't timeout
            'response_time_reasonable': lambda: True,  # Handled in caller
        }

        validator = validation_map.get(criterion)
        if validator:
            return validator()

        # Default validation for unknown criteria
        return True

    async def _run_stress_tests(self, stress_tests: List[EdgeCaseTestCase]) -> Dict[str, Any]:
        """Run stress tests with rapid requests"""
        stress_results = {
            'stress_test_count': len(stress_tests),
            'rapid_fire_results': [],
            'system_stability': 'unknown'
        }

        # Test rapid fire requests
        for stress_test in stress_tests:
            rapid_results = await self._test_rapid_fire_requests(stress_test)
            stress_results['rapid_fire_results'].append(rapid_results)

        # Assess system stability
        all_passed = all(r['passed'] for r in stress_results['rapid_fire_results'])
        stress_results['system_stability'] = 'stable' if all_passed else 'unstable'

        return stress_results

    async def _test_rapid_fire_requests(self, stress_test: EdgeCaseTestCase) -> Dict[str, Any]:
        """Test rapid fire requests for stress testing"""
        rapid_results = {
            'test_id': stress_test.id,
            'rapid_requests': 5,
            'successful_requests': 0,
            'failed_requests': 0,
            'average_response_time': 0.0,
            'passed': True
        }

        response_times = []

        # Make multiple rapid requests
        for i in range(5):
            start_time = time.time()
            try:
                response = await self._make_edge_case_api_request(stress_test.test_query)
                response_time = time.time() - start_time
                response_times.append(response_time)

                if response and response.status_code == 200:
                    rapid_results['successful_requests'] += 1
                else:
                    rapid_results['failed_requests'] += 1

            except Exception as e:
                rapid_results['failed_requests'] += 1
                logger.warning(f"Rapid fire request {i+1} failed: {e}")

            # Small delay between requests
            await asyncio.sleep(0.1)

        if response_times:
            rapid_results['average_response_time'] = sum(response_times) / len(response_times)

        rapid_results['passed'] = rapid_results['successful_requests'] >= 3  # At least 60% success

        return rapid_results

    def _assess_system_robustness(self) -> Dict[str, Any]:
        """Assess overall system robustness based on edge case results"""
        if not self.test_results:
            return {'status': 'unknown', 'details': 'No test results available'}

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)

        # Calculate category-specific robustness
        category_robustness = {}
        for result in self.test_results:
            category = result.category
            if category not in category_robustness:
                category_robustness[category] = {'scores': [], 'passed': 0, 'total': 0}

            category_robustness[category]['scores'].append(result.robustness_score)
            category_robustness[category]['total'] += 1
            if result.passed:
                category_robustness[category]['passed'] += 1

        # Calculate average scores per category
        for category, data in category_robustness.items():
            data['average_score'] = sum(data['scores']) / len(data['scores'])
            data['pass_rate'] = data['passed'] / data['total']

        overall_robustness = {
            'overall_pass_rate': passed_tests / total_tests,
            'overall_robustness_score': sum(r.robustness_score for r in self.test_results) / total_tests,
            'category_robustness': category_robustness,
            'critical_failure_count': sum(1 for r in self.test_results if not r.passed and r.robustness_score < 0.5),
            'system_stability': 'robust' if passed_tests / total_tests >= 0.8 else 'needs_improvement'
        }

        return overall_robustness

    def _calculate_edge_case_coverage(self) -> Dict[str, Any]:
        """Calculate edge case coverage metrics"""
        edge_case_categories = [
            'boundary', 'multi_tax', 'invalid_input', 'extreme_values',
            'temporal', 'ambiguous', 'calculation', 'error_recovery'
        ]

        coverage = {
            'total_categories': len(edge_case_categories),
            'categories_tested': 0,
            'category_coverage': {},
            'overall_coverage_score': 0.0
        }

        # Check coverage per category
        tested_categories = set(r.category for r in self.test_results)
        coverage['categories_tested'] = len(tested_categories)

        for category in edge_case_categories:
            category_results = [r for r in self.test_results if r.category == category]
            if category_results:
                avg_score = sum(r.edge_case_coverage_score for r in category_results) / len(category_results)
                coverage['category_coverage'][category] = {
                    'tests_run': len(category_results),
                    'average_coverage_score': avg_score,
                    'covered': True
                }
            else:
                coverage['category_coverage'][category] = {
                    'tests_run': 0,
                    'average_coverage_score': 0.0,
                    'covered': False
                }

        # Calculate overall coverage score
        if self.test_results:
            coverage['overall_coverage_score'] = sum(r.edge_case_coverage_score for r in self.test_results) / len(self.test_results)

        return coverage

    def _generate_edge_case_recommendations(self) -> List[str]:
        """Generate recommendations based on edge case testing results"""
        recommendations = []

        # Analyze common failure patterns
        failed_tests = [r for r in self.test_results if not r.passed]

        # Category-specific recommendations
        boundary_failures = [r for r in failed_tests if r.category == 'boundary']
        if boundary_failures:
            recommendations.append("Improve boundary condition handling, especially threshold calculations")

        multi_tax_failures = [r for r in failed_tests if r.category == 'multi_tax']
        if multi_tax_failures:
            recommendations.append("Enhance multi-tax scenario processing and comprehensive calculation abilities")

        invalid_input_failures = [r for r in failed_tests if r.category == 'invalid_input']
        if invalid_input_failures:
            recommendations.append("Strengthen input validation and graceful error handling")

        extreme_value_failures = [r for r in failed_tests if r.category == 'extreme_values']
        if extreme_value_failures:
            recommendations.append("Improve handling of extreme numerical values and edge case calculations")

        # Performance recommendations
        slow_tests = [r for r in self.test_results if r.response_time > 30]
        if slow_tests:
            recommendations.append("Optimize performance for complex edge case scenarios")

        # Error handling recommendations
        low_error_scores = [r for r in self.test_results if r.error_handling_score < 0.7]
        if low_error_scores:
            recommendations.append("Enhance error handling and recovery mechanisms")

        return recommendations

    def _create_error_edge_case_result(self, test_case: EdgeCaseTestCase, error_message: str) -> EdgeCaseResult:
        """Create error result for failed edge case test"""
        return EdgeCaseResult(
            test_case_id=test_case.id,
            category=test_case.category,
            passed=False,
            actual_behavior=f"Test execution failed: {error_message}",
            response_time=0.0,
            error_handling_score=0.0,
            robustness_score=0.0,
            edge_case_coverage_score=0.0,
            detailed_analysis={'error': error_message},
            issues_found=[f"Test execution error: {error_message}"],
            recommendations=["Fix test execution issues"],
            timestamp=datetime.now()
        )

    def _create_api_failure_result(self, test_case: EdgeCaseTestCase, error_code: str, response_time: float) -> EdgeCaseResult:
        """Create result for API failure"""
        return EdgeCaseResult(
            test_case_id=test_case.id,
            category=test_case.category,
            passed=False,
            actual_behavior=f"API failure: {error_code}",
            response_time=response_time,
            error_handling_score=0.0,
            robustness_score=0.0,
            edge_case_coverage_score=0.0,
            detailed_analysis={'api_error': error_code},
            issues_found=[f"API returned error: {error_code}"],
            recommendations=["Investigate API reliability issues"],
            timestamp=datetime.now()
        )

    def _generate_edge_case_report(self, results: Dict[str, Any]):
        """Generate detailed edge case testing report"""
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_path = reports_dir / f"edge_case_test_report_{timestamp}.json"

        # Make results JSON serializable
        serializable_results = self._make_serializable(results)

        with open(report_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)

        logger.info(f"Edge case test report generated: {report_path}")

    def _make_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, EdgeCaseResult):
            return asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj


async def main():
    """
    Run the edge case testing suite
    """
    edge_case_suite = EdgeCaseTestSuite()

    print("🌪️ NSW Revenue AI Edge Case Testing Suite")
    print("="*60)

    # Run comprehensive edge case testing
    results = await edge_case_suite.run_comprehensive_edge_case_testing()

    # Print summary
    robustness = results['robustness_assessment']
    coverage = results['edge_case_coverage']

    print(f"\n📊 EDGE CASE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Overall Pass Rate: {robustness.get('overall_pass_rate', 0)*100:.1f}%")
    print(f"Robustness Score: {robustness.get('overall_robustness_score', 0)*100:.1f}%")
    print(f"Edge Case Coverage: {coverage.get('overall_coverage_score', 0)*100:.1f}%")
    print(f"Categories Tested: {coverage.get('categories_tested', 0)}/{coverage.get('total_categories', 0)}")
    print(f"System Stability: {robustness.get('system_stability', 'unknown').upper()}")

    # Print category results
    print(f"\n📋 CATEGORY RESULTS:")
    for category, data in robustness.get('category_robustness', {}).items():
        pass_rate = data.get('pass_rate', 0)
        status = '✅' if pass_rate >= 0.8 else '⚠️' if pass_rate >= 0.6 else '❌'
        print(f"  {status} {category.title()}: {pass_rate*100:.1f}% pass rate")

    # Print recommendations
    recommendations = results.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")

    # Determine production readiness
    production_ready = (
        robustness.get('overall_pass_rate', 0) >= 0.85 and
        robustness.get('overall_robustness_score', 0) >= 0.8 and
        robustness.get('critical_failure_count', 0) == 0
    )

    if production_ready:
        print(f"\n✅ EDGE CASE RESILIENT: System handles edge cases well!")
        return 0
    else:
        print(f"\n❌ NEEDS IMPROVEMENT: Edge case handling requires attention")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))