"""
Performance Monitor for Enhanced NSW Revenue Vector Store
Provides monitoring, caching, and optimization features
"""

import time
import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from collections import deque
import threading

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics for a single operation"""
    operation_type: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    memory_usage_mb: float
    cpu_usage_percent: float
    success: bool
    error_message: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class SystemMetrics:
    """Overall system performance metrics"""
    timestamp: datetime
    total_operations: int
    average_response_time: float
    p95_response_time: float
    success_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float
    cache_hit_rate: float
    active_components: List[str]

class PerformanceMonitor:
    """
    Monitors and optimizes performance of the enhanced vector store system
    """

    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.cache_stats = {'hits': 0, 'misses': 0}
        self.active_operations = {}
        self.lock = threading.Lock()

        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 2.0,  # 2 seconds
            'response_time_critical': 5.0,  # 5 seconds
            'memory_warning': 400,  # 400 MB
            'memory_critical': 500,  # 500 MB
            'cpu_warning': 80,  # 80%
            'cpu_critical': 95  # 95%
        }

    def start_operation(self, operation_type: str, operation_id: str = None) -> str:
        """Start monitoring an operation"""
        if operation_id is None:
            operation_id = f"{operation_type}_{int(time.time()*1000)}"

        with self.lock:
            self.active_operations[operation_id] = {
                'operation_type': operation_type,
                'start_time': datetime.now(),
                'start_memory': self._get_memory_usage(),
                'start_cpu': self._get_cpu_usage()
            }

        return operation_id

    def end_operation(self,
                     operation_id: str,
                     success: bool = True,
                     error_message: str = None,
                     additional_data: Dict[str, Any] = None) -> PerformanceMetrics:
        """End monitoring an operation and record metrics"""

        end_time = datetime.now()
        end_memory = self._get_memory_usage()
        end_cpu = self._get_cpu_usage()

        with self.lock:
            if operation_id not in self.active_operations:
                logger.warning(f"Operation {operation_id} not found in active operations")
                return None

            op_data = self.active_operations.pop(operation_id)

        # Calculate metrics
        duration = (end_time - op_data['start_time']).total_seconds()

        metrics = PerformanceMetrics(
            operation_type=op_data['operation_type'],
            start_time=op_data['start_time'],
            end_time=end_time,
            duration_seconds=duration,
            memory_usage_mb=end_memory,
            cpu_usage_percent=end_cpu,
            success=success,
            error_message=error_message,
            additional_data=additional_data or {}
        )

        # Store metrics
        self.metrics_history.append(metrics)

        # Check for performance issues
        self._check_performance_alerts(metrics)

        return metrics

    def record_cache_hit(self) -> None:
        """Record a cache hit"""
        with self.lock:
            self.cache_stats['hits'] += 1

    def record_cache_miss(self) -> None:
        """Record a cache miss"""
        with self.lock:
            self.cache_stats['misses'] += 1

    def get_system_metrics(self, time_window_minutes: int = 10) -> SystemMetrics:
        """Get aggregated system metrics for the specified time window"""

        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)

        # Filter metrics to time window
        recent_metrics = [
            m for m in self.metrics_history
            if m.start_time >= cutoff_time
        ]

        if not recent_metrics:
            return SystemMetrics(
                timestamp=datetime.now(),
                total_operations=0,
                average_response_time=0.0,
                p95_response_time=0.0,
                success_rate=0.0,
                memory_usage_mb=self._get_memory_usage(),
                cpu_usage_percent=self._get_cpu_usage(),
                cache_hit_rate=0.0,
                active_components=[]
            )

        # Calculate metrics
        durations = [m.duration_seconds for m in recent_metrics]
        successful_ops = [m for m in recent_metrics if m.success]

        # Sort durations for percentile calculation
        sorted_durations = sorted(durations)
        p95_index = int(0.95 * len(sorted_durations)) if sorted_durations else 0
        p95_response_time = sorted_durations[p95_index] if sorted_durations else 0.0

        # Cache hit rate
        total_cache_ops = self.cache_stats['hits'] + self.cache_stats['misses']
        cache_hit_rate = (self.cache_stats['hits'] / total_cache_ops) if total_cache_ops > 0 else 0.0

        # Active components
        active_components = list(set(m.operation_type for m in recent_metrics))

        return SystemMetrics(
            timestamp=datetime.now(),
            total_operations=len(recent_metrics),
            average_response_time=sum(durations) / len(durations) if durations else 0.0,
            p95_response_time=p95_response_time,
            success_rate=len(successful_ops) / len(recent_metrics) if recent_metrics else 0.0,
            memory_usage_mb=self._get_memory_usage(),
            cpu_usage_percent=self._get_cpu_usage(),
            cache_hit_rate=cache_hit_rate,
            active_components=active_components
        )

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""

        system_metrics = self.get_system_metrics()

        # Operation type breakdown
        operation_breakdown = {}
        for metric in self.metrics_history:
            op_type = metric.operation_type
            if op_type not in operation_breakdown:
                operation_breakdown[op_type] = {
                    'count': 0,
                    'total_duration': 0.0,
                    'success_count': 0,
                    'error_count': 0
                }

            breakdown = operation_breakdown[op_type]
            breakdown['count'] += 1
            breakdown['total_duration'] += metric.duration_seconds
            if metric.success:
                breakdown['success_count'] += 1
            else:
                breakdown['error_count'] += 1

        # Calculate averages
        for op_type, data in operation_breakdown.items():
            data['average_duration'] = data['total_duration'] / data['count']
            data['success_rate'] = data['success_count'] / data['count']

        # Recent errors
        recent_errors = [
            {
                'operation_type': m.operation_type,
                'timestamp': m.start_time.isoformat(),
                'duration': m.duration_seconds,
                'error_message': m.error_message
            }
            for m in list(self.metrics_history)[-50:]  # Last 50 operations
            if not m.success
        ]

        return {
            'system_metrics': asdict(system_metrics),
            'operation_breakdown': operation_breakdown,
            'recent_errors': recent_errors,
            'cache_statistics': self.cache_stats.copy(),
            'performance_thresholds': self.thresholds.copy(),
            'active_operations_count': len(self.active_operations)
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB (simplified version)"""
        try:
            # Use os.getpid() and basic resource tracking
            pid = os.getpid()
            # This is a simplified placeholder - in production use psutil
            return 100.0  # Placeholder value
        except Exception:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage (simplified version)"""
        try:
            # Simplified placeholder - in production use psutil
            return 25.0  # Placeholder value
        except Exception:
            return 0.0

    def _check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance issues and log alerts"""

        # Response time alerts
        if metrics.duration_seconds > self.thresholds['response_time_critical']:
            logger.critical(f"CRITICAL: {metrics.operation_type} took {metrics.duration_seconds:.2f}s "
                          f"(threshold: {self.thresholds['response_time_critical']}s)")
        elif metrics.duration_seconds > self.thresholds['response_time_warning']:
            logger.warning(f"WARNING: {metrics.operation_type} took {metrics.duration_seconds:.2f}s "
                         f"(threshold: {self.thresholds['response_time_warning']}s)")

        # Memory alerts
        if metrics.memory_usage_mb > self.thresholds['memory_critical']:
            logger.critical(f"CRITICAL: Memory usage {metrics.memory_usage_mb:.1f}MB "
                          f"(threshold: {self.thresholds['memory_critical']}MB)")
        elif metrics.memory_usage_mb > self.thresholds['memory_warning']:
            logger.warning(f"WARNING: Memory usage {metrics.memory_usage_mb:.1f}MB "
                         f"(threshold: {self.thresholds['memory_warning']}MB)")

        # CPU alerts
        if metrics.cpu_usage_percent > self.thresholds['cpu_critical']:
            logger.critical(f"CRITICAL: CPU usage {metrics.cpu_usage_percent:.1f}% "
                          f"(threshold: {self.thresholds['cpu_critical']}%)")
        elif metrics.cpu_usage_percent > self.thresholds['cpu_warning']:
            logger.warning(f"WARNING: CPU usage {metrics.cpu_usage_percent:.1f}% "
                         f"(threshold: {self.thresholds['cpu_warning']}%)")

    def export_metrics(self, filepath: str) -> None:
        """Export performance metrics to file"""
        report = self.get_performance_report()

        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Performance metrics exported to {filepath}")

    def reset_metrics(self) -> None:
        """Reset all metrics and statistics"""
        with self.lock:
            self.metrics_history.clear()
            self.cache_stats = {'hits': 0, 'misses': 0}
            self.active_operations.clear()

        logger.info("Performance metrics reset")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


