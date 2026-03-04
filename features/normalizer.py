import json
import os


class MinMaxNormalizer:
    def __init__(self):
        self.mins = {}
        self.maxs = {}

    def fit(self, vectors, feature_names):
        for i, name in enumerate(feature_names):
            vals = [v[i] for v in vectors]
            self.mins[name] = min(vals)
            self.maxs[name] = max(vals)

    def transform(self, vector, feature_names):
        result = []
        for i, name in enumerate(feature_names):
            mn  = self.mins.get(name, 0)
            mx  = self.maxs.get(name, 1)
            den = mx - mn if mx != mn else 1
            result.append((vector[i] - mn) / den)
        return result

    def save(self, path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump({'mins': self.mins, 'maxs': self.maxs}, f)

    def load(self, path):
        with open(path) as f:
            data = json.load(f)
        self.mins = data['mins']
        self.maxs = data['maxs']