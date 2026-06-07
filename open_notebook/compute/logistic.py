"""Logistic regression — binary classifier.

Pure Python implementation with sigmoid activation, cross-entropy loss,
and gradient descent optimisation.
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Sequence

from open_notebook.compute.stats import sigmoid


class LogisticRegression:
    """Binary logistic regression classifier.

    Parameters
    ----------
    learning_rate : float
        Step size for gradient descent.
    epochs : int
        Number of training iterations over the full dataset.
    """

    def __init__(self, learning_rate: float = 0.01, epochs: int = 100):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.weights: List[float] = []
        self.bias: float = 0.0
        self._fitted = False

    # ------------------------------------------------------------------
    # Prediction
    # ------------------------------------------------------------------

    def _z(self, x: Sequence[float]) -> float:
        """Linear combination: w·x + b."""
        return sum(w * xi for w, xi in zip(self.weights, x)) + self.bias

    def predict_proba(self, x: Sequence[float]) -> float:
        """Probability of the positive class."""
        return sigmoid(self._z(x))

    def predict(self, x: Sequence[float]) -> int:
        """Predict class label (0 or 1)."""
        return 1 if self.predict_proba(x) >= 0.5 else 0

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, X: Sequence[Sequence[float]], Y: Sequence[int]) -> List[float]:
        """Train the model. Returns per-epoch loss list."""
        n_features = len(X[0])
        self.weights = [random.gauss(0, 0.01) for _ in range(n_features)]
        self.bias = 0.0
        self._fitted = True

        n = len(X)
        losses: List[float] = []

        for _ in range(self.epochs):
            grad_w = [0.0] * n_features
            grad_b = 0.0
            epoch_loss = 0.0

            for x, y in zip(X, Y):
                p = self.predict_proba(x)
                eps = 1e-12
                epoch_loss += -(y * math.log(p + eps) + (1 - y) * math.log(1 - p + eps))

                diff = p - y
                for j in range(n_features):
                    grad_w[j] += diff * x[j]
                grad_b += diff

            # Update
            for j in range(n_features):
                self.weights[j] -= self.learning_rate * grad_w[j] / n
            self.bias -= self.learning_rate * grad_b / n

            losses.append(epoch_loss / n)

        return losses

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> Dict[str, Any]:
        return {
            "weights": self.weights,
            "bias": self.bias,
            "learning_rate": self.learning_rate,
            "epochs": self.epochs,
        }

    @classmethod
    def deserialize(cls, d: Dict[str, Any]) -> LogisticRegression:
        model = cls(
            learning_rate=d.get("learning_rate", 0.01),
            epochs=d.get("epochs", 100),
        )
        model.weights = d["weights"]
        model.bias = d["bias"]
        model._fitted = True
        return model
