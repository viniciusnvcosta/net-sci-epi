# ABOUTME: Tests for the NB2 trend-plus-harmonics forecaster used by MinT and the null model.
# ABOUTME: Covers the design matrix, parameter recovery, training-only fits and failure records.
"""Behaviour tests for ``headd_l0.forecast``."""

from pathlib import Path

import numpy as np
import pytest

from headd_l0.forecast import fit_nb2, forecast_mean, harmonic_design

REFERENCE = Path(__file__).parent / "reference"
TRUE = np.array([3.0, 0.002, 0.3, -0.2, 0.1, 0.05])


def _simulate(coefficients, alpha, months, rng):
    """NB2 draws as a gamma-Poisson mixture with mean mu and variance mu + alpha mu^2."""
    mu = np.exp(harmonic_design(months) @ coefficients)
    return rng.poisson(rng.gamma(1 / alpha, alpha * mu))


def _panel(n_series, months, seed):
    rng = np.random.default_rng(seed)
    return np.vstack([_simulate(TRUE, 0.1, months, rng) for _ in range(n_series)])


def test_design_hand_calculation():
    X = harmonic_design(np.array([0, 3]))
    expected = [[1, 0, 0, 1, 0, 1], [1, 3, 1, 0, 0, -1]]
    np.testing.assert_allclose(X, expected, atol=1e-12)


def test_recovers_known_parameters():
    counts = _panel(2, np.arange(600), seed=7)
    fit = fit_nb2(counts, train_months=600)
    assert fit.converged.all()
    np.testing.assert_allclose(fit.coefficients, np.tile(TRUE, (2, 1)), atol=0.08)
    np.testing.assert_allclose(fit.alpha, 0.1, rtol=0.3)


def test_fit_uses_training_only():
    counts = _panel(3, np.arange(132), seed=1)
    changed = counts.copy()
    changed[:, 60:] = np.random.default_rng(2).integers(0, 10**6, size=(3, 72))
    first, second = fit_nb2(counts), fit_nb2(changed)
    assert first.train_months == 60
    np.testing.assert_array_equal(first.coefficients, second.coefficients)
    np.testing.assert_array_equal(first.alpha, second.alpha)
    months = np.arange(132)
    np.testing.assert_array_equal(
        forecast_mean(first, months), forecast_mean(second, months)
    )


def test_forecast_positive_and_shaped():
    fit = fit_nb2(_panel(3, np.arange(132), seed=3))
    months = np.arange(132)
    mu = forecast_mean(fit, months)
    assert mu.shape == (3, 132)
    assert np.isfinite(mu).all() and (mu > 0).all()
    np.testing.assert_allclose(mu, np.exp(fit.coefficients @ harmonic_design(months).T))


@pytest.mark.filterwarnings("error")
def test_nonconvergence_recorded():
    counts = _panel(2, np.arange(132), seed=4)
    counts[1] = 0
    fit = fit_nb2(counts)
    assert fit.converged.tolist() == [True, False]
    assert np.isfinite(fit.coefficients[0]).all()
    assert not np.isfinite(forecast_mean(fit, np.arange(132))[1]).all()


@pytest.mark.filterwarnings("error")
def test_real_sivep_series_converge():
    """PA and the 13 regions of the committed reference fixture all converge."""
    reference = np.load(REFERENCE / "data.npz")
    observed = np.vstack([reference["state"], reference["counts"].T])
    fit = fit_nb2(observed)
    assert fit.coefficients.shape == (14, 6)
    assert fit.converged.all()
    assert (fit.alpha > 0).all()
