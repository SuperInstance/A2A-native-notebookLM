"""Compute engine — pure-Python ML algorithms for the exocortex."""

from open_notebook.compute.stats import (
    cosine_similarity,
    euclidean_distance,
    mean,
    sigmoid,
    softmax,
    standardize,
    std_dev,
    variance,
)
from open_notebook.compute.engine import ComputeEngine

__all__ = [
    "mean",
    "variance",
    "std_dev",
    "standardize",
    "euclidean_distance",
    "cosine_similarity",
    "sigmoid",
    "softmax",
    "ComputeEngine",
]
