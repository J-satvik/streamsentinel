import torch
import json
from features.normalizer import MinMaxNormalizer
from model.autoencoder import LSTMAutoencoder

FEATURE_NAMES = [
    "req_count", "req_rate_delta", "unique_ips", "ip_entropy",
    "error_ratio", "rate_429", "rate_500", "success_ratio",
    "latency_mean", "latency_p99", "latency_std", "latency_min",
    "payload_mean", "payload_std", "payload_max",
    "unique_countries", "country_entropy",
]


class InferenceEngine:
    def __init__(
        self,
        model_path="model/artifacts/model.pt",
        scaler_path="model/artifacts/scaler.json",
        threshold_path="model/artifacts/threshold.json",
    ):
        self.normalizer = MinMaxNormalizer()
        self.normalizer.load(scaler_path)

        self.model = LSTMAutoencoder(input_dim=17)
        self.model.load_state_dict(torch.load(model_path, weights_only=True))
        self.model.eval()

        with open(threshold_path) as f:
            data = json.load(f)
        self.threshold = data["threshold"]

    def score(self, feature_vector: list[float]) -> dict:
        vec = self.normalizer.transform(feature_vector, FEATURE_NAMES)
        x   = torch.tensor(vec, dtype=torch.float32).unsqueeze(0).unsqueeze(0)

        with torch.no_grad():
            error = self.model.reconstruction_error(x).item()

        is_anomaly = error > self.threshold
        confidence = min(error / self.threshold, 10.0) / 10.0  # 0-1 scale

        return {
            "score":      round(error, 6),
            "threshold":  round(self.threshold, 6),
            "is_anomaly": is_anomaly,
            "confidence": round(confidence, 4),
        }