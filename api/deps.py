from functools import lru_cache
from inference.engine import InferenceEngine
from inference.scorer import Scorer


@lru_cache(maxsize=1)
def get_engine() -> InferenceEngine:
    return InferenceEngine()


@lru_cache(maxsize=1)
def get_scorer() -> Scorer:
    return Scorer(get_engine())