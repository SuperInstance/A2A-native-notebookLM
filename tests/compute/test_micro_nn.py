"""Tests for MicroNN — two-layer MLP."""

import pytest

from open_notebook.compute.micro_nn import MicroNN


class TestMicroNN:
    def test_init(self):
        nn = MicroNN(3, 5, 2)
        assert nn.input_size == 3
        assert nn.hidden_size == 5
        assert nn.output_size == 2
        assert len(nn.W1) == 5
        assert len(nn.W1[0]) == 3
        assert len(nn.W2) == 2
        assert len(nn.W2[0]) == 5

    def test_forward_shapes(self):
        nn = MicroNN(3, 5, 2)
        fwd = nn.forward([1.0, 2.0, 3.0])
        assert len(fwd["a1"]) == 5
        assert len(fwd["a2"]) == 2
        # Softmax sums to ~1
        assert abs(sum(fwd["a2"]) - 1.0) < 1e-6

    def test_predict(self):
        nn = MicroNN(2, 4, 3)
        pred = nn.predict([0.5, 0.5])
        assert isinstance(pred, int)
        assert 0 <= pred < 3

    def test_train_step_reduces_loss(self):
        nn = MicroNN(2, 8, 2, learning_rate=0.1)
        x = [1.0, 0.0]
        y = 1
        losses = [nn.train_step(x, y) for _ in range(50)]
        # Loss should generally decrease
        assert losses[-1] < losses[0]

    def test_train_batch(self):
        nn = MicroNN(2, 8, 2, learning_rate=0.1)
        X = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0], [0.0, 0.0]]
        Y = [1, 0, 1, 0]
        losses = nn.train_batch(X, Y, epochs=50)
        assert len(losses) == 50
        assert losses[-1] < losses[0]

    def test_serialize_deserialize(self):
        nn = MicroNN(2, 4, 3, learning_rate=0.05)
        x = [1.0, 2.0]
        pred1 = nn.predict(x)

        d = nn.serialize()
        assert d["input_size"] == 2

        nn2 = MicroNN.deserialize(d)
        pred2 = nn2.predict(x)
        assert pred1 == pred2

    def test_weights_change_after_training(self):
        nn = MicroNN(2, 4, 2, learning_rate=0.1)
        w_before = [row[:] for row in nn.W1]
        nn.train_step([1.0, 0.0], 1)
        assert nn.W1 != w_before
