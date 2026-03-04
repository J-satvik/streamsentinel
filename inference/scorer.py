from dataclasses import dataclass, field
from datetime import datetime
from features.extractor import extract
from features.schema import FeatureVector
from inference.engine import InferenceEngine


@dataclass
class AnomalyAlert:
    host:       str
    timestamp:  datetime
    score:      float
    threshold:  float
    confidence: float
    severity:   str          # LOW / MEDIUM / HIGH / CRITICAL
    feature_snapshot: dict


def classify_severity(confidence: float) -> str:
    if confidence < 0.3:
        return "LOW"
    elif confidence < 0.6:
        return "MEDIUM"
    elif confidence < 0.85:
        return "HIGH"
    return "CRITICAL"


class Scorer:
    def __init__(self, engine: InferenceEngine):
        self.engine = engine

    def evaluate(self, events: list, host: str) -> AnomalyAlert | None:
        if not events:
            return None

        fv     = extract(events, host)
        result = self.engine.score(fv.to_vector())

        if not result["is_anomaly"]:
            return None

        severity = classify_severity(result["confidence"])

        return AnomalyAlert(
            host=host,
            timestamp=datetime.utcnow(),
            score=result["score"],
            threshold=result["threshold"],
            confidence=result["confidence"],
            severity=severity,
            feature_snapshot={
                "ip_entropy":   round(fv.ip_entropy, 4),
                "error_ratio":  round(fv.error_ratio, 4),
                "latency_mean": round(fv.latency_mean, 2),
                "rate_429":     round(fv.rate_429, 4),
                "unique_ips":   fv.unique_ips,
            },
        )