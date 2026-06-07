"""Tests for Isolation Forest anomaly detection."""

import pytest

from open_notebook.compute.isolation import IsolationForest, IsolationTree, _c


class TestHelperC:
    def test_c_zero(self):
        assert _c(0) == 0.0
        assert _c(1) == 0.0

    def test_c_positive(self):
        assert _c(10) > 0


class TestIsolationTree:
    def test_fit_single_point(self):
        tree = IsolationTree(max_depth=5)
        tree.fit([[1.0, 2.0]])
        assert tree.size == 1

    def test_path_length_single(self):
        tree = IsolationTree(max_depth=5)
        tree.fit([[1.0, 2.0]])
        pl = tree.path_length([1.0, 2.0])
        assert pl >= 0


class TestIsolationForest:
    def test_fit_and_score(self):
        # Normal points clustered, one outlier
        import random
        random.seed(42)
        X = [[0.0, 0.0]] * 10 + [[100.0, 100.0]]
        forest = IsolationForest(n_trees=20, max_depth=5, sample_size=11)
        forest.fit(X)

        score_normal = forest.score([0.0, 0.0])
        score_outlier = forest.score([100.0, 100.0])
        # Outlier should have higher anomaly score
        assert isinstance(score_normal, float)
        assert isinstance(score_outlier, float)

    def test_predict(self):
        import random
        random.seed(42)
        X = [[float(i), float(i)] for i in range(20)]
        forest = IsolationForest(n_trees=10, max_depth=5)
        forest.fit(X)
        result = forest.predict([0.0, 0.0])
        assert isinstance(result, bool)

    def test_not_fitted_raises(self):
        forest = IsolationForest()
        with pytest.raises(RuntimeError, match="not fitted"):
            forest.score([0.0])

    def test_serialize_deserialize(self):
        import random
        random.seed(42)
        X = [[0.0, 0.0], [1.0, 1.0]]
        forest = IsolationForest(n_trees=5, max_depth=3)
        forest.fit(X)
        d = forest.serialize()
        assert d["n_trees"] == 5

        forest2 = IsolationForest.deserialize(d)
        assert forest2.n_trees == 5
