"""Threshold-based alert management."""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class Alert:
    level: str  # "info", "warning", "critical"
    metric: str
    message: str
    value: float
    threshold: float


class AlertManager:
    """Monitor metrics and trigger threshold-based alerts."""

    DEFAULT_THRESHOLDS = {
        "complexity_avg": ("warning", 10.0, "Average cyclomatic complexity too high"),
        "security_high": ("critical", 5, "Too many HIGH severity security issues"),
        "coverage_functions": ("warning", 0.5, "Function documentation coverage below 50%"),
        "clone_ratio": ("warning", 0.2, "Code clone ratio above 20%"),
        "cost_usd": ("info", 1.0, "Claude API cost exceeded $1.00"),
    }

    def __init__(self):
        self.thresholds = dict(self.DEFAULT_THRESHOLDS)
        self.alerts: List[Alert] = []
        self.callbacks: List[Callable] = []

    def register_callback(self, callback: Callable) -> None:
        self.callbacks.append(callback)

    def check(self, metrics: Dict[str, Any]) -> List[Alert]:
        new_alerts = []
        for metric, value in metrics.items():
            if metric not in self.thresholds:
                continue
            level, threshold, message = self.thresholds[metric]
            triggered = False
            if metric in ("coverage_functions",):
                triggered = value < threshold
            else:
                triggered = value > threshold

            if triggered:
                alert = Alert(
                    level=level,
                    metric=metric,
                    message=f"{message}: {value:.2f} (threshold: {threshold})",
                    value=float(value),
                    threshold=float(threshold),
                )
                new_alerts.append(alert)
                self.alerts.append(alert)
                for cb in self.callbacks:
                    try:
                        cb(alert)
                    except Exception:
                        pass
        return new_alerts

    def get_active_alerts(self) -> List[Alert]:
        return self.alerts

    def clear(self) -> None:
        self.alerts.clear()
