import json
from datetime import datetime
from inference.scorer import AnomalyAlert


class ConsoleAlerter:
    """Simple alerter that prints to console — swap for Redis/Slack later."""

    COLORS = {
        "LOW":      "\033[93m",   # yellow
        "MEDIUM":   "\033[33m",   # orange
        "HIGH":     "\033[91m",   # red
        "CRITICAL": "\033[31m",   # bright red
    }
    RESET = "\033[0m"

    def dispatch(self, alert: AnomalyAlert):
        color = self.COLORS.get(alert.severity, "")
        print(
            f"{color}[{alert.severity}] ANOMALY DETECTED{self.RESET} "
            f"host={alert.host} "
            f"score={alert.score:.4f} "
            f"confidence={alert.confidence:.2%} "
            f"ip_entropy={alert.feature_snapshot['ip_entropy']} "
            f"error_ratio={alert.feature_snapshot['error_ratio']}"
        )   