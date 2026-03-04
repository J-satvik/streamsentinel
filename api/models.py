from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertResponse(BaseModel):
    host:       str
    timestamp:  datetime
    score:      float
    threshold:  float
    confidence: float
    severity:   str
    feature_snapshot: dict


class ScoreRequest(BaseModel):
    host:         str
    window_size:  int = 100
    anomaly_type: str = "normal"   # "normal" | "ddos" for testing


class HealthResponse(BaseModel):
    status:    str
    model:     str
    threshold: float
    uptime_seconds: float