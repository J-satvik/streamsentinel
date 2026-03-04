import asyncio
import random
from fastapi import WebSocket, WebSocketDisconnect
from ingestion.log_simulator import make_normal_event, make_ddos_event
from inference.scorer import Scorer
from api.deps import get_scorer
from api.models import AlertResponse


async def stream_anomalies(websocket: WebSocket):
    scorer = get_scorer()
    await websocket.accept()

    try:
        while True:
            # randomly inject a DDoS burst every ~10 windows
            is_attack = random.random() < 0.15
            host      = random.choice(["server-01", "server-02", "server-03"])

            if is_attack:
                events = [make_ddos_event(host) for _ in range(100)]
            else:
                events = [make_normal_event(host) for _ in range(100)]

            alert = scorer.evaluate(events, host)

            if alert:
                payload = AlertResponse(
                    host=alert.host,
                    timestamp=alert.timestamp,
                    score=alert.score,
                    threshold=alert.threshold,
                    confidence=alert.confidence,
                    severity=alert.severity,
                    feature_snapshot=alert.feature_snapshot,
                )
                await websocket.send_text(payload.model_dump_json())

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        pass