"""Compute engine orchestrator.

Coordinates training, prediction, and model persistence. Models are
stored in-memory by default; in production they would be persisted to
SurrealDB via the domain layer.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from open_notebook.compute.kmeans import KMeans
from open_notebook.compute.logistic import LogisticRegression
from open_notebook.compute.micro_nn import MicroNN

# ---------------------------------------------------------------------------
# Model registry (in-memory)
# ---------------------------------------------------------------------------

_model_store: Dict[str, Any] = {}


def _model_key(notebook_id: str, model_type: str) -> str:
    return f"{notebook_id}:{model_type}"


class ComputeEngine:
    """Orchestrates ML training and inference for notebooks."""

    # Supported model types
    MODEL_TYPES = {
        "micro_nn": MicroNN,
        "logistic": LogisticRegression,
        "kmeans": KMeans,
    }

    def train(
        self,
        notebook_id: str,
        model_type: str,
        params: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Train a model and return a training report.

        For now this is a stub that creates a model with default params
        so the protocol layer can be tested end-to-end.
        """
        start = time.time()
        key = _model_key(notebook_id, model_type)

        # Stub training data from params if provided
        X = params.get("X", [[0.0, 0.0], [1.0, 1.0]])
        Y = params.get("Y", [0, 1])
        epochs = params.get("epochs", 50)

        if model_type == "micro_nn":
            input_size = len(X[0])
            hidden_size = params.get("hidden_size", 4)
            output_size = params.get("output_size", 2)
            model = MicroNN(input_size, hidden_size, output_size)
            losses = model.train_batch(X, Y, epochs=epochs)
            _model_store[key] = model
            elapsed = time.time() - start
            return {
                "model_type": "micro_nn",
                "input_size": input_size,
                "hidden_size": hidden_size,
                "output_size": output_size,
                "epochs": epochs,
                "final_loss": losses[-1] if losses else 0,
                "elapsed_ms": int(elapsed * 1000),
            }

        elif model_type == "logistic":
            model = LogisticRegression(
                learning_rate=params.get("learning_rate", 0.1),
                epochs=epochs,
            )
            losses = model.train(X, Y)
            _model_store[key] = model
            elapsed = time.time() - start
            return {
                "model_type": "logistic",
                "epochs": epochs,
                "final_loss": losses[-1] if losses else 0,
                "n_features": len(X[0]),
                "elapsed_ms": int(elapsed * 1000),
            }

        elif model_type == "kmeans":
            k = params.get("k", 3)
            model = KMeans(k=k)
            assignments = model.fit(X)
            _model_store[key] = model
            elapsed = time.time() - start
            return {
                "model_type": "kmeans",
                "k": k,
                "assignments": assignments,
                "elapsed_ms": int(elapsed * 1000),
            }

        else:
            raise ValueError(f"Unknown model type: {model_type}")

    def predict(
        self,
        notebook_id: str,
        model_type: str,
        input_data: Any,
    ) -> Dict[str, Any]:
        """Run inference with a trained model."""
        key = _model_key(notebook_id, model_type)
        model = _model_store.get(key)
        if model is None:
            return {"error": f"No trained model for {key}", "prediction": None}

        if isinstance(model, MicroNN):
            pred = model.predict(input_data)
            probs = model.forward(input_data)["a2"]
            return {"class": pred, "probabilities": probs}

        elif isinstance(model, LogisticRegression):
            prob = model.predict_proba(input_data)
            label = model.predict(input_data)
            return {"label": label, "probability": prob}

        elif isinstance(model, KMeans):
            cluster = model.predict(input_data)
            return {"cluster": cluster}

        return {"error": "Unknown model instance type"}

    def get_model(self, notebook_id: str, model_type: str) -> Any:
        """Retrieve a trained model instance."""
        return _model_store.get(_model_key(notebook_id, model_type))

    def save_model(self, notebook_id: str, model_type: str, model: Any) -> None:
        """Store a model in the registry."""
        _model_store[_model_key(notebook_id, model_type)] = model

    def load_or_train(
        self,
        notebook_id: str,
        model_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Load a cached model or train a new one."""
        model = self.get_model(notebook_id, model_type)
        if model is not None:
            return model
        self.train(notebook_id, model_type, params or {})
        return self.get_model(notebook_id, model_type)
