"""Tests for pure math statistical functions."""

import math

import pytest

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


class TestMean:
    def test_basic(self):
        assert mean([1, 2, 3, 4, 5]) == 3.0

    def test_single(self):
        assert mean([42]) == 42.0

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            mean([])


class TestVariance:
    def test_basic(self):
        v = variance([2, 4, 4, 4, 5, 5, 7, 9])
        assert abs(v - 4.0) < 1e-9


class TestStdDev:
    def test_basic(self):
        s = std_dev([2, 4, 4, 4, 5, 5, 7, 9])
        assert abs(s - 2.0) < 1e-9


class TestStandardize:
    def test_basic(self):
        result = standardize([1, 2, 3, 4, 5])
        assert abs(sum(result)) < 1e-9  # mean ≈ 0
        assert abs(result[0] + result[-1]) < 1e-9  # symmetric

    def test_zero_std(self):
        result = standardize([5, 5, 5])
        assert result == [0.0, 0.0, 0.0]


class TestEuclideanDistance:
    def test_same(self):
        assert euclidean_distance([1, 2, 3], [1, 2, 3]) == 0.0

    def test_known(self):
        d = euclidean_distance([0, 0], [3, 4])
        assert abs(d - 5.0) < 1e-9

    def test_mismatched_length(self):
        with pytest.raises(ValueError):
            euclidean_distance([1], [1, 2])


class TestCosineSimilarity:
    def test_same(self):
        assert abs(cosine_similarity([1, 2, 3], [1, 2, 3]) - 1.0) < 1e-9

    def test_orthogonal(self):
        assert abs(cosine_similarity([1, 0], [0, 1])) < 1e-9

    def test_opposite(self):
        assert abs(cosine_similarity([1, 0], [-1, 0]) + 1.0) < 1e-9

    def test_zero_vector(self):
        assert cosine_similarity([0, 0], [1, 1]) == 0.0


class TestSigmoid:
    def test_zero(self):
        assert abs(sigmoid(0) - 0.5) < 1e-9

    def test_bounds(self):
        for x in [-10, -1, 0, 1, 10]:
            assert 0 < sigmoid(x) < 1


class TestSoftmax:
    def test_sums_to_one(self):
        result = softmax([1, 2, 3])
        assert abs(sum(result) - 1.0) < 1e-9

    def test_ordering(self):
        result = softmax([1, 3, 2])
        assert result[1] > result[2] > result[0]

    def test_empty(self):
        assert softmax([]) == []
