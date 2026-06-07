"""Two-layer MLP (MicroNN) — minimal neural network.

Pure Python with no ML framework dependencies. Supports:
* Xavier weight initialisation
* Forward pass with ReLU hidden + softmax output
* Backpropagation with SGD
* Serialisation to / from plain dicts
"""

from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional

from open_notebook.compute.stats import sigmoid, softmax


def _xavier(fan_in: int, fan_out: int) -> List[List[float]]:
    """Xavier/Glorot uniform initialisation."""
    limit = math.sqrt(6.0 / (fan_in + fan_out))
    return [
        [random.uniform(-limit, limit) for _ in range(fan_in)]
        for _ in range(fan_out)
    ]


class MicroNN:
    """A two-layer fully-connected neural network.

    Architecture: input → hidden (ReLU) → output (softmax).

    Parameters
    ----------
    input_size : int
        Number of input features.
    hidden_size : int
        Number of hidden units.
    output_size : int
        Number of output classes.
    learning_rate : float
        SGD learning rate.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int,
        output_size: int,
        learning_rate: float = 0.01,
    ):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.learning_rate = learning_rate

        # Weights: W1 is (hidden_size × input_size), W2 is (output_size × hidden_size)
        self.W1: List[List[float]] = []
        self.b1: List[float] = [0.0] * hidden_size
        self.W2: List[List[float]] = []
        self.b2: List[float] = [0.0] * output_size

        self._init_weights()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_weights(self) -> None:
        self.W1 = _xavier(self.input_size, self.hidden_size)
        self.W2 = _xavier(self.hidden_size, self.output_size)
        self.b1 = [0.0] * self.hidden_size
        self.b2 = [0.0] * self.output_size

    # ------------------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------------------

    @staticmethod
    def _mat_vec(W: List[List[float]], x: List[float], b: List[float]) -> List[float]:
        return [sum(wi * xi for wi, xi in zip(row, x)) + bi for row, bi in zip(W, b)]

    @staticmethod
    def _relu(x: List[float]) -> List[float]:
        return [max(0.0, v) for v in x]

    def forward(self, x: List[float]) -> Dict[str, List[float]]:
        """Run the forward pass, returning intermediate activations."""
        z1 = self._mat_vec(self.W1, x, self.b1)
        a1 = self._relu(z1)
        z2 = self._mat_vec(self.W2, a1, self.b2)
        a2 = softmax(z2)
        return {"z1": z1, "a1": a1, "z2": z2, "a2": a2}

    def predict(self, x: List[float]) -> int:
        """Return the predicted class index."""
        out = self.forward(x)["a2"]
        return out.index(max(out))

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train_step(self, x: List[float], y: int) -> float:
        """Single training step (forward + backprop). Returns cross-entropy loss."""
        fwd = self.forward(x)
        a1 = fwd["a1"]
        a2 = fwd["a2"]

        # Cross-entropy loss
        eps = 1e-12
        loss = -math.log(a2[y] + eps)

        # Output layer gradient (softmax + cross-entropy simplification)
        dz2 = list(a2)
        dz2[y] -= 1.0  # shape: (output_size,)

        # Gradients for W2 and b2
        for j in range(self.output_size):
            for k in range(self.hidden_size):
                self.W2[j][k] -= self.learning_rate * dz2[j] * a1[k]
            self.b2[j] -= self.learning_rate * dz2[j]

        # Hidden layer gradient (ReLU derivative)
        da1 = [
            sum(self.W2[j][k] * dz2[j] for j in range(self.output_size))
            for k in range(self.hidden_size)
        ]
        dz1 = [da1[k] * (1.0 if a1[k] > 0 else 0.0) for k in range(self.hidden_size)]

        # Gradients for W1 and b1
        for k in range(self.hidden_size):
            for i in range(self.input_size):
                self.W1[k][i] -= self.learning_rate * dz1[k] * x[i]
            self.b1[k] -= self.learning_rate * dz1[k]

        return loss

    def train_batch(
        self,
        X: List[List[float]],
        Y: List[int],
        epochs: int = 100,
    ) -> List[float]:
        """Train on a batch for *epochs* iterations. Returns per-epoch loss list."""
        losses: List[float] = []
        for _ in range(epochs):
            epoch_loss = 0.0
            for x, y in zip(X, Y):
                epoch_loss += self.train_step(x, y)
            losses.append(epoch_loss / len(X))
        return losses

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def serialize(self) -> Dict[str, Any]:
        return {
            "input_size": self.input_size,
            "hidden_size": self.hidden_size,
            "output_size": self.output_size,
            "learning_rate": self.learning_rate,
            "W1": self.W1,
            "b1": self.b1,
            "W2": self.W2,
            "b2": self.b2,
        }

    @classmethod
    def deserialize(cls, d: Dict[str, Any]) -> MicroNN:
        nn = cls(
            d["input_size"],
            d["hidden_size"],
            d["output_size"],
            d.get("learning_rate", 0.01),
        )
        nn.W1 = d["W1"]
        nn.b1 = d["b1"]
        nn.W2 = d["W2"]
        nn.b2 = d["b2"]
        return nn
