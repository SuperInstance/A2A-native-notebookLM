"""Pure-math statistical functions.

No external dependencies — everything is plain Python for portability.
"""

from __future__ import annotations

import math
from typing import List, Sequence


def mean(data: Sequence[float]) -> float:
    """Arithmetic mean."""
    if not data:
        raise ValueError("mean requires at least one data point")
    return sum(data) / len(data)


def variance(data: Sequence[float]) -> float:
    """Population variance."""
    m = mean(data)
    return sum((x - m) ** 2 for x in data) / len(data)


def std_dev(data: Sequence[float]) -> float:
    """Population standard deviation."""
    return math.sqrt(variance(data))


def standardize(data: Sequence[float]) -> List[float]:
    """Z-score standardization (mean=0, std=1)."""
    m = mean(data)
    s = std_dev(data)
    if s == 0:
        return [0.0] * len(data)
    return [(x - m) / s for x in data]


def euclidean_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """Euclidean distance between two vectors."""
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length")
    return math.sqrt(sum((ai - bi) ** 2 for ai, bi in zip(a, b)))


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """Cosine similarity between two vectors.

    Returns 0.0 when either vector has zero magnitude.
    """
    if len(a) != len(b):
        raise ValueError("Vectors must have the same length")
    dot = sum(ai * bi for ai, bi in zip(a, b))
    mag_a = math.sqrt(sum(ai * ai for ai in a))
    mag_b = math.sqrt(sum(bi * bi for bi in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def sigmoid(x: float) -> float:
    """Standard sigmoid function."""
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    z = math.exp(x)
    return z / (1.0 + z)


def softmax(x: Sequence[float]) -> List[float]:
    """Numerically stable softmax."""
    if not x:
        return []
    max_x = max(x)
    exps = [math.exp(xi - max_x) for xi in x]
    total = sum(exps)
    return [e / total for e in exps]
