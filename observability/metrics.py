from prometheus_client import Gauge, Counter, Histogram, start_http_server

# Reconstruction error per host
RECONSTRUCTION_ERROR = Gauge(
    "streamsentinel_reconstruction_error",
    "Autoencoder reconstruction error score",
    ["host"]
)

# Alert counters
ALERTS_TOTAL = Counter(
    "streamsentinel_alerts_total",
    "Total anomaly alerts fired",
    ["host", "severity"]
)

# Events processed
EVENTS_PROCESSED = Counter(
    "streamsentinel_events_processed_total",
    "Total events processed by inference worker",
    ["host"]
)

# Window score distribution
SCORE_HISTOGRAM = Histogram(
    "streamsentinel_score_distribution",
    "Distribution of reconstruction error scores",
    buckets=[0.05, 0.09, 0.1, 0.2, 0.5, 1.0, 5.0, 50.0, 200.0, 600.0]
)

# Is currently under attack (1 = yes, 0 = no)
ANOMALY_ACTIVE = Gauge(
    "streamsentinel_anomaly_active",
    "Whether an anomaly is currently active",
    ["host"]
)


def start_metrics_server(port: int = 8001):
    start_http_server(port)
    print(f"Prometheus metrics exposed on :{port}/metrics")