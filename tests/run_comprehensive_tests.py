#!/usr/bin/env python3
"""
Comprehensive Test Runner for NSW Revenue AI System
Orchestrates all test suites: functional, performance, accuracy, integration, edge cases
"""

import os
import sys
import asyncio
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import all test suites
from tests.functional_test_suite import FunctionalTestSuite
from tests.performance_test_suite import PerformanceTestSuite
from tests.accuracy_validation_suite import AccuracyValidationSuite
from tests.integration_test_suite import IntegrationTestSuite
from tests.edge_case_test_suite import EdgeCaseTestSuite

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveTestRunner:
    """
    Comprehensive test runner that orchestrates all test suites
    for complete validation of the NSW Revenue AI system
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.test_suites = {}
        self.overall_results = {}
        self.production_readiness_criteria = {
            'functional_pass_rate': 0.95,          # 95% functional tests must pass
            'performance_response_time': 2.0,       # <2s average response time
            'accuracy_score': 0.95,                 # 95% accuracy required
            'integration_pass_rate': 0.90,          # 90% integration tests must pass
            'edge_case_robustness': 0.80,           # 80% edge case robustness
            'revenue_type_coverage': 1.0             # 100% revenue type coverage
        }

    def initialize_test_suites(self):
        """Initialize all test suites"""
        logger.info("Initializing test suites...")

        self.test_suites = {
            'functional': FunctionalTestSuite(self.api_base_url),
            'performance': PerformanceTestSuite(self.api_base_url),
            'accuracy': AccuracyValidationSuite(self.api_base_url),
            'integration': IntegrationTestSuite(self.api_base_url),
            'edge_case': EdgeCaseTestSuite(self.api_base_url)
        }

        logger.info("All test suites initialized successfully")

    async def run_all_tests(self, selected_suites: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run all selected test suites comprehensively

        Args:
            selected_suites: List of suite names to run. If None, runs all suites.

        Returns:
            Comprehensive test results
        """
        logger.info("🚀 Starting Comprehensive NSW Revenue AI Test Suite")
        logger.info("="*80)

        start_time = datetime.now()

        # Initialize test suites
        self.initialize_test_suites()

        # Determine which suites to run
        suites_to_run = selected_suites or list(self.test_suites.keys())

        results = {
            'test_run_info': {
                'start_time': start_time,
                'api_base_url': self.api_base_url,
                'suites_executed': suites_to_run,
                'total_suites': len(suites_to_run)
            },
            'suite_results': {},
            'production_readiness_assessment': {},
            'summary_metrics': {},
            'recommendations': [],
            'critical_issues': []
        }

        # Run each selected test suite
        for suite_name in suites_to_run:
            if suite_name in self.test_suites:
                logger.info(f"\n{'='*60}")
                logger.info(f"RUNNING {suite_name.upper()} TEST SUITE")
                logger.info(f"{'='*60}")

                try:
                    suite_result = await self._run_test_suite(suite_name)
                    results['suite_results'][suite_name] = suite_result

                except Exception as e:
                    logger.error(f"Failed to run {suite_name} test suite: {e}")
                    results['suite_results'][suite_name] = {
                        'status': 'failed',
                        'error': str(e)
                    }

        # Calculate overall metrics and assessment
        results['summary_metrics'] = self._calculate_summary_metrics(results['suite_results'])
        results['production_readiness_assessment'] = self._assess_production_readiness(results['suite_results'])
        results['recommendations'] = self._generate_overall_recommendations(results['suite_results'])
        results['critical_issues'] = self._identify_critical_issues(results['suite_results'])

        # Finalize results
        results['test_run_info']['end_time'] = datetime.now()
        results['test_run_info']['total_duration'] = (
            results['test_run_info']['end_time'] - start_time
        ).total_seconds()

        # Generate comprehensive report
        self._generate_comprehensive_report(results)

        # Store overall results
        self.overall_results = results

        return results

    async def _run_test_suite(self, suite_name: str) -> Dict[str, Any]:
        """Run a specific test suite"""
        suite = self.test_suites[suite_name]

        try:
            if suite_name == 'functional':
                return await suite.run_complete_functional_test_suite()
            elif suite_name == 'performance':
                return await suite.run_comprehensive_performance_tests()
            elif suite_name == 'accuracy':
                return await suite.run_comprehensive_accuracy_validation()
            elif suite_name == 'integration':
                return await suite.run_comprehensive_integration_tests()
            elif suite_name == 'edge_case':
                return await suite.run_comprehensive_edge_case_testing()
            else:
                raise ValueError(f"Unknown test suite: {suite_name}")

        except Exception as e:
            logger.error(f"Error running {suite_name} test suite: {e}")
            raise

    def _calculate_summary_metrics(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall summary metrics across all test suites"""
        summary = {
            'total_tests_run': 0,
            'total_tests_passed': 0,
            'total_tests_failed': 0,
            'overall_pass_rate': 0.0,
            'suite_performance': {},
            'key_metrics': {}
        }

        # Aggregate metrics from each suite
        for suite_name, results in suite_results.items():
            if isinstance(results, dict) and 'status' not in results:
                suite_metrics = self._extract_suite_metrics(suite_name, results)
                summary['suite_performance'][suite_name] = suite_metrics

                # Add to totals
                summary['total_tests_run'] += suite_metrics.get('tests_run', 0)
                summary['total_tests_passed'] += suite_metrics.get('tests_passed', 0)
                summary['total_tests_failed'] += suite_metrics.get('tests_failed', 0)

        # Calculate overall metrics
        if summary['total_tests_run'] > 0:
            summary['overall_pass_rate'] = summary['total_tests_passed'] / summary['total_tests_run']

        # Extract key metrics for production readiness
        summary['key_metrics'] = self._extract_key_metrics(suite_results)

        return summary

    def _extract_suite_metrics(self, suite_name: str, results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract standardized metrics from each test suite"""
        metrics = {
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'pass_rate': 0.0,
            'suite_specific': {}
        }

        try:
            if suite_name == 'functional':
                perf_summary = results.get('performance_summary', {})
                metrics.update({
                    'tests_run': perf_summary.get('total_tests', 0),
                    'tests_passed': perf_summary.get('passed_tests', 0),
                    'tests_failed': perf_summary.get('failed_tests', 0),
                    'pass_rate': perf_summary.get('pass_rate', 0.0),
                    'suite_specific': {
                        'average_response_time': perf_summary.get('average_response_time', 0.0),
                        'average_accuracy': perf_summary.get('average_accuracy', 0.0),
                        'coverage_percentage': results.get('coverage_analysis', {}).get('coverage_percentage', 0.0)
                    }
                })

            elif suite_name == 'performance':
                assessment = results.get('overall_assessment', {})
                metrics.update({
                    'tests_run': 1,  # Performance is more about benchmarks
                    'tests_passed': 1 if assessment.get('production_ready', False) else 0,
                    'tests_failed': 0 if assessment.get('production_ready', False) else 1,
                    'pass_rate': 1.0 if assessment.get('production_ready', False) else 0.0,
                    'suite_specific': {
                        'meets_response_time_target': assessment.get('meets_response_time_target', False),
                        'meets_throughput_target': assessment.get('meets_throughput_target', False),
                        'meets_memory_target': assessment.get('meets_memory_target', False)
                    }
                })

            elif suite_name == 'accuracy':
                scores = results.get('overall_accuracy_scores', {})
                readiness = results.get('production_readiness', {})
                metrics.update({
                    'tests_run': scores.get('total_tests', 0),
                    'tests_passed': scores.get('passed_tests', 0),
                    'tests_failed': scores.get('total_tests', 0) - scores.get('passed_tests', 0),
                    'pass_rate': scores.get('pass_rate', 0.0),
                    'suite_specific': {
                        'overall_accuracy': scores.get('overall_accuracy', 0.0),
                        'legal_accuracy': scores.get('legal_accuracy', 0.0),
                        'calculation_accuracy': scores.get('calculation_accuracy', 0.0),
                        'production_ready': readiness.get('production_ready', False)
                    }
                })

            elif suite_name == 'integration':
                health = results.get('overall_integration_health', {})
                metrics.update({
                    'tests_run': health.get('total_tests', 0),
                    'tests_passed': health.get('passed_tests', 0),
                    'tests_failed': health.get('failed_tests', 0),
                    'pass_rate': health.get('pass_rate', 0.0),
                    'suite_specific': {
                        'overall_status': health.get('overall_status', 'unknown'),
                        'production_ready': health.get('production_ready', False),
                        'component_health': health.get('component_health', {})
                    }
                })

            elif suite_name == 'edge_case':
                robustness = results.get('robustness_assessment', {})
                coverage = results.get('edge_case_coverage', {})
                metrics.update({
                    'tests_run': len(results.get('category_results', {})),
                    'tests_passed': int(robustness.get('overall_pass_rate', 0) * len(results.get('category_results', {}))),
                    'tests_failed': len(results.get('category_results', {})) - int(robustness.get('overall_pass_rate', 0) * len(results.get('category_results', {}))),
                    'pass_rate': robustness.get('overall_pass_rate', 0.0),
                    'suite_specific': {
                        'robustness_score': robustness.get('overall_robustness_score', 0.0),
                        'system_stability': robustness.get('system_stability', 'unknown'),
                        'edge_case_coverage': coverage.get('overall_coverage_score', 0.0)
                    }
                })

        except Exception as e:
            logger.warning(f"Error extracting metrics for {suite_name}: {e}")

        return metrics

    def _extract_key_metrics(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract key metrics for production readiness assessment"""
        key_metrics = {}

        # Functional metrics
        if 'functional' in suite_results:
            functional = suite_results['functional']
            perf_summary = functional.get('performance_summary', {})
            coverage = functional.get('coverage_analysis', {})

            key_metrics.update({
                'functional_pass_rate': perf_summary.get('pass_rate', 0.0),
                'average_response_time': perf_summary.get('average_response_time', 0.0),
                'revenue_type_coverage': coverage.get('coverage_percentage', 0.0) / 100.0
            })

        # Performance metrics
        if 'performance' in suite_results:
            performance = suite_results['performance']
            baseline = performance.get('test_results', {}).get('baseline')
            if baseline:
                key_metrics['performance_response_time'] = baseline.average_response_time

        # Accuracy metrics
        if 'accuracy' in suite_results:
            accuracy = suite_results['accuracy']
            scores = accuracy.get('overall_accuracy_scores', {})
            key_metrics['accuracy_score'] = scores.get('overall_accuracy', 0.0)

        # Integration metrics
        if 'integration' in suite_results:
            integration = suite_results['integration']
            health = integration.get('overall_integration_health', {})
            key_metrics['integration_pass_rate'] = health.get('pass_rate', 0.0)

        # Edge case metrics
        if 'edge_case' in suite_results:
            edge_case = suite_results['edge_case']
            robustness = edge_case.get('robustness_assessment', {})
            key_metrics['edge_case_robustness'] = robustness.get('overall_robustness_score', 0.0)

        return key_metrics

    def _assess_production_readiness(self, suite_results: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall production readiness against criteria"""
        key_metrics = self._extract_key_metrics(suite_results)

        assessment = {
            'production_ready': True,
            'criteria_met': {},
            'criteria_failed': {},
            'overall_score': 0.0,
            'readiness_level': 'unknown'
        }

        # Check each criterion
        for criterion, threshold in self.production_readiness_criteria.items():
            actual_value = key_metrics.get(criterion, 0.0)
            meets_criterion = actual_value >= threshold

            if meets_criterion:
                assessment['criteria_met'][criterion] = {
                    'threshold': threshold,
                    'actual': actual_value,
                    'status': 'passed'
                }
            else:
                assessment['criteria_failed'][criterion] = {
                    'threshold': threshold,
                    'actual': actual_value,
                    'gap': threshold - actual_value,
                    'status': 'failed'
                }
                assessment['production_ready'] = False

        # Calculate overall score
        if self.production_readiness_criteria:
            total_score = 0
            for criterion, threshold in self.production_readiness_criteria.items():
                actual = key_metrics.get(criterion, 0.0)
                score = min(actual / threshold, 1.0) if threshold > 0 else 1.0
                total_score += score

            assessment['overall_score'] = total_score / len(self.production_readiness_criteria)

        # Determine readiness level
        if assessment['overall_score'] >= 0.95:
            assessment['readiness_level'] = 'production_ready'
        elif assessment['overall_score'] >= 0.85:
            assessment['readiness_level'] = 'nearly_ready'
        elif assessment['overall_score'] >= 0.70:
            assessment['readiness_level'] = 'needs_improvement'
        else:
            assessment['readiness_level'] = 'not_ready'

        return assessment

    def _generate_overall_recommendations(self, suite_results: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations based on all test results"""
        recommendations = []

        # Collect recommendations from individual suites
        for suite_name, results in suite_results.items():
            if isinstance(results, dict):
                suite_recommendations = results.get('recommendations', [])
                if suite_recommendations:
                    recommendations.append(f"\n{suite_name.title()} Suite Recommendations:")
                    recommendations.extend([f"  - {rec}" for rec in suite_recommendations])

        # Add system-level recommendations
        key_metrics = self._extract_key_metrics(suite_results)

        if key_metrics.get('functional_pass_rate', 0) < 0.95:
            recommendations.append("🔧 Improve core functionality - functional test pass rate below 95%")

        if key_metrics.get('average_response_time', 0) > 2.0:
            recommendations.append("⚡ Optimize performance - response times exceed 2 second target")

        if key_metrics.get('accuracy_score', 0) < 0.95:
            recommendations.append("🎯 Enhance accuracy - accuracy scores below 95% threshold")

        if key_metrics.get('revenue_type_coverage', 0) < 1.0:
            recommendations.append("📊 Complete revenue type coverage - missing test coverage for some revenue types")

        if key_metrics.get('edge_case_robustness', 0) < 0.8:
            recommendations.append("🛡️ Strengthen edge case handling - robustness below 80%")

        return recommendations

    def _identify_critical_issues(self, suite_results: Dict[str, Any]) -> List[str]:
        """Identify critical issues that must be resolved before production"""
        critical_issues = []

        # Check for critical failures in each suite
        for suite_name, results in suite_results.items():
            if isinstance(results, dict):
                # Look for critical issues indicators
                if 'critical_issues' in results:
                    suite_critical = results['critical_issues']
                    if suite_critical:
                        critical_issues.append(f"{suite_name.title()} Suite Critical Issues:")
                        critical_issues.extend([f"  ❌ {issue}" for issue in suite_critical])

                # Check for system failures
                if results.get('status') == 'failed':
                    critical_issues.append(f"❌ {suite_name.title()} test suite failed to execute")

        # System-level critical issues
        key_metrics = self._extract_key_metrics(suite_results)

        if key_metrics.get('functional_pass_rate', 0) < 0.8:
            critical_issues.append("❌ CRITICAL: Functional pass rate below 80% - system not functional")

        if key_metrics.get('accuracy_score', 0) < 0.9:
            critical_issues.append("❌ CRITICAL: Accuracy below 90% - legal compliance risk")

        if key_metrics.get('integration_pass_rate', 0) < 0.8:
            critical_issues.append("❌ CRITICAL: Integration failures - system components not working together")

        return critical_issues

    def _generate_comprehensive_report(self, results: Dict[str, Any]):
        """Generate comprehensive test report"""
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSON Report
        json_report_path = reports_dir / f"comprehensive_test_report_{timestamp}.json"
        with open(json_report_path, 'w') as f:
            json.dump(self._make_serializable(results), f, indent=2, default=str)

        # HTML Summary Report
        html_report_path = reports_dir / f"test_summary_{timestamp}.html"
        html_content = self._generate_html_summary(results)
        with open(html_report_path, 'w') as f:
            f.write(html_content)

        logger.info(f"📋 Comprehensive test reports generated:")
        logger.info(f"   JSON: {json_report_path}")
        logger.info(f"   HTML: {html_report_path}")

    def _generate_html_summary(self, results: Dict[str, Any]) -> str:
        """Generate HTML summary report"""
        summary_metrics = results.get('summary_metrics', {})
        readiness = results.get('production_readiness_assessment', {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>NSW Revenue AI - Comprehensive Test Results</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #ecf0f1; padding: 20px; margin: 20px 0; border-radius: 8px; }}
        .metric {{ display: inline-block; margin: 10px; padding: 15px; background: white; border-radius: 5px; }}
        .pass {{ color: #27ae60; }}
        .fail {{ color: #e74c3c; }}
        .warning {{ color: #f39c12; }}
        .recommendations {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        .critical {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; margin: 20px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>NSW Revenue AI - Comprehensive Test Results</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <h2>Production Readiness Assessment</h2>
        <div class="metric">
            <strong>Overall Score:</strong> {readiness.get('overall_score', 0)*100:.1f}%
        </div>
        <div class="metric">
            <strong>Readiness Level:</strong>
            <span class="{'pass' if readiness.get('production_ready', False) else 'fail'}">
                {readiness.get('readiness_level', 'unknown').replace('_', ' ').title()}
            </span>
        </div>
        <div class="metric">
            <strong>Total Tests:</strong> {summary_metrics.get('total_tests_run', 0)}
        </div>
        <div class="metric">
            <strong>Pass Rate:</strong>
            <span class="{'pass' if summary_metrics.get('overall_pass_rate', 0) >= 0.95 else 'fail'}">
                {summary_metrics.get('overall_pass_rate', 0)*100:.1f}%
            </span>
        </div>
    </div>

    <div class="summary">
        <h2>Test Suite Results</h2>
        {self._generate_suite_results_html(summary_metrics.get('suite_performance', {}))}
    </div>

    {self._generate_critical_issues_html(results.get('critical_issues', []))}

    {self._generate_recommendations_html(results.get('recommendations', []))}

</body>
</html>
        """
        return html

    def _generate_suite_results_html(self, suite_performance: Dict[str, Any]) -> str:
        """Generate HTML for suite results"""
        html = ""
        for suite_name, metrics in suite_performance.items():
            pass_rate = metrics.get('pass_rate', 0)
            status_class = 'pass' if pass_rate >= 0.9 else 'warning' if pass_rate >= 0.8 else 'fail'

            html += f"""
            <div class="metric">
                <strong>{suite_name.title()}:</strong><br>
                <span class="{status_class}">
                    {pass_rate*100:.1f}% pass rate
                </span><br>
                <small>
                    {metrics.get('tests_passed', 0)}/{metrics.get('tests_run', 0)} tests passed
                </small>
            </div>
            """
        return html

    def _generate_critical_issues_html(self, critical_issues: List[str]) -> str:
        """Generate HTML for critical issues"""
        if not critical_issues:
            return '<div class="summary"><h2>Critical Issues</h2><p class="pass">✅ No critical issues found!</p></div>'

        html = '<div class="critical"><h2>❌ Critical Issues</h2><ul>'
        for issue in critical_issues:
            html += f'<li>{issue}</li>'
        html += '</ul></div>'
        return html

    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations"""
        if not recommendations:
            return ""

        html = '<div class="recommendations"><h2>💡 Recommendations</h2><ul>'
        for rec in recommendations:
            html += f'<li>{rec}</li>'
        html += '</ul></div>'
        return html

    def _make_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj

    def print_final_summary(self):
        """Print final test summary to console"""
        if not self.overall_results:
            print("❌ No test results available")
            return

        summary = self.overall_results.get('summary_metrics', {})
        readiness = self.overall_results.get('production_readiness_assessment', {})
        critical_issues = self.overall_results.get('critical_issues', [])

        print(f"\n{'='*80}")
        print(f"🏁 COMPREHENSIVE TEST RESULTS SUMMARY")
        print(f"{'='*80}")

        # Overall metrics
        print(f"📊 OVERALL METRICS:")
        print(f"   Total Tests Run: {summary.get('total_tests_run', 0)}")
        print(f"   Tests Passed: {summary.get('total_tests_passed', 0)}")
        print(f"   Tests Failed: {summary.get('total_tests_failed', 0)}")
        print(f"   Overall Pass Rate: {summary.get('overall_pass_rate', 0)*100:.1f}%")

        # Production readiness
        print(f"\n🎯 PRODUCTION READINESS:")
        print(f"   Overall Score: {readiness.get('overall_score', 0)*100:.1f}%")
        print(f"   Readiness Level: {readiness.get('readiness_level', 'unknown').replace('_', ' ').title()}")
        print(f"   Production Ready: {'✅ YES' if readiness.get('production_ready', False) else '❌ NO'}")

        # Suite breakdown
        suite_performance = summary.get('suite_performance', {})
        if suite_performance:
            print(f"\n📋 SUITE BREAKDOWN:")
            for suite_name, metrics in suite_performance.items():
                status = '✅' if metrics.get('pass_rate', 0) >= 0.9 else '⚠️' if metrics.get('pass_rate', 0) >= 0.8 else '❌'
                print(f"   {status} {suite_name.title()}: {metrics.get('pass_rate', 0)*100:.1f}% ({metrics.get('tests_passed', 0)}/{metrics.get('tests_run', 0)})")

        # Critical issues
        if critical_issues:
            print(f"\n❌ CRITICAL ISSUES ({len(critical_issues)}):")
            for issue in critical_issues[:5]:  # Show first 5
                print(f"   • {issue}")
            if len(critical_issues) > 5:
                print(f"   ... and {len(critical_issues) - 5} more")
        else:
            print(f"\n✅ NO CRITICAL ISSUES FOUND")

        print(f"\n{'='*80}")

        # Final verdict
        if readiness.get('production_ready', False):
            print(f"🎉 SYSTEM IS PRODUCTION READY!")
            print(f"   All criteria met for production deployment.")
        else:
            print(f"⚠️ SYSTEM NEEDS IMPROVEMENT")
            print(f"   Address critical issues before production deployment.")

        print(f"{'='*80}")


async def main():
    """Main function to run comprehensive tests"""
    parser = argparse.ArgumentParser(description='Run comprehensive NSW Revenue AI tests')
    parser.add_argument('--api-url', default='http://localhost:8080',
                       help='API base URL (default: http://localhost:8080)')
    parser.add_argument('--suites', nargs='+',
                       choices=['functional', 'performance', 'accuracy', 'integration', 'edge_case'],
                       help='Specific test suites to run (default: all)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Initialize test runner
    test_runner = ComprehensiveTestRunner(args.api_url)

    print(f"🚀 NSW Revenue AI Comprehensive Testing Framework")
    print(f"API URL: {args.api_url}")
    print(f"Suites: {args.suites or 'all'}")
    print(f"{'='*80}")

    try:
        # Run comprehensive tests
        results = await test_runner.run_all_tests(args.suites)

        # Print final summary
        test_runner.print_final_summary()

        # Return appropriate exit code
        production_ready = results.get('production_readiness_assessment', {}).get('production_ready', False)
        return 0 if production_ready else 1

    except KeyboardInterrupt:
        print(f"\n⏹️ Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        logger.error(f"Test execution error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))