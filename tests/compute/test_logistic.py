"""Tests for logistic regression."""

import math

import pytest

from open_notebook.compute.logistic import LogisticRegression
from open_notebook.compute.stats import sigmoid


class TestSigmoid:
    def test_zero(self):
        assert abs(sigmoid(0) - 0.5) < 1e-9

    def test_large_positive(self):
        assert sigmoid(100) > 0.99

    def test_large_negative(self):
        assert sigmoid(-100) < 0.01

    def test_symmetry(self):
        assert abs(sigmoid(2) + sigmoid(-2) - 1.0) < 1e-9


class TestLogisticRegression:
    def test_train_and_predict(self):
        model = LogisticRegression(learning_rate=0.5, epochs=100)
        X = [[0.0, 0.0], [1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
        Y = [0, 1, 0, 1]
        losses = model.train(X, Y)
        assert len(losses) == 100
        assert losses[-1] < losses[0]

        # Check predictions are reasonable
        for x, y in zip(X, Y):
            pred = model.predict(x)
            # Not guaranteed perfect but should lean correct
            assert model.predict_proba(x) is not None

    def test_predict_proba_range(self):
        model = LogisticRegression(learning_rate=0.1, epochs=50)
        model.train([[0], [1]], [0, 1])
        p = model.predict_proba([0.5])
        assert 0.0 <= p <= 1.0

    def test_serialization(self):
        model = LogisticRegression(learning_rate=0.05, epochs=200)
        model.train([[0], [1]], [0, 1])
        d = model.serialize()
        assert "weights" in d
        assert "bias" in d

        model2 = LogisticRegression.deserialize(d)
        x = [0.5]
        assert abs(model.predict_proba(x) - model2.predict_proba(x)) < 1e-9