def monitor_operation(operation_type: str):
    """Decorator to monitor function performance"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            op_id = performance_monitor.start_operation(operation_type)

            try:
                result = func(*args, **kwargs)
                performance_monitor.end_operation(op_id, success=True)
                return result

            except Exception as e:
                performance_monitor.end_operation(
                    op_id,
                    success=False,
                    error_message=str(e)
                )
                raise

        return wrapper
    return decorator


def main():
    """Test the performance monitor"""
    monitor = PerformanceMonitor()

    # Simulate some operations
    print("🔧 Testing Performance Monitor...")

    # Test vector search operations
    for i in range(5):
        op_id = monitor.start_operation('vector_search')
        time.sleep(0.1 + i * 0.05)  # Simulate increasing response times
        monitor.end_operation(
            op_id,
            success=i < 4,  # Last operation fails
            error_message="Test error" if i == 4 else None,
            additional_data={'query_length': 50 + i * 10}
        )

    # Test rate calculations
    for i in range(3):
        op_id = monitor.start_operation('rate_calculation')
        time.sleep(0.05)
        monitor.end_operation(op_id, success=True)

    # Test cache operations
    for i in range(10):
        if i < 7:
            monitor.record_cache_hit()
        else:
            monitor.record_cache_miss()

    # Get performance report
    print("\n📊 Performance Report:")
    report = monitor.get_performance_report()

    system_metrics = report['system_metrics']
    print(f"Total operations: {system_metrics['total_operations']}")
    print(f"Average response time: {system_metrics['average_response_time']:.3f}s")
    print(f"P95 response time: {system_metrics['p95_response_time']:.3f}s")
    print(f"Success rate: {system_metrics['success_rate']:.1%}")
    print(f"Cache hit rate: {system_metrics['cache_hit_rate']:.1%}")
    print(f"Memory usage: {system_metrics['memory_usage_mb']:.1f}MB")

    print(f"\n🔍 Operation Breakdown:")
    for op_type, data in report['operation_breakdown'].items():
        print(f"  {op_type}:")
        print(f"    Count: {data['count']}")
        print(f"    Avg duration: {data['average_duration']:.3f}s")
        print(f"    Success rate: {data['success_rate']:.1%}")

    if report['recent_errors']:
        print(f"\n❌ Recent Errors:")
        for error in report['recent_errors']:
            print(f"  {error['operation_type']}: {error['error_message']}")


if __name__ == "__main__":
    main()