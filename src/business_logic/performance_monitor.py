from typing import Dict, List, Optional
import time
from datetime import datetime, timedelta
import psutil
import logging
from pathlib import Path
from collections import deque
import json
import asyncio

class PerformanceMonitor:
    def __init__(self):
        self.response_times = {}  # Operation -> list of response times
        self.operation_counts = {}  # Operation -> count
        self.slow_operations = deque(maxlen=100)  # Keep last 100 slow operations
        self.threshold = 2.0  # 2 seconds threshold
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging for performance monitoring"""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            filename=log_dir / 'performance.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    def start_operation(self, operation_name: str) -> str:
        """Start timing an operation"""
        operation_id = f"{operation_name}_{time.time()}"
        if operation_name not in self.response_times:
            self.response_times[operation_name] = []
            self.operation_counts[operation_name] = 0
        self.response_times[operation_name].append({
            'id': operation_id,
            'start': time.time(),
            'end': None,
            'duration': None
        })
        return operation_id

    def end_operation(self, operation_id: str) -> Optional[float]:
        """End timing an operation and return its duration"""
        operation_name = operation_id.rsplit('_', 1)[0]
        if operation_name not in self.response_times:
            return None

        # Find the operation record
        for op in self.response_times[operation_name]:
            if op['id'] == operation_id and op['end'] is None:
                end_time = time.time()
                op['end'] = end_time
                op['duration'] = end_time - op['start']
                self.operation_counts[operation_name] += 1

                # Check if operation was slow
                if op['duration'] > self.threshold:
                    self.slow_operations.append({
                        'operation': operation_name,
                        'duration': op['duration'],
                        'timestamp': datetime.utcnow().isoformat(),
                        'system_load': psutil.cpu_percent(),
                        'memory_usage': psutil.virtual_memory().percent
                    })
                    logging.warning(
                        f"Slow operation detected: {operation_name} "
                        f"took {op['duration']:.2f} seconds"
                    )

                return op['duration']
        return None

    def get_average_response_time(self, operation_name: str) -> Optional[float]:
        """Get average response time for an operation"""
        if operation_name in self.response_times:
            completed_ops = [
                op['duration'] for op in self.response_times[operation_name]
                if op['duration'] is not None
            ]
            if completed_ops:
                return sum(completed_ops) / len(completed_ops)
        return None

    def get_operation_statistics(self) -> Dict[str, Dict]:
        """Get statistics for all operations"""
        stats = {}
        for op_name in self.response_times:
            completed_ops = [
                op['duration'] for op in self.response_times[op_name]
                if op['duration'] is not None
            ]
            if completed_ops:
                stats[op_name] = {
                    'count': self.operation_counts[op_name],
                    'average': sum(completed_ops) / len(completed_ops),
                    'min': min(completed_ops),
                    'max': max(completed_ops),
                    'slow_count': len([d for d in completed_ops if d > self.threshold])
                }
        return stats

    def get_slow_operations(self) -> List[Dict]:
        """Get list of slow operations"""
        return list(self.slow_operations)

    def get_system_performance(self) -> Dict:
        """Get current system performance metrics"""
        return {
            'cpu_usage': psutil.cpu_percent(interval=1),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.utcnow().isoformat()
        }

    async def monitor_system_performance(self, interval: int = 60):
        """Continuously monitor system performance"""
        while True:
            try:
                metrics = self.get_system_performance()
                
                # Log if system resources are running high
                if metrics['cpu_usage'] > 80:
                    logging.warning(f"High CPU usage: {metrics['cpu_usage']}%")
                if metrics['memory_usage'] > 80:
                    logging.warning(f"High memory usage: {metrics['memory_usage']}%")
                if metrics['disk_usage'] > 80:
                    logging.warning(f"High disk usage: {metrics['disk_usage']}%")

                # Save metrics to log
                logging.info(f"System metrics: {json.dumps(metrics)}")
                
                await asyncio.sleep(interval)
            except Exception as e:
                logging.error(f"Error monitoring system performance: {str(e)}")
                await asyncio.sleep(interval)

    def clear_old_data(self, hours: int = 24):
        """Clear performance data older than specified hours"""
        cutoff = time.time() - (hours * 3600)
        for op_name in self.response_times:
            self.response_times[op_name] = [
                op for op in self.response_times[op_name]
                if op['start'] > cutoff
            ]

    def export_statistics(self, filepath: str):
        """Export performance statistics to file"""
        try:
            data = {
                'statistics': self.get_operation_statistics(),
                'slow_operations': list(self.slow_operations),
                'system_performance': self.get_system_performance(),
                'export_time': datetime.utcnow().isoformat()
            }
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error exporting statistics: {str(e)}")
            return False