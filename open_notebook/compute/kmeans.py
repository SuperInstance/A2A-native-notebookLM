"""K-Means clustering with k-means++ initialisation.

Pure Python implementation.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Sequence

from open_notebook.compute.stats import euclidean_distance


class KMeans:
    """K-Means clustering.

    Parameters
    ----------
    k : int
        Number of clusters.
    max_iters : int
        Maximum number of iterations.
    """

    def __init__(self, k: int = 3, max_iters: int = 100):
        self.k = k
        self.max_iters = max_iters
        self.centroids: List[List[float]] = []
        self._fitted = False

    # ------------------------------------------------------------------
    # K-means++ initialisation
    # ------------------------------------------------------------------

    def _kmeans_pp_init(self, X: Sequence[Sequence[float]]) -> List[List[float]]:
        """Initialise centroids using k-means++ algorithm."""
        centroids = [list(random.choice(X))]

        for _ in range(1, self.k):
            # Compute squared distances to nearest centroid
            dists = []
            for x in X:
                min_d = min(euclidean_distance(x, c) ** 2 for c in centroids)
                dists.append(min_d)

            total = sum(dists)
            if total == 0:
                # All points coincide with centroids
                centroids.append(list(random.choice(X)))
                continue

            # Weighted random selection
            probs = [d / total for d in dists]
            r = random.random()
            cumsum = 0.0
            for i, p in enumerate(probs):
                cumsum += p
                if r <= cumsum:
                    centroids.append(list(X[i]))
                    break
            else:
                centroids.append(list(X[-1]))

        return centroids

    # ------------------------------------------------------------------
    # Fit / predict
    # ------------------------------------------------------------------

    def fit(self, X: Sequence[Sequence[float]]) -> List[int]:
        """Fit the model to data. Returns cluster assignments."""
        if len(X) < self.k:
            raise ValueError("Need at least k data points")

        self.centroids = self._kmeans_pp_init(X)
        assignments = [0] * len(X)

        for _ in range(self.max_iters):
            # Assign each point to nearest centroid
            new_assignments = []
            for x in X:
                dists = [euclidean_distance(x, c) for c in self.centroids]
                new_assignments.append(dists.index(min(dists)))

            # Check convergence
            if new_assignments == assignments:
                assignments = new_assignments
                break
            assignments = new_assignments

            # Update centroids
            for ci in range(self.k):
                members = [X[i] for i in range(len(X)) if assignments[i] == ci]
                if members:
                    n = len(members[0])
                    self.centroids[ci] = [
                        sum(m[d] for m in members) / len(members) for d in range(n)
                    ]

        self._fitted = True
        return assignments

    def predict(self, x: Sequence[float]) -> int:
        """Predict the cluster for a single point."""
        if not self._fitted:
            raise RuntimeError("Model not fitted yet")
        dists = [euclidean_distance(x, c) for c in self.centroids]
        return dists.index(min(dists))

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> Dict[str, Any]:
        return {
            "k": self.k,
            "max_iters": self.max_iters,
            "centroids": self.centroids,
        }

    @classmethod
    def deserialize(cls, d: Dict[str, Any]) -> KMeans:
        model = cls(k=d["k"], max_iters=d.get("max_iters", 100))
        model.centroids = d["centroids"]
        model._fitted = True
        return model
