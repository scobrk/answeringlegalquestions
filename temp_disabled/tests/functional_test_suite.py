#!/usr/bin/env python3
"""
Functional Test Suite for NSW Revenue AI System
Tests all 67 revenue types for correct functionality and responses
"""

import os
import sys
import asyncio
import json
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
import logging
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_framework_architecture import TestFramework, TestCase, TestResult, RevenueCategory

logger = logging.getLogger(__name__)


class FunctionalTestSuite:
    """
    Comprehensive functional testing suite for NSW Revenue AI system
    Validates that all 67 revenue types respond correctly
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.test_cases = []
        self.revenue_coverage_map = {}
        self.critical_test_cases = []
        self.load_test_cases()

    def load_test_cases(self):
        """Load test cases and organize by revenue type"""
        test_data_path = Path(__file__).parent / "test_data" / "comprehensive_revenue_test_cases.json"

        if test_data_path.exists():
            with open(test_data_path, 'r') as f:
                data = json.load(f)
                for case_data in data.get('test_cases', []):
                    if case_data.get('test_type') == 'functional':
                        test_case = TestCase(**case_data)
                        self.test_cases.append(test_case)

                        # Map to revenue coverage
                        revenue_type = case_data.get('revenue_type')
                        if revenue_type not in self.revenue_coverage_map:
                            self.revenue_coverage_map[revenue_type] = []
                        self.revenue_coverage_map[revenue_type].append(test_case)

                        # Track critical tests
                        if case_data.get('priority') == 'critical':
                            self.critical_test_cases.append(test_case)

        logger.info(f"Loaded {len(self.test_cases)} functional test cases covering {len(self.revenue_coverage_map)} revenue types")

    async def run_complete_functional_test_suite(self) -> Dict[str, any]:
        """
        Run the complete functional test suite with comprehensive validation
        """
        logger.info("🚀 Starting Complete Functional Test Suite")
        start_time = datetime.now()

        results = {
            'suite_name': 'Complete Functional Test Suite',
            'start_time': start_time,
            'test_results': [],
            'coverage_analysis': {},
            'critical_test_results': [],
            'performance_summary': {},
            'recommendations': []
        }

        # 1. Run Revenue Type Coverage Tests
        logger.info("📋 Testing Revenue Type Coverage...")
        coverage_results = await self.test_revenue_type_coverage()
        results['coverage_analysis'] = coverage_results

        # 2. Run Critical Test Cases First
        logger.info("🔥 Running Critical Test Cases...")
        critical_results = await self.run_critical_tests()
        results['critical_test_results'] = critical_results

        # 3. Run All Functional Tests
        logger.info("📊 Running All Functional Tests...")
        all_results = await self.run_all_functional_tests()
        results['test_results'] = all_results

        # 4. Analyze Results and Generate Recommendations
        logger.info("📈 Analyzing Results...")
        performance_summary = self.analyze_performance(all_results)
        results['performance_summary'] = performance_summary

        recommendations = self.generate_recommendations(coverage_results, critical_results, all_results)
        results['recommendations'] = recommendations

        # 5. Generate Detailed Report
        results['end_time'] = datetime.now()
        results['total_duration'] = (results['end_time'] - start_time).total_seconds()

        self.generate_functional_test_report(results)

        return results

    async def test_revenue_type_coverage(self) -> Dict[str, any]:
        """
        Test coverage of all 67 revenue types
        """
        logger.info("Testing coverage of all NSW revenue types...")

        # Get all revenue types we should cover
        all_revenue_types = {member.value for member in RevenueCategory}
        covered_types = set(self.revenue_coverage_map.keys())

        missing_types = all_revenue_types - covered_types
        coverage_percentage = len(covered_types) / len(all_revenue_types) * 100

        # Test each covered revenue type
        coverage_test_results = []
        for revenue_type, test_cases in self.revenue_coverage_map.items():
            # Run one representative test for each revenue type
            representative_test = test_cases[0]  # Use first test case as representative
            result = await self.execute_single_test(representative_test)
            coverage_test_results.append({
                'revenue_type': revenue_type,
                'test_case_id': representative_test.id,
                'passed': result.passed,
                'confidence': result.actual_confidence,
                'response_time': result.actual_response_time
            })

        coverage_analysis = {
            'total_revenue_types': len(all_revenue_types),
            'covered_types': len(covered_types),
            'missing_types': list(missing_types),
            'coverage_percentage': coverage_percentage,
            'coverage_test_results': coverage_test_results,
            'passed_coverage_tests': sum(1 for r in coverage_test_results if r['passed']),
            'failed_coverage_tests': sum(1 for r in coverage_test_results if not r['passed'])
        }

        logger.info(f"Revenue Type Coverage: {coverage_percentage:.1f}% ({len(covered_types)}/{len(all_revenue_types)})")
        if missing_types:
            logger.warning(f"Missing coverage for: {missing_types}")

        return coverage_analysis

    async def run_critical_tests(self) -> List[TestResult]:
        """
        Run all critical priority test cases first
        """
        logger.info(f"Running {len(self.critical_test_cases)} critical test cases...")

        critical_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit critical tests
            future_to_test = {
                executor.submit(asyncio.run, self.execute_single_test(tc)): tc
                for tc in self.critical_test_cases
            }

            # Collect results
            for future in as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result(timeout=30)
                    critical_results.append(result)
                except Exception as e:
                    logger.error(f"Critical test {test_case.id} failed: {e}")
                    critical_results.append(self.create_error_result(test_case, str(e)))

        passed_critical = sum(1 for r in critical_results if r.passed)
        logger.info(f"Critical Tests: {passed_critical}/{len(critical_results)} passed")

        return critical_results

    async def run_all_functional_tests(self) -> List[TestResult]:
        """
        Run all functional test cases
        """
        logger.info(f"Running {len(self.test_cases)} functional test cases...")

        all_results = []
        batch_size = 10

        # Process tests in batches to avoid overwhelming the system
        for i in range(0, len(self.test_cases), batch_size):
            batch = self.test_cases[i:i + batch_size]
            batch_results = await self.run_test_batch(batch, f"Batch {i//batch_size + 1}")
            all_results.extend(batch_results)

            # Brief pause between batches
            await asyncio.sleep(1)

        return all_results

    async def run_test_batch(self, test_cases: List[TestCase], batch_name: str) -> List[TestResult]:
        """
        Run a batch of test cases concurrently
        """
        logger.info(f"Running {batch_name} with {len(test_cases)} tests...")

        results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submit tests
            future_to_test = {
                executor.submit(asyncio.run, self.execute_single_test(tc)): tc
                for tc in test_cases
            }

            # Collect results
            for future in as_completed(future_to_test):
                test_case = future_to_test[future]
                try:
                    result = future.result(timeout=30)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Test {test_case.id} failed: {e}")
                    results.append(self.create_error_result(test_case, str(e)))

        passed = sum(1 for r in results if r.passed)
        logger.info(f"{batch_name}: {passed}/{len(results)} passed")

        return results

    async def execute_single_test(self, test_case: TestCase) -> TestResult:
        """
        Execute a single functional test case
        """
        start_time = time.time()

        try:
            # Make API request
            response = await self.make_async_api_request(test_case.question)

            if response.status_code == 200:
                data = response.json()
                response_time = time.time() - start_time

                # Validate the response
                result = self.validate_functional_response(test_case, data, response_time)
                return result

            else:
                return TestResult(
                    test_case_id=test_case.id,
                    passed=False,
                    actual_response=f"API Error: {response.status_code}",
                    actual_confidence=0.0,
                    actual_response_time=time.time() - start_time,
                    detected_revenue_types=[],
                    accuracy_score=0.0,
                    errors=[f"HTTP {response.status_code}: {response.text}"],
                    warnings=[],
                    timestamp=datetime.now()
                )

        except Exception as e:
            return self.create_error_result(test_case, str(e))

    async def make_async_api_request(self, question: str) -> requests.Response:
        """
        Make async API request to the NSW Revenue AI system
        """
        # For now, using synchronous requests (would convert to async in production)
        url = f"{self.api_base_url}/api/query"

        payload = {
            "question": question,
            "enable_approval": True,
            "include_metadata": True
        }

        return requests.post(url, json=payload, timeout=30)

    def validate_functional_response(self, test_case: TestCase, response_data: Dict, response_time: float) -> TestResult:
        """
        Validate functional test response with comprehensive checks
        """
        passed = True
        errors = []
        warnings = []

        # Extract response components
        answer = response_data.get('answer', '')
        confidence = response_data.get('confidence', 0.0)
        classification = response_data.get('classification', {})
        detected_revenue_type = classification.get('revenue_type', '')
        source_count = response_data.get('source_count', 0)

        # 1. Response Time Check
        if response_time > test_case.expected_response_time_max:
            passed = False
            errors.append(f"Response time {response_time:.2f}s exceeds maximum {test_case.expected_response_time_max}s")

        # 2. Confidence Check
        if confidence < test_case.expected_confidence_min:
            passed = False
            errors.append(f"Confidence {confidence:.2f} below minimum {test_case.expected_confidence_min}")

        # 3. Revenue Type Detection Check
        if test_case.expected_revenue_types:
            if detected_revenue_type not in test_case.expected_revenue_types:
                passed = False
                errors.append(f"Detected revenue type '{detected_revenue_type}' not in expected {test_case.expected_revenue_types}")

        # 4. Content Quality Checks
        content_errors = self.validate_content_quality(test_case, answer)
        errors.extend(content_errors)
        if content_errors:
            passed = False

        # 5. Functional Requirements Check
        functional_errors = self.validate_functional_requirements(test_case, response_data)
        errors.extend(functional_errors)
        if functional_errors:
            passed = False

        # 6. Source Validation
        if source_count == 0:
            warnings.append("No sources provided with response")

        # Calculate functional accuracy score
        accuracy_score = self.calculate_functional_accuracy(test_case, response_data, errors, warnings)

        return TestResult(
            test_case_id=test_case.id,
            passed=passed,
            actual_response=answer,
            actual_confidence=confidence,
            actual_response_time=response_time,
            detected_revenue_types=[detected_revenue_type],
            accuracy_score=accuracy_score,
            errors=errors,
            warnings=warnings,
            timestamp=datetime.now(),
            additional_metrics={
                'classification': classification,
                'source_count': source_count,
                'content_length': len(answer),
                'has_calculations': '$' in answer or any(char.isdigit() for char in answer)
            }
        )

    def validate_content_quality(self, test_case: TestCase, answer: str) -> List[str]:
        """
        Validate the quality and completeness of the response content
        """
        errors = []

        # Check for minimum content length
        if len(answer.strip()) < 50:
            errors.append("Response too brief (less than 50 characters)")

        # Check for obvious errors or failures
        error_indicators = [
            "error occurred", "unable to process", "cannot answer",
            "insufficient information", "system error", "failed to"
        ]

        if any(indicator in answer.lower() for indicator in error_indicators):
            errors.append("Response contains error indicators")

        # Check for specific functional requirements
        validation_criteria = test_case.validation_criteria

        if validation_criteria.get('must_contain_calculation') and not any(char.isdigit() for char in answer):
            errors.append("Expected calculation but no numbers found in response")

        if validation_criteria.get('must_provide_dollar_amount') and '$' not in answer:
            errors.append("Expected dollar amount but none found in response")

        if validation_criteria.get('must_mention_thresholds') and 'threshold' not in answer.lower():
            errors.append("Expected threshold information but not mentioned")

        if validation_criteria.get('must_mention_exemption') and 'exemption' not in answer.lower():
            errors.append("Expected exemption information but not mentioned")

        if validation_criteria.get('must_explain_ppr') and 'principal place of residence' not in answer.lower():
            errors.append("Expected PPR explanation but not found")

        return errors

    def validate_functional_requirements(self, test_case: TestCase, response_data: Dict) -> List[str]:
        """
        Validate specific functional requirements based on test case
        """
        errors = []

        # Multi-tax scenario validation
        if test_case.multi_tax_scenario:
            answer = response_data.get('answer', '')
            tax_mentions = 0

            tax_keywords = ['payroll', 'land tax', 'stamp duty', 'parking', 'levy', 'duty', 'tax']
            for keyword in tax_keywords:
                if keyword in answer.lower():
                    tax_mentions += 1

            if tax_mentions < 2:
                errors.append("Multi-tax scenario not properly addressed - insufficient tax type mentions")

        # Calculation requirement validation
        if test_case.requires_calculation:
            answer = response_data.get('answer', '')
            has_numbers = any(char.isdigit() for char in answer)
            has_currency = '$' in answer

            if not (has_numbers and has_currency):
                errors.append("Calculation required but no monetary calculations found")

        # Numerical answer validation
        if test_case.has_numerical_answer:
            answer = response_data.get('answer', '')
            if not any(char.isdigit() for char in answer):
                errors.append("Expected numerical answer but no numbers found")

        return errors

    def calculate_functional_accuracy(self, test_case: TestCase, response_data: Dict, errors: List[str], warnings: List[str]) -> float:
        """
        Calculate functional accuracy score based on multiple criteria
        """
        base_score = 1.0

        # Deduct for errors
        for error in errors:
            if "response time" in error:
                base_score -= 0.1
            elif "confidence" in error:
                base_score -= 0.15
            elif "revenue type" in error:
                base_score -= 0.2
            elif "calculation" in error or "numerical" in error:
                base_score -= 0.25
            else:
                base_score -= 0.1

        # Minor deductions for warnings
        base_score -= len(warnings) * 0.05

        # Boost for meeting expectations
        if response_data.get('confidence', 0) >= test_case.expected_confidence_min:
            base_score += 0.1

        if response_data.get('source_count', 0) > 0:
            base_score += 0.05

        return max(0.0, min(1.0, base_score))

    def create_error_result(self, test_case: TestCase, error_message: str) -> TestResult:
        """
        Create a test result for a failed test execution
        """
        return TestResult(
            test_case_id=test_case.id,
            passed=False,
            actual_response=f"Test execution failed: {error_message}",
            actual_confidence=0.0,
            actual_response_time=float('inf'),
            detected_revenue_types=[],
            accuracy_score=0.0,
            errors=[error_message],
            warnings=[],
            timestamp=datetime.now()
        )

    def analyze_performance(self, results: List[TestResult]) -> Dict[str, any]:
        """
        Analyze functional test performance
        """
        if not results:
            return {}

        total_tests = len(results)
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = total_tests - passed_tests

        response_times = [r.actual_response_time for r in results if r.actual_response_time != float('inf')]
        confidences = [r.actual_confidence for r in results]
        accuracy_scores = [r.accuracy_score for r in results]

        performance_summary = {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'average_response_time': sum(response_times) / len(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'average_confidence': sum(confidences) / len(confidences) if confidences else 0,
            'average_accuracy': sum(accuracy_scores) / len(accuracy_scores) if accuracy_scores else 0,
            'response_time_violations': sum(1 for rt in response_times if rt > 2.0),
            'low_confidence_tests': sum(1 for c in confidences if c < 0.7),
        }

        return performance_summary

    def generate_recommendations(self, coverage_analysis: Dict, critical_results: List[TestResult], all_results: List[TestResult]) -> List[str]:
        """
        Generate recommendations based on test results
        """
        recommendations = []

        # Coverage recommendations
        coverage_pct = coverage_analysis.get('coverage_percentage', 0)
        if coverage_pct < 100:
            missing_types = coverage_analysis.get('missing_types', [])
            recommendations.append(f"Add test coverage for missing revenue types: {missing_types}")

        # Critical test recommendations
        critical_passed = sum(1 for r in critical_results if r.passed)
        critical_total = len(critical_results)
        if critical_passed < critical_total:
            recommendations.append(f"Fix {critical_total - critical_passed} failing critical tests before production")

        # Performance recommendations
        slow_tests = sum(1 for r in all_results if r.actual_response_time > 2.0)
        if slow_tests > 0:
            recommendations.append(f"Optimize {slow_tests} tests with slow response times (>2s)")

        # Accuracy recommendations
        low_accuracy_tests = sum(1 for r in all_results if r.accuracy_score < 0.8)
        if low_accuracy_tests > 0:
            recommendations.append(f"Improve accuracy for {low_accuracy_tests} tests scoring below 80%")

        # Overall system recommendations
        pass_rate = sum(1 for r in all_results if r.passed) / len(all_results) if all_results else 0
        if pass_rate < 0.95:
            recommendations.append("Overall pass rate below 95% - system not ready for production")

        return recommendations

    def generate_functional_test_report(self, results: Dict) -> str:
        """
        Generate detailed functional test report
        """
        report_path = Path(__file__).parent / "reports" / f"functional_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(exist_ok=True)

        # Create serializable results
        serializable_results = results.copy()
        serializable_results['start_time'] = results['start_time'].isoformat()
        serializable_results['end_time'] = results['end_time'].isoformat()

        # Convert TestResult objects to dicts
        serializable_results['test_results'] = [
            {
                'test_case_id': r.test_case_id,
                'passed': r.passed,
                'actual_confidence': r.actual_confidence,
                'actual_response_time': r.actual_response_time,
                'accuracy_score': r.accuracy_score,
                'errors': r.errors,
                'warnings': r.warnings,
                'timestamp': r.timestamp.isoformat()
            }
            for r in results['test_results']
        ]

        serializable_results['critical_test_results'] = [
            {
                'test_case_id': r.test_case_id,
                'passed': r.passed,
                'actual_confidence': r.actual_confidence,
                'actual_response_time': r.actual_response_time,
                'accuracy_score': r.accuracy_score,
                'errors': r.errors
            }
            for r in results['critical_test_results']
        ]

        with open(report_path, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        logger.info(f"Functional test report generated: {report_path}")
        return str(report_path)


async def main():
    """
    Run the functional test suite
    """
    functional_suite = FunctionalTestSuite()

    print("🚀 NSW Revenue AI Functional Test Suite")
    print("="*50)

    # Run the complete functional test suite
    results = await functional_suite.run_complete_functional_test_suite()

    # Print summary
    performance = results['performance_summary']
    coverage = results['coverage_analysis']

    print(f"\n📊 FUNCTIONAL TEST RESULTS")
    print(f"{'='*50}")
    print(f"Total Tests: {performance.get('total_tests', 0)}")
    print(f"Passed: {performance.get('passed_tests', 0)}")
    print(f"Failed: {performance.get('failed_tests', 0)}")
    print(f"Pass Rate: {performance.get('pass_rate', 0)*100:.1f}%")
    print(f"Average Response Time: {performance.get('average_response_time', 0):.2f}s")
    print(f"Average Accuracy: {performance.get('average_accuracy', 0)*100:.1f}%")
    print(f"Revenue Type Coverage: {coverage.get('coverage_percentage', 0):.1f}%")

    # Print recommendations
    if results['recommendations']:
        print(f"\n📋 RECOMMENDATIONS:")
        for i, rec in enumerate(results['recommendations'], 1):
            print(f"{i}. {rec}")

    # Determine if production ready
    is_production_ready = (
        performance.get('pass_rate', 0) >= 0.95 and
        performance.get('average_response_time', 0) <= 2.0 and
        performance.get('average_accuracy', 0) >= 0.95 and
        coverage.get('coverage_percentage', 0) >= 100.0
    )

    if is_production_ready:
        print(f"\n✅ PRODUCTION READY: All functional criteria met!")
        return 0
    else:
        print(f"\n❌ NOT PRODUCTION READY: Functional criteria not met")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))