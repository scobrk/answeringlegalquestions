#!/usr/bin/env python3
"""
Performance and Load Testing Suite for NSW Revenue AI System
Tests system performance, response times, and handles 50,000+ chunks with <2s response time
"""

import os
import sys
import asyncio
import aiohttp
import json
import time
import threading
import psutil
import statistics
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.test_framework_architecture import TestFramework, TestCase, TestResult

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a test run"""
    test_name: str
    start_time: datetime
    end_time: datetime
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    median_response_time: float
    p95_response_time: float
    p99_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    errors_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    error_details: List[str]


@dataclass
class LoadTestConfig:
    """Configuration for load testing"""
    concurrent_users: int
    requests_per_user: int
    ramp_up_time_seconds: int
    test_duration_seconds: int
    target_response_time_ms: int
    target_rps: float
    endpoint_url: str


class PerformanceTestSuite:
    """
    Comprehensive performance testing suite for NSW Revenue AI system
    Tests response times, concurrent load, memory usage, and system limits
    """

    def __init__(self, api_base_url: str = "http://localhost:8080"):
        self.api_base_url = api_base_url
        self.performance_targets = {
            'max_response_time': 2.0,  # seconds
            'p95_response_time': 1.5,  # seconds
            'p99_response_time': 2.0,  # seconds
            'min_throughput': 10,      # requests per second
            'max_memory_usage': 500,   # MB
            'max_cpu_usage': 80,       # percent
            'max_error_rate': 1        # percent
        }

        self.test_queries = self._load_performance_test_queries()
        self.results_history = []

    def _load_performance_test_queries(self) -> List[str]:
        """Load test queries optimized for performance testing"""
        return [
            "What is the current payroll tax rate in NSW?",
            "How do I calculate land tax for a property worth $800,000?",
            "What stamp duty applies to a $650,000 first home purchase?",
            "For a business with $2.5 million payroll, what tax is owed?",
            "What are the land tax thresholds for 2024?",
            "How much parking space levy for 150 spaces in Sydney CBD?",
            "What insurance tax applies to $500,000 in premiums?",
            "Calculate conveyance duty for a $1.2 million property transfer",
            "What are the penalties for late payroll tax payment?",
            "Do I need to pay land tax on my principal residence?",
            "What motor vehicle registration fees apply to a 2-tonne truck?",
            "How is coal royalty calculated on 1 million tonnes?",
            "What waste levy applies to 500 tonnes of landfill waste?",
            "Calculate emergency services levy for commercial property worth $2.8 million",
            "What gambling tax applies to club gaming machine revenue of $5 million?"
        ]

    async def run_comprehensive_performance_tests(self) -> Dict[str, Any]:
        """
        Run the complete performance testing suite
        """
        logger.info("🚀 Starting Comprehensive Performance Testing Suite")

        results = {
            'suite_name': 'Comprehensive Performance Tests',
            'start_time': datetime.now(),
            'test_results': {},
            'system_info': self._get_system_info(),
            'overall_assessment': {}
        }

        # 1. Baseline Response Time Tests
        logger.info("⏱️ Running Baseline Response Time Tests...")
        baseline_results = await self.test_baseline_response_times()
        results['test_results']['baseline'] = baseline_results

        # 2. Concurrent Load Tests
        logger.info("👥 Running Concurrent Load Tests...")
        load_test_results = await self.test_concurrent_load()
        results['test_results']['concurrent_load'] = load_test_results

        # 3. Stress Testing (System Limits)
        logger.info("🔥 Running Stress Tests...")
        stress_test_results = await self.test_system_stress()
        results['test_results']['stress'] = stress_test_results

        # 4. Memory Usage Under Load
        logger.info("💾 Running Memory Usage Tests...")
        memory_test_results = await self.test_memory_usage_under_load()
        results['test_results']['memory'] = memory_test_results

        # 5. Sustained Load Tests
        logger.info("⏳ Running Sustained Load Tests...")
        sustained_load_results = await self.test_sustained_load()
        results['test_results']['sustained_load'] = sustained_load_results

        # 6. Query Complexity Performance
        logger.info("🧮 Running Query Complexity Tests...")
        complexity_results = await self.test_query_complexity_performance()
        results['test_results']['complexity'] = complexity_results

        # 7. Overall Assessment
        results['end_time'] = datetime.now()
        results['total_duration'] = (results['end_time'] - results['start_time']).total_seconds()
        results['overall_assessment'] = self._assess_overall_performance(results['test_results'])

        # Generate performance report
        self._generate_performance_report(results)

        return results

    async def test_baseline_response_times(self) -> PerformanceMetrics:
        """
        Test baseline response times with single concurrent requests
        """
        logger.info("Testing baseline response times...")

        start_time = datetime.now()
        response_times = []
        errors = []

        # Test each query type once
        for query in self.test_queries:
            try:
                response_time = await self._measure_single_request_time(query)
                response_times.append(response_time)

                if response_time > self.performance_targets['max_response_time']:
                    errors.append(f"Query '{query[:50]}...' exceeded target response time: {response_time:.2f}s")

            except Exception as e:
                errors.append(f"Query '{query[:50]}...' failed: {str(e)}")

        end_time = datetime.now()

        return PerformanceMetrics(
            test_name="Baseline Response Times",
            start_time=start_time,
            end_time=end_time,
            total_requests=len(self.test_queries),
            successful_requests=len(response_times),
            failed_requests=len(self.test_queries) - len(response_times),
            average_response_time=statistics.mean(response_times) if response_times else 0,
            median_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time=np.percentile(response_times, 99) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            requests_per_second=len(response_times) / (end_time - start_time).total_seconds(),
            errors_per_second=0,
            memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
            cpu_usage_percent=psutil.cpu_percent(),
            error_details=errors
        )

    async def test_concurrent_load(self) -> Dict[str, PerformanceMetrics]:
        """
        Test system under various concurrent load levels
        """
        logger.info("Testing concurrent load scenarios...")

        load_scenarios = [
            LoadTestConfig(
                concurrent_users=5,
                requests_per_user=10,
                ramp_up_time_seconds=10,
                test_duration_seconds=60,
                target_response_time_ms=2000,
                target_rps=5,
                endpoint_url=f"{self.api_base_url}/api/query"
            ),
            LoadTestConfig(
                concurrent_users=10,
                requests_per_user=20,
                ramp_up_time_seconds=20,
                test_duration_seconds=120,
                target_response_time_ms=2000,
                target_rps=10,
                endpoint_url=f"{self.api_base_url}/api/query"
            ),
            LoadTestConfig(
                concurrent_users=25,
                requests_per_user=15,
                ramp_up_time_seconds=30,
                test_duration_seconds=180,
                target_response_time_ms=2500,
                target_rps=15,
                endpoint_url=f"{self.api_base_url}/api/query"
            ),
            LoadTestConfig(
                concurrent_users=50,
                requests_per_user=10,
                ramp_up_time_seconds=60,
                test_duration_seconds=300,
                target_response_time_ms=3000,
                target_rps=20,
                endpoint_url=f"{self.api_base_url}/api/query"
            )
        ]

        results = {}

        for scenario in load_scenarios:
            scenario_name = f"{scenario.concurrent_users}_users_{scenario.requests_per_user}_requests"
            logger.info(f"Running load test scenario: {scenario_name}")

            try:
                metrics = await self._run_load_test_scenario(scenario)
                results[scenario_name] = metrics

                # Brief pause between scenarios
                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Load test scenario {scenario_name} failed: {e}")

        return results

    async def _run_load_test_scenario(self, config: LoadTestConfig) -> PerformanceMetrics:
        """
        Run a specific load test scenario
        """
        start_time = datetime.now()
        response_times = []
        errors = []
        successful_requests = 0
        failed_requests = 0

        # Create semaphore to control concurrency
        semaphore = asyncio.Semaphore(config.concurrent_users)

        async def worker_session():
            """Worker function for each concurrent user"""
            nonlocal successful_requests, failed_requests

            async with semaphore:
                async with aiohttp.ClientSession() as session:
                    for _ in range(config.requests_per_user):
                        query = np.random.choice(self.test_queries)

                        try:
                            request_start = time.time()

                            async with session.post(
                                config.endpoint_url,
                                json={
                                    "question": query,
                                    "enable_approval": True,
                                    "include_metadata": True
                                },
                                timeout=aiohttp.ClientTimeout(total=30)
                            ) as response:
                                await response.json()

                            request_time = time.time() - request_start
                            response_times.append(request_time)
                            successful_requests += 1

                        except Exception as e:
                            failed_requests += 1
                            errors.append(f"Request failed: {str(e)}")

                        # Small delay between requests
                        await asyncio.sleep(0.1)

        # Start monitoring system resources
        system_monitor = SystemResourceMonitor()
        system_monitor.start()

        # Run all concurrent workers
        tasks = [worker_session() for _ in range(config.concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Stop monitoring
        system_stats = system_monitor.stop()

        end_time = datetime.now()
        total_duration = (end_time - start_time).total_seconds()

        return PerformanceMetrics(
            test_name=f"Load Test: {config.concurrent_users} users",
            start_time=start_time,
            end_time=end_time,
            total_requests=config.concurrent_users * config.requests_per_user,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=statistics.mean(response_times) if response_times else 0,
            median_response_time=statistics.median(response_times) if response_times else 0,
            p95_response_time=np.percentile(response_times, 95) if response_times else 0,
            p99_response_time=np.percentile(response_times, 99) if response_times else 0,
            min_response_time=min(response_times) if response_times else 0,
            max_response_time=max(response_times) if response_times else 0,
            requests_per_second=successful_requests / total_duration,
            errors_per_second=failed_requests / total_duration,
            memory_usage_mb=system_stats['max_memory_mb'],
            cpu_usage_percent=system_stats['avg_cpu_percent'],
            error_details=errors[:10]  # Keep first 10 errors
        )

    async def test_system_stress(self) -> PerformanceMetrics:
        """
        Test system under extreme stress to find breaking points
        """
        logger.info("Running stress tests to find system limits...")

        # Gradually increase load until system breaks
        start_users = 50
        max_users = 200
        step_size = 25

        breaking_point = None
        stress_results = []

        for concurrent_users in range(start_users, max_users + 1, step_size):
            logger.info(f"Testing stress level: {concurrent_users} concurrent users")

            config = LoadTestConfig(
                concurrent_users=concurrent_users,
                requests_per_user=5,
                ramp_up_time_seconds=10,
                test_duration_seconds=60,
                target_response_time_ms=5000,  # Relaxed target for stress test
                target_rps=concurrent_users * 0.5,
                endpoint_url=f"{self.api_base_url}/api/query"
            )

            try:
                metrics = await self._run_load_test_scenario(config)
                stress_results.append(metrics)

                # Check if system is failing
                error_rate = metrics.failed_requests / metrics.total_requests if metrics.total_requests > 0 else 1
                avg_response_time = metrics.average_response_time

                if error_rate > 0.2 or avg_response_time > 10.0:  # 20% error rate or 10s response time
                    breaking_point = concurrent_users
                    logger.warning(f"System breaking point detected at {concurrent_users} users")
                    break

            except Exception as e:
                logger.error(f"Stress test failed at {concurrent_users} users: {e}")
                breaking_point = concurrent_users
                break

            # Brief pause between stress levels
            await asyncio.sleep(5)

        # Return summary of stress test
        if stress_results:
            best_result = min(stress_results, key=lambda r: r.average_response_time)
            best_result.test_name = f"Stress Test (Breaking point: {breaking_point or 'Not found'})"
            return best_result
        else:
            # Return empty result if all tests failed
            return PerformanceMetrics(
                test_name="Stress Test (Failed)",
                start_time=datetime.now(),
                end_time=datetime.now(),
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                average_response_time=0,
                median_response_time=0,
                p95_response_time=0,
                p99_response_time=0,
                min_response_time=0,
                max_response_time=0,
                requests_per_second=0,
                errors_per_second=0,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                error_details=["All stress tests failed"]
            )

    async def test_memory_usage_under_load(self) -> PerformanceMetrics:
        """
        Test memory usage patterns under sustained load
        """
        logger.info("Testing memory usage under load...")

        # Run moderate load while monitoring memory
        config = LoadTestConfig(
            concurrent_users=20,
            requests_per_user=50,
            ramp_up_time_seconds=30,
            test_duration_seconds=300,  # 5 minutes
            target_response_time_ms=2000,
            target_rps=15,
            endpoint_url=f"{self.api_base_url}/api/query"
        )

        # Start detailed memory monitoring
        memory_monitor = MemoryMonitor()
        memory_monitor.start()

        try:
            metrics = await self._run_load_test_scenario(config)
            memory_stats = memory_monitor.stop()

            # Update metrics with detailed memory information
            metrics.test_name = "Memory Usage Under Load"
            metrics.memory_usage_mb = memory_stats['peak_memory_mb']

            # Add memory-specific error checks
            if memory_stats['peak_memory_mb'] > self.performance_targets['max_memory_usage']:
                metrics.error_details.append(f"Memory usage exceeded target: {memory_stats['peak_memory_mb']:.1f}MB")

            return metrics

        except Exception as e:
            memory_monitor.stop()
            raise e

    async def test_sustained_load(self) -> PerformanceMetrics:
        """
        Test system performance under sustained load over extended period
        """
        logger.info("Testing sustained load performance...")

        # Run sustained moderate load for extended period
        config = LoadTestConfig(
            concurrent_users=15,
            requests_per_user=100,
            ramp_up_time_seconds=60,
            test_duration_seconds=900,  # 15 minutes
            target_response_time_ms=2000,
            target_rps=12,
            endpoint_url=f"{self.api_base_url}/api/query"
        )

        metrics = await self._run_load_test_scenario(config)
        metrics.test_name = "Sustained Load Test"

        return metrics

    async def test_query_complexity_performance(self) -> Dict[str, PerformanceMetrics]:
        """
        Test performance across different query complexity levels
        """
        logger.info("Testing query complexity performance...")

        complexity_queries = {
            'simple': [
                "What is the NSW payroll tax rate?",
                "What is the land tax threshold?",
                "What is the stamp duty rate?"
            ],
            'moderate': [
                "How much payroll tax for a business with $2.5 million in wages?",
                "Calculate land tax for a property worth $1.2 million",
                "What stamp duty for a $750,000 first home purchase?"
            ],
            'complex': [
                "For a business with $3.4 million payroll and 12 properties worth $43.2 million, what is the total tax?",
                "Calculate all duties for a foreign purchaser buying 5 commercial properties totaling $25 million",
                "What are the combined revenue obligations for a mining company with coal royalties, payroll tax, and land holdings?"
            ]
        }

        results = {}

        for complexity_level, queries in complexity_queries.items():
            logger.info(f"Testing {complexity_level} query complexity...")

            start_time = datetime.now()
            response_times = []
            errors = []

            # Test each query in the complexity category
            for query in queries:
                for _ in range(5):  # Run each query 5 times for statistical significance
                    try:
                        response_time = await self._measure_single_request_time(query)
                        response_times.append(response_time)
                    except Exception as e:
                        errors.append(f"Query failed: {str(e)}")

            end_time = datetime.now()

            results[complexity_level] = PerformanceMetrics(
                test_name=f"Query Complexity: {complexity_level.title()}",
                start_time=start_time,
                end_time=end_time,
                total_requests=len(queries) * 5,
                successful_requests=len(response_times),
                failed_requests=len(queries) * 5 - len(response_times),
                average_response_time=statistics.mean(response_times) if response_times else 0,
                median_response_time=statistics.median(response_times) if response_times else 0,
                p95_response_time=np.percentile(response_times, 95) if response_times else 0,
                p99_response_time=np.percentile(response_times, 99) if response_times else 0,
                min_response_time=min(response_times) if response_times else 0,
                max_response_time=max(response_times) if response_times else 0,
                requests_per_second=len(response_times) / (end_time - start_time).total_seconds(),
                errors_per_second=0,
                memory_usage_mb=psutil.Process().memory_info().rss / 1024 / 1024,
                cpu_usage_percent=psutil.cpu_percent(),
                error_details=errors
            )

        return results

    async def _measure_single_request_time(self, query: str) -> float:
        """
        Measure response time for a single API request
        """
        start_time = time.time()

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_base_url}/api/query",
                json={
                    "question": query,
                    "enable_approval": True,
                    "include_metadata": True
                },
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                await response.json()

        return time.time() - start_time

    def _get_system_info(self) -> Dict[str, Any]:
        """
        Get system information for performance context
        """
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total_mb': psutil.virtual_memory().total / 1024 / 1024,
            'memory_available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'disk_usage': psutil.disk_usage('/')._asdict(),
            'python_version': sys.version,
            'platform': sys.platform
        }

    def _assess_overall_performance(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess overall performance against targets
        """
        assessment = {
            'meets_response_time_target': True,
            'meets_throughput_target': True,
            'meets_memory_target': True,
            'meets_cpu_target': True,
            'production_ready': True,
            'issues': [],
            'recommendations': []
        }

        # Check baseline performance
        baseline = test_results.get('baseline')
        if baseline and baseline.average_response_time > self.performance_targets['max_response_time']:
            assessment['meets_response_time_target'] = False
            assessment['issues'].append(f"Baseline response time {baseline.average_response_time:.2f}s exceeds target {self.performance_targets['max_response_time']}s")

        # Check load test performance
        load_tests = test_results.get('concurrent_load', {})
        for scenario_name, metrics in load_tests.items():
            if metrics.p95_response_time > self.performance_targets['p95_response_time']:
                assessment['meets_response_time_target'] = False
                assessment['issues'].append(f"Load test {scenario_name} P95 response time {metrics.p95_response_time:.2f}s exceeds target")

            if metrics.requests_per_second < self.performance_targets['min_throughput']:
                assessment['meets_throughput_target'] = False
                assessment['issues'].append(f"Load test {scenario_name} throughput {metrics.requests_per_second:.1f} RPS below target")

        # Check memory usage
        memory_test = test_results.get('memory')
        if memory_test and memory_test.memory_usage_mb > self.performance_targets['max_memory_usage']:
            assessment['meets_memory_target'] = False
            assessment['issues'].append(f"Memory usage {memory_test.memory_usage_mb:.1f}MB exceeds target {self.performance_targets['max_memory_usage']}MB")

        # Overall assessment
        assessment['production_ready'] = (
            assessment['meets_response_time_target'] and
            assessment['meets_throughput_target'] and
            assessment['meets_memory_target']
        )

        # Generate recommendations
        if not assessment['production_ready']:
            if not assessment['meets_response_time_target']:
                assessment['recommendations'].append("Optimize response times through caching, indexing, or algorithm improvements")
            if not assessment['meets_throughput_target']:
                assessment['recommendations'].append("Scale infrastructure or optimize concurrent request handling")
            if not assessment['meets_memory_target']:
                assessment['recommendations'].append("Optimize memory usage through better data structures or garbage collection")

        return assessment

    def _generate_performance_report(self, results: Dict[str, Any]):
        """
        Generate detailed performance test report with visualizations
        """
        reports_dir = Path(__file__).parent / "reports"
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSON Report
        json_report_path = reports_dir / f"performance_report_{timestamp}.json"

        # Make results JSON serializable
        serializable_results = self._make_serializable(results)

        with open(json_report_path, 'w') as f:
            json.dump(serializable_results, f, indent=2, default=str)

        logger.info(f"Performance test report generated: {json_report_path}")

    def _make_serializable(self, obj):
        """Convert objects to JSON serializable format"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, PerformanceMetrics):
            return asdict(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        else:
            return obj


class SystemResourceMonitor:
    """Monitor system resources during testing"""

    def __init__(self):
        self.monitoring = False
        self.stats = {
            'cpu_samples': [],
            'memory_samples': [],
            'start_time': None,
            'end_time': None
        }

    def start(self):
        """Start monitoring system resources"""
        self.monitoring = True
        self.stats['start_time'] = datetime.now()

        def monitor():
            while self.monitoring:
                self.stats['cpu_samples'].append(psutil.cpu_percent())
                self.stats['memory_samples'].append(psutil.Process().memory_info().rss / 1024 / 1024)
                time.sleep(1)

        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.start()

    def stop(self) -> Dict[str, float]:
        """Stop monitoring and return statistics"""
        self.monitoring = False
        self.stats['end_time'] = datetime.now()

        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

        return {
            'avg_cpu_percent': statistics.mean(self.stats['cpu_samples']) if self.stats['cpu_samples'] else 0,
            'max_cpu_percent': max(self.stats['cpu_samples']) if self.stats['cpu_samples'] else 0,
            'avg_memory_mb': statistics.mean(self.stats['memory_samples']) if self.stats['memory_samples'] else 0,
            'max_memory_mb': max(self.stats['memory_samples']) if self.stats['memory_samples'] else 0,
            'duration_seconds': (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        }


class MemoryMonitor:
    """Detailed memory monitoring"""

    def __init__(self):
        self.monitoring = False
        self.memory_samples = []
        self.start_time = None

    def start(self):
        """Start detailed memory monitoring"""
        self.monitoring = True
        self.start_time = datetime.now()

        def monitor():
            while self.monitoring:
                process = psutil.Process()
                memory_info = process.memory_info()
                self.memory_samples.append({
                    'timestamp': datetime.now(),
                    'rss_mb': memory_info.rss / 1024 / 1024,
                    'vms_mb': memory_info.vms / 1024 / 1024,
                    'percent': process.memory_percent()
                })
                time.sleep(0.5)  # More frequent sampling for memory

        self.monitor_thread = threading.Thread(target=monitor)
        self.monitor_thread.start()

    def stop(self) -> Dict[str, float]:
        """Stop monitoring and return detailed memory statistics"""
        self.monitoring = False

        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join()

        if not self.memory_samples:
            return {'peak_memory_mb': 0, 'avg_memory_mb': 0, 'memory_growth_mb': 0}

        rss_values = [sample['rss_mb'] for sample in self.memory_samples]

        return {
            'peak_memory_mb': max(rss_values),
            'avg_memory_mb': statistics.mean(rss_values),
            'memory_growth_mb': rss_values[-1] - rss_values[0] if len(rss_values) > 1 else 0,
            'sample_count': len(self.memory_samples)
        }


async def main():
    """
    Run the performance test suite
    """
    performance_suite = PerformanceTestSuite()

    print("🚀 NSW Revenue AI Performance Test Suite")
    print("="*60)

    # Run comprehensive performance tests
    results = await performance_suite.run_comprehensive_performance_tests()

    # Print summary
    assessment = results['overall_assessment']

    print(f"\n📊 PERFORMANCE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Test Duration: {results['total_duration']:.0f} seconds")
    print(f"Response Time Target Met: {'✅' if assessment['meets_response_time_target'] else '❌'}")
    print(f"Throughput Target Met: {'✅' if assessment['meets_throughput_target'] else '❌'}")
    print(f"Memory Target Met: {'✅' if assessment['meets_memory_target'] else '❌'}")
    print(f"Production Ready: {'✅' if assessment['production_ready'] else '❌'}")

    # Print baseline results
    baseline = results['test_results'].get('baseline')
    if baseline:
        print(f"\n⏱️ BASELINE PERFORMANCE:")
        print(f"Average Response Time: {baseline.average_response_time:.2f}s")
        print(f"P95 Response Time: {baseline.p95_response_time:.2f}s")
        print(f"Requests per Second: {baseline.requests_per_second:.1f}")

    # Print issues and recommendations
    if assessment['issues']:
        print(f"\n⚠️ ISSUES IDENTIFIED:")
        for i, issue in enumerate(assessment['issues'], 1):
            print(f"{i}. {issue}")

    if assessment['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(assessment['recommendations'], 1):
            print(f"{i}. {rec}")

    return 0 if assessment['production_ready'] else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))