import torch
import json
import numpy as np
from ingestion.log_simulator import make_normal_event
from features.extractor import extract
from features.normalizer import MinMaxNormalizer
from model.autoencoder import LSTMAutoencoder

FEATURE_NAMES = [
    "req_count", "req_rate_delta", "unique_ips", "ip_entropy",
    "error_ratio", "rate_429", "rate_500", "success_ratio",
    "latency_mean", "latency_p99", "latency_std", "latency_min",
    "payload_mean", "payload_std", "payload_max",
    "unique_countries", "country_entropy",
]


def calibrate(percentile=95):
    normalizer = MinMaxNormalizer()
    normalizer.load("model/artifacts/scaler.json")

    model = LSTMAutoencoder(input_dim=17)
    model.load_state_dict(torch.load("model/artifacts/model.pt", weights_only=True))
    model.eval()

    print("Calibrating threshold on 200 normal windows...")
    errors = []
    for i in range(200):
        events = [make_normal_event("server-01") for _ in range(100)]
        fv     = extract(events, "server-01")
        vec    = normalizer.transform(fv.to_vector(), FEATURE_NAMES)
        x      = torch.tensor(vec, dtype=torch.float32).unsqueeze(0).unsqueeze(0)
        with torch.no_grad():
            err = model.reconstruction_error(x).item()
        errors.append(err)
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/200 done")

    threshold = float(np.percentile(errors, percentile))
    result = {
        "threshold": threshold,
        "percentile": percentile,
        "mean_error": float(np.mean(errors)),
        "max_error":  float(np.max(errors)),
    }

    with open("model/artifacts/threshold.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"Threshold P{percentile}: {threshold:.6f}")
    print(f"Mean error:             {result['mean_error']:.6f}")
    print("Saved → model/artifacts/threshold.json")
    return threshold


if __name__ == "__main__":
    calibrate() 