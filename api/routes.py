import time
from fastapi import APIRouter, Depends
from ingestion.log_simulator import make_normal_event, make_ddos_event
from inference.scorer import Scorer
from api.deps import get_scorer
from api.models import AlertResponse, ScoreRequest, HealthResponse

router     = APIRouter()
START_TIME = time.time()


@router.get("/health", response_model=HealthResponse)
def health(scorer: Scorer = Depends(get_scorer)):
    return HealthResponse(
        status="ok",
        model="LSTMAutoencoder",
        threshold=scorer.engine.threshold,
        uptime_seconds=round(time.time() - START_TIME, 1),
    )


@router.post("/score", response_model=AlertResponse | None)
def score(req: ScoreRequest, scorer: Scorer = Depends(get_scorer)):
    if req.anomaly_type == "ddos":
        events = [make_ddos_event(req.host) for _ in range(req.window_size)]
    else:
        events = [make_normal_event(req.host) for _ in range(req.window_size)]

    alert = scorer.evaluate(events, req.host)

    if alert is None:
        return None

    return AlertResponse(
        host=alert.host,
        timestamp=alert.timestamp,
        score=alert.score,
        threshold=alert.threshold,
        confidence=alert.confidence,
        severity=alert.severity,
        feature_snapshot=alert.feature_snapshot,
    )