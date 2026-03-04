import torch
import torch.nn as nn
import os
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


def generate_training_data(n_windows=500, window_size=100):
    print(f"Generating {n_windows} normal windows...")
    vectors = []
    for i in range(n_windows):
        events = [make_normal_event("server-01") for _ in range(window_size)]
        fv     = extract(events, "server-01")
        vectors.append(fv.to_vector())
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n_windows} windows done")
    return vectors


def train(epochs=50, lr=0.001):
    os.makedirs("model/artifacts", exist_ok=True)

    raw_vecs   = generate_training_data()
    normalizer = MinMaxNormalizer()
    normalizer.fit(raw_vecs, FEATURE_NAMES)
    normalizer.save("model/artifacts/scaler.json")

    norm_vecs = [normalizer.transform(v, FEATURE_NAMES) for v in raw_vecs]
    X         = torch.tensor(norm_vecs, dtype=torch.float32).unsqueeze(1)

    split   = int(0.8 * len(X))
    X_train = X[:split]
    X_val   = X[split:]

    model     = LSTMAutoencoder(input_dim=17)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    print("Training autoencoder...")
    best_val = float("inf")

    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        out, _ = model(X_train)
        loss   = nn.MSELoss()(out, X_train)
        loss.backward()
        optimizer.step()

        model.eval()
        with torch.no_grad():
            out_val, _ = model(X_val)
            val_loss   = nn.MSELoss()(out_val, X_val).item()

        if val_loss < best_val:
            best_val = val_loss
            torch.save(model.state_dict(), "model/artifacts/model.pt")

        if (epoch + 1) % 10 == 0:
            print(f"  epoch {epoch+1}/{epochs}  train={loss.item():.6f}  val={val_loss:.6f}")

    print(f"Done. Best val loss: {best_val:.6f}")
    print("Saved → model/artifacts/model.pt")
    print("Saved → model/artifacts/scaler.json")


if __name__ == "__main__":
    train()