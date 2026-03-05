# StreamSentinel 🛡️

Real-time anomaly detection pipeline using Kafka, PyTorch, FastAPI, and Grafana.

## What it does
Ingests server logs via Kafka, extracts features, runs them through an LSTM Autoencoder, 
and flags anomalies (DDoS, fraud, server failures) in real time.

## Tech Stack
- **Python 3.11** — core language
- **Apache Kafka** — event streaming
- **PyTorch** — LSTM Autoencoder model
- **FastAPI** — REST + WebSocket API
- **Grafana + Prometheus** — observability
- **Docker** — infrastructure

## Quick Start
```bash
# 1. Start infrastructure
docker compose up -d

# 2. Train the model (first time only)
python -m model.train
python -m model.threshold

# 3. Run all services (separate terminals)
python -m ingestion.log_simulator
python -m uvicorn api.main:app --reload --port 8000
python -m inference.worker
```

## Results
- Normal traffic scores: 0.04 – 0.07 (below threshold 0.089)
- DDoS traffic scores: 606+ (6,000x above threshold)
- Detection confidence: 100% on simulated attacks
