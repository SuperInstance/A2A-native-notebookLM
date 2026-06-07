"""Tests for K-Means clustering."""

import pytest

from open_notebook.compute.kmeans import KMeans


class TestKMeans:
    def test_basic_clustering(self):
        # Two clearly separated clusters
        X = [[0.0, 0.0], [0.1, 0.1], [10.0, 10.0], [10.1, 10.1]]
        model = KMeans(k=2, max_iters=50)
        labels = model.fit(X)
        assert len(labels) == 4
        # Points in same cluster should have same label
        assert labels[0] == labels[1]
        assert labels[2] == labels[3]
        assert labels[0] != labels[2]

    def test_predict_after_fit(self):
        X = [[0.0, 0.0], [0.1, 0.1], [10.0, 10.0], [10.1, 10.1]]
        model = KMeans(k=2, max_iters=50)
        model.fit(X)
        cluster = model.predict([0.0, 0.0])
        assert isinstance(cluster, int)
        assert 0 <= cluster < 2

    def test_predict_before_fit_raises(self):
        model = KMeans(k=2)
        with pytest.raises(RuntimeError, match="not fitted"):
            model.predict([0.0])

    def test_too_few_points_raises(self):
        model = KMeans(k=3)
        with pytest.raises(ValueError, match="at least k"):
            model.fit([[0.0], [1.0]])

    def test_serialization(self):
        X = [[0.0, 0.0], [10.0, 10.0]]
        model = KMeans(k=2, max_iters=10)
        model.fit(X)
        d = model.serialize()
        assert d["k"] == 2
        assert len(d["centroids"]) == 2

        model2 = KMeans.deserialize(d)
        assert model2.predict([0.0, 0.0]) == model.predict([0.0, 0.0])

    def test_kmeans_pp_init(self):
        X = [[float(i)] for i in range(20)]
        model = KMeans(k=5, max_iters=1)
        centroids = model._kmeans_pp_init(X)
        assert len(centroids) == 5
