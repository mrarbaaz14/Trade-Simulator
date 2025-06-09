import time
from dataclasses import dataclass
from typing import List, Dict
import statistics
import threading
from collections import deque
import logging

@dataclass
class LatencyMetrics:
    """Container for latency measurements."""
    data_processing: float  # Time taken to process data
    ui_update: float       # Time taken to update UI
    end_to_end: float      # Total time from data receipt to UI update
    timestamp: float       # When the measurement was taken

class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.metrics_history = deque(maxlen=window_size)
        self.lock = threading.Lock()
        self.start_time = None
        self.current_metrics = None
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('PerformanceMonitor')
    
    def start_measurement(self):
        """Start a new measurement cycle."""
        self.start_time = time.time()
        self.current_metrics = LatencyMetrics(
            data_processing=0.0,
            ui_update=0.0,
            end_to_end=0.0,
            timestamp=self.start_time
        )
    
    def record_data_processing(self):
        """Record the time taken for data processing."""
        if self.current_metrics is None:
            return
        
        current_time = time.time()
        self.current_metrics.data_processing = current_time - self.start_time
    
    def record_ui_update(self):
        """Record the time taken for UI update."""
        if self.current_metrics is None:
            return
        
        current_time = time.time()
        self.current_metrics.ui_update = current_time - self.start_time
    
    def end_measurement(self):
        """End the current measurement cycle and store metrics."""
        if self.current_metrics is None:
            return
        
        current_time = time.time()
        self.current_metrics.end_to_end = current_time - self.start_time
        
        with self.lock:
            self.metrics_history.append(self.current_metrics)
        
        self.current_metrics = None
        self.start_time = None
    
    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Calculate statistics for all metrics."""
        with self.lock:
            if not self.metrics_history:
                return {}
            
            metrics = {
                'data_processing': [],
                'ui_update': [],
                'end_to_end': []
            }
            
            for m in self.metrics_history:
                metrics['data_processing'].append(m.data_processing)
                metrics['ui_update'].append(m.ui_update)
                metrics['end_to_end'].append(m.end_to_end)
            
            stats = {}
            for metric_name, values in metrics.items():
                stats[metric_name] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'p95': statistics.quantiles(values, n=20)[18],  # 95th percentile
                    'p99': statistics.quantiles(values, n=100)[98],  # 99th percentile
                    'min': min(values),
                    'max': max(values)
                }
            
            return stats
    
    def log_statistics(self):
        """Log current performance statistics."""
        stats = self.get_statistics()
        if not stats:
            return
        
        self.logger.info("Performance Statistics:")
        for metric_name, metric_stats in stats.items():
            self.logger.info(f"\n{metric_name}:")
            for stat_name, value in metric_stats.items():
                self.logger.info(f"  {stat_name}: {value*1000:.2f}ms")
    
    def check_performance_thresholds(self, thresholds: Dict[str, float]) -> Dict[str, bool]:
        """
        Check if current performance meets specified thresholds.
        
        Args:
            thresholds: Dictionary of metric names and their maximum allowed values in seconds
            
        Returns:
            Dictionary indicating which thresholds were exceeded
        """
        stats = self.get_statistics()
        if not stats:
            return {}
        
        results = {}
        for metric_name, threshold in thresholds.items():
            if metric_name in stats:
                # Check if p95 exceeds threshold
                results[metric_name] = stats[metric_name]['p95'] <= threshold
        
        return results
    
    def get_recent_metrics(self, n: int = 10) -> List[LatencyMetrics]:
        """Get the n most recent metrics."""
        with self.lock:
            return list(self.metrics_history)[-n:]
    
    def clear_history(self):
        """Clear the metrics history."""
        with self.lock:
            self.metrics_history.clear() 