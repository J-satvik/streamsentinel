from pydantic import BaseModel, Field
from datetime import datetime


class FeatureVector(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    host: str
    window_seconds: int
    req_count: float
    req_rate_delta: float
    unique_ips: float
    ip_entropy: float
    error_ratio: float
    rate_429: float
    rate_500: float
    success_ratio: float
    latency_mean: float
    latency_p99: float
    latency_std: float
    latency_min: float
    payload_mean: float
    payload_std: float
    payload_max: float
    unique_countries: float
    country_entropy: float

    def to_vector(self):
        return [
            self.req_count, self.req_rate_delta, self.unique_ips, self.ip_entropy,
            self.error_ratio, self.rate_429, self.rate_500, self.success_ratio,
            self.latency_mean, self.latency_p99, self.latency_std, self.latency_min,
            self.payload_mean, self.payload_std, self.payload_max,
            self.unique_countries, self.country_entropy,
        ]