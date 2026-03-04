import math
from collections import Counter
from ingestion.schema import RawEvent
from features.schema import FeatureVector


def _entropy(values):
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((c / total) * math.log2(c / total) for c in counts.values())


def _std(values):
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def extract(events, host, window_seconds=60, prev_count=0.0):
    if not events:
        return _empty(host, window_seconds)

    total     = len(events)
    latencies = [e.latency_ms for e in events]
    payloads  = [e.payload_bytes for e in events]
    ips       = [e.ip_address for e in events]
    countries = [e.country_code for e in events]
    statuses  = [e.status_code for e in events]

    sorted_lat = sorted(latencies)
    p99_idx    = max(0, int(0.99 * len(sorted_lat)) - 1)

    return FeatureVector(
        host=host,
        window_seconds=window_seconds,
        req_count=float(total),
        req_rate_delta=float(total - prev_count),
        unique_ips=float(len(set(ips))),
        ip_entropy=_entropy(ips),
        error_ratio=sum(1 for s in statuses if s >= 400) / total,
        rate_429=sum(1 for s in statuses if s == 429) / total,
        rate_500=sum(1 for s in statuses if s == 500) / total,
        success_ratio=sum(1 for s in statuses if s < 400) / total,
        latency_mean=sum(latencies) / total,
        latency_p99=sorted_lat[p99_idx],
        latency_std=_std(latencies),
        latency_min=min(latencies),
        payload_mean=sum(payloads) / total,
        payload_std=_std(payloads),
        payload_max=float(max(payloads)),
        unique_countries=float(len(set(countries))),
        country_entropy=_entropy(countries),
    )


def _empty(host, window_seconds):
    return FeatureVector(
        host=host, window_seconds=window_seconds,
        req_count=0, req_rate_delta=0, unique_ips=0, ip_entropy=0,
        error_ratio=0, rate_429=0, rate_500=0, success_ratio=0,
        latency_mean=0, latency_p99=0, latency_std=0, latency_min=0,
        payload_mean=0, payload_std=0, payload_max=0,
        unique_countries=0, country_entropy=0,
    )