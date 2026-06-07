"""Isolation Forest for anomaly detection.

Pure Python implementation using random isolation trees.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence


class IsolationTree:
    """A single isolation tree.

    Randomly selects a feature and split value until the node is a leaf
    (single sample or max depth reached).
    """

    def __init__(self, max_depth: int = 10):
        self.max_depth = max_depth
        self.split_feature: int = -1
        self.split_value: float = 0.0
        self.left: Optional[IsolationTree] = None
        self.right: Optional[IsolationTree] = None
        self.size: int = 0  # number of samples at leaf
        self.depth: int = 0

    def fit(self, X: Sequence[Sequence[float]], depth: int = 0) -> None:
        self.depth = depth
        self.size = len(X)

        if len(X) <= 1 or depth >= self.max_depth:
            return

        n_features = len(X[0])
        # Pick a random feature
        self.split_feature = random.randint(0, n_features - 1)

        values = [x[self.split_feature] for x in X]
        min_v, max_v = min(values), max(values)

        if min_v == max_v:
            return

        self.split_value = random.uniform(min_v, max_v)

        left_X = [x for x in X if x[self.split_feature] < self.split_value]
        right_X = [x for x in X if x[self.split_feature] >= self.split_value]

        if not left_X or not right_X:
            return

        self.left = IsolationTree(max_depth=self.max_depth)
        self.right = IsolationTree(max_depth=self.max_depth)
        self.left.fit(left_X, depth + 1)
        self.right.fit(right_X, depth + 1)

    def path_length(self, x: Sequence[float]) -> float:
        """Return the path length for a single sample."""
        if self.left is None or self.right is None:
            # Leaf node
            return self.depth + _c(self.size)

        if x[self.split_feature] < self.split_value:
            return self.left.path_length(x)
        return self.right.path_length(x)


def _c(n: int) -> float:
    """Average path length of an unsuccessful BST search with n elements."""
    if n <= 1:
        return 0.0
    return 2.0 * (math.log(n - 1) + 0.5772156649) - 2.0 * (n - 1) / n


class IsolationForest:
    """Isolation Forest anomaly detector.

    Parameters
    ----------
    n_trees : int
        Number of isolation trees.
    max_depth : int
        Maximum depth of each tree.
    sample_size : int
        Number of samples drawn to train each tree.
    """

    def __init__(
        self,
        n_trees: int = 100,
        max_depth: int = 10,
        sample_size: int = 256,
    ):
        self.n_trees = n_trees
        self.max_depth = max_depth
        self.sample_size = sample_size
        self.trees: List[IsolationTree] = []
        self._n_samples: int = 0

    def fit(self, X: Sequence[Sequence[float]]) -> None:
        """Build the isolation forest."""
        self._n_samples = len(X)
        self.trees = []
        sample_size = min(self.sample_size, len(X))

        for _ in range(self.n_trees):
            sample = random.sample(list(X), sample_size)
            tree = IsolationTree(max_depth=self.max_depth)
            tree.fit(sample)
            self.trees.append(tree)

    def score(self, x: Sequence[float]) -> float:
        """Compute the anomaly score for a single sample.

        Scores close to 1 indicate anomalies; scores close to 0 indicate normal.
        """
        if not self.trees:
            raise RuntimeError("Model not fitted yet")

        avg_path = sum(tree.path_length(x) for tree in self.trees) / len(self.trees)
        c_val = _c(self._n_samples)
        if c_val == 0:
            return 0.0
        return 2.0 ** (-avg_path / c_val)

    def predict(self, x: Sequence[float], threshold: float = 0.6) -> bool:
        """Return True if the sample is anomalous."""
        return self.score(x) >= threshold

    def serialize(self) -> Dict[str, Any]:
        return {
            "n_trees": self.n_trees,
            "max_depth": self.max_depth,
            "sample_size": self.sample_size,
            "n_samples": self._n_samples,
        }

    @classmethod
    def deserialize(cls, d: Dict[str, Any]) -> IsolationForest:
        model = cls(
            n_trees=d["n_trees"],
            max_depth=d.get("max_depth", 10),
            sample_size=d.get("sample_size", 256),
        )
        model._n_samples = d.get("n_samples", 0)
        return model
