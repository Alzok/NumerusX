import time
import numpy as np
from collections import defaultdict
import logging

class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
        self.start_time = time.time()
        self.logger = logging.getLogger('PerfMonitor')

    def track(self, metric: str, value: float):
        try:
            self.metrics[metric].append((time.time(), value))
        except Exception as e:
            self.logger.error(f"Erreur de tracking: {str(e)}")

    def generate_report(self) -> dict:
        return {
            'uptime': self._format_uptime(),
            'success_rate': self._calc_success_rate(),
            'avg_latency': self._calc_avg_latency(),
            'profitability': np.nanmean(self.metrics['profit']) if self.metrics['profit'] else 0
        }

    def _format_uptime(self) -> str:
        delta = time.time() - self.start_time
        hours = int(delta // 3600)
        minutes = int((delta % 3600) // 60)
        return f"{hours}h{minutes}m"

    def _calc_success_rate(self) -> float:
        trades = self.metrics.get('trade', [])
        if not trades:
            return 0.0
        successes = sum(1 for _,s in trades if s == 'success')
        return successes / len(trades)

    def _calc_avg_latency(self) -> float:
        latencies = [v for _,v in self.metrics.get('latency', [])]
        return np.mean(latencies) if latencies else 0

    def log_metrics(self):
        report = self.generate_report()
        self.logger.info(f"Rapport performance: {report}")