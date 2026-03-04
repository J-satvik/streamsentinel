import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket
from api.routes import router
from api.websocket import stream_anomalies
from api.deps import get_scorer

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # warm up model on startup
    get_scorer()
    print("Model loaded and ready")
    yield


app = FastAPI(
    title="StreamSentinel",
    description="Real-time anomaly detection API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await stream_anomalies(websocket)


@app.get("/")
def root():
    return {
        "service": "StreamSentinel",
        "docs":    "/docs",
        "health":  "/api/v1/health",
        "stream":  "ws://localhost:8000/ws/stream",
    }