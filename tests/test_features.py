# ABOUTME: Behaviour tests for causal features built from standardized residuals.
# ABOUTME: Checks full-axis alignment, hand calculations, validity and prefix invariance.
"""Tests for local, neighborhood and rolling early-warning features."""

import numpy as np
import pytest

from headd_l0.features import FEATURES, local_features, neighbor_features, rolling_ews


def test_neighbor_hand_calculation():
    x = np.array([[1.0, 2.0, 3.0], [10.0, 20.0, 30.0]])
    W = np.array([[0.0, 1.0], [1.0, 0.0]])
    batch = neighbor_features(x, W, window=2)
    np.testing.assert_array_equal(batch.values[:, :, 0], W @ x)
    np.testing.assert_array_equal(batch.values[:, 1:, 1], W @ x[:, :-1])
    np.testing.assert_array_equal(batch.values[:, 0, 1], 0)
    np.testing.assert_array_equal(batch.values[:, :, 2], x - W @ x)
    assert batch.names == (
        "neighbor_now",
        "neighbor_lag1",
        "neighbor_difference",
        "local_moran",
    )
    np.testing.assert_array_equal(batch.months, np.arange(3))


def test_prefix_invariance():
    rng = np.random.default_rng(5)
    x = rng.normal(size=(3, 132))
    changed = x.copy()
    changed[:, 90:] += 100
    W = np.array([[0, 1, 0], [0.5, 0, 0.5], [0, 1, 0]], dtype=float)
    np.testing.assert_array_equal(
        local_features(x).values[:, :90], local_features(changed).values[:, :90]
    )
    np.testing.assert_array_equal(
        neighbor_features(x, W).values[:, :90],
        neighbor_features(changed, W).values[:, :90],
    )
    ews, valid = rolling_ews(x[0], 12)
    changed_ews, changed_valid = rolling_ews(changed[0], 12)
    np.testing.assert_array_equal(ews[:90], changed_ews[:90])
    np.testing.assert_array_equal(valid[:90], changed_valid[:90])
    assert not valid[:11].any()


def test_constant_series_finite_with_invalid_mask():
    ews, valid = rolling_ews(np.zeros(132), 12)
    assert ews.shape == valid.shape == (132, 5)
    assert np.isfinite(ews).all()
    assert not valid[:, 1:3].any()
    assert valid[11, 0]
    assert ews[11, 0] == 0
    assert not valid[11, 3:].any()


def test_node_and_feature_axes():
    residuals = np.arange(14 * 4, dtype=float).reshape(14, 4)
    local = local_features(residuals)
    assert local.values.shape == (14, 4, 3)
    assert local.names == ("residual", "residual_lag1", "residual_change")
    np.testing.assert_array_equal(local.months, np.arange(4))
    np.testing.assert_array_equal(local.values[:, :, 0], residuals)
    np.testing.assert_array_equal(local.values[:, 1:, 1], residuals[:, :-1])
    np.testing.assert_array_equal(
        local.values[:, :, 2], local.values[:, :, 0] - local.values[:, :, 1]
    )
    W = np.eye(13)
    W = (np.ones((13, 13)) - W) / 12
    neighbors = neighbor_features(residuals[1:], W, window=2)
    assert neighbors.values.shape == (13, 4, 4)
    assert set(FEATURES) == {"local", "neighbors"}
    assert FEATURES["local"](residuals).values.shape == local.values.shape
    assert FEATURES["neighbors"](residuals[1:], W, window=2).names == neighbors.names


def test_local_moran_hand_calculation():
    x = np.array([[1.0, 1.0], [2.0, 2.0], [4.0, 4.0]])
    W = np.array([[0, 1, 0], [0.5, 0, 0.5], [0, 1, 0]], dtype=float)
    moran = neighbor_features(x, W, window=2).values[:, :, 3]
    np.testing.assert_array_equal(moran[:, 0], 0)
    np.testing.assert_allclose(moran[:, 1], [2 / 7, -1 / 28, -5 / 14])
    constant = neighbor_features(np.ones_like(x), W, window=2)
    assert np.isfinite(constant.values).all()
    np.testing.assert_array_equal(constant.values[:, :, 3], 0)


def test_residual_inputs_only():
    residuals = np.array([[0.0, 1.0, -2.0], [2.0, -1.0, 1.0]])
    W = np.array([[0.0, 1.0], [1.0, 0.0]])
    counts_a = 10 + residuals
    counts_b = 1000 + 100 * residuals
    standardized_a = (counts_a - 10) / 1
    standardized_b = (counts_b - 1000) / 100
    np.testing.assert_array_equal(
        local_features(standardized_a).values, local_features(standardized_b).values
    )
    np.testing.assert_array_equal(
        neighbor_features(standardized_a, W, window=2).values,
        neighbor_features(standardized_b, W, window=2).values,
    )


def test_rolling_ews_hand_calculation():
    ews, valid = rolling_ews(np.array([1.0, 2.0, 3.0, 4.0]), 4)
    assert not valid[:3].any()
    np.testing.assert_allclose(
        ews[3], [np.sqrt(5 / 3), np.sqrt(5 / 3) / 2.5, 1, 0, 1.64]
    )
    assert valid[3].all()


@pytest.mark.parametrize("window", [0, -1])
def test_window_must_be_positive(window):
    with pytest.raises(ValueError, match="window"):
        rolling_ews(np.arange(5.0), window)
    with pytest.raises(ValueError, match="window"):
        neighbor_features(np.ones((2, 5)), np.array([[0, 1], [1, 0]]), window)
