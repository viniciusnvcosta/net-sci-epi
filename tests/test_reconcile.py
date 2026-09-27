# ABOUTME: Tests for S, bottom-up and MinT(Shrink) reconciliation of NB2 count forecasts.
# ABOUTME: Checks parity of S with CDADE, the Schafer-Strimmer lambda, coherence and causality.
"""Parity and behaviour tests for ``headd_l0.reconcile``."""

from pathlib import Path

import numpy as np
import pytest

from headd_l0.data import hierarchy
from headd_l0.forecast import fit_nb2, forecast_mean
from headd_l0.reconcile import (
    RECONCILERS,
    fit_mint,
    reconcile,
    reconciled_residuals,
    shrinkage_covariance,
    standardize,
    summing_matrix,
)

REFERENCE = Path(__file__).parent / "reference"
S = summing_matrix(hierarchy())


def _observed() -> np.ndarray:
    """Real coherent SIVEP counts, rows PA + 13 regions, from the pinned export."""
    reference = np.load(REFERENCE / "data.npz")
    return np.vstack([reference["state"], reference["counts"].T]).astype(float)


def test_s_matches_original():
    """CDADE builds the same 14 x 13 matrix; its MinT used a 13 x 13 one (MIGRATION.md)."""
    assert S.shape == (14, 13)
    np.testing.assert_array_equal(S, np.load(REFERENCE / "data.npz")["summing_matrix"])
    np.testing.assert_array_equal(S, np.vstack([np.ones((1, 13)), np.eye(13)]))


def test_bottom_up_exact():
    observed = _observed()
    np.testing.assert_array_equal(reconcile(observed, S, "bottom_up"), observed)
    incoherent = observed.copy()
    incoherent[0] += 5
    out = reconcile(incoherent, S, "bottom_up")
    np.testing.assert_array_equal(out[1:], observed[1:])
    np.testing.assert_array_equal(out[0], observed[1:].sum(axis=0))


def test_lambda_matches_manual_calculation():
    errors = np.random.default_rng(0).normal(size=(8, 3)) @ np.array(
        [[1.0, 0.5, 0.0], [0.0, 1.0, 0.3], [0.0, 0.0, 1.0]]
    )
    n, p = errors.shape
    w1 = errors.T @ errors / n
    sd = np.sqrt(np.diag(w1))
    xs = errors / sd
    numerator = denominator = 0.0
    for i in range(p):
        for j in range(p):
            if i == j:
                continue
            w = xs[:, i] * xs[:, j]
            numerator += ((w - w.mean()) ** 2).sum() / (n * (n - 1))
            denominator += (w1[i, j] / (sd[i] * sd[j])) ** 2
    expected = min(max(numerator / denominator, 0.0), 1.0)
    covariance, lam = shrinkage_covariance(errors)
    assert lam == pytest.approx(expected, rel=1e-12)
    target = lam * np.diag(np.diag(w1)) + (1 - lam) * w1
    np.testing.assert_allclose(covariance, target, rtol=1e-12)


def test_mint_is_coherent_and_idempotent():
    coherent = S @ np.arange(26.0).reshape(13, 2)
    out = reconcile(coherent, S, "mint_shrink", covariance=np.eye(14))
    np.testing.assert_allclose(out, coherent, atol=1e-10)
    rng = np.random.default_rng(1)
    base = rng.uniform(1, 100, size=(14, 5))
    a = rng.normal(size=(14, 14))
    covariance = a @ a.T + 14 * np.eye(14)
    once = reconcile(base, S, "mint_shrink", covariance=covariance)
    assert np.max(np.abs(once[0] - once[1:].sum(axis=0))) < 1e-10
    twice = reconcile(once, S, "mint_shrink", covariance=covariance)
    np.testing.assert_allclose(twice, once, atol=1e-10)
    inverse = np.linalg.inv(covariance)
    projection = S @ np.linalg.inv(S.T @ inverse @ S) @ S.T @ inverse
    np.testing.assert_allclose(once, projection @ base, atol=1e-10)


def test_mint_requires_training_covariance():
    with pytest.raises(ValueError, match="covariance"):
        reconcile(_observed(), S, "mint_shrink")
    with pytest.raises(ValueError, match="unknown"):
        reconcile(_observed(), S, "min_t")
    assert set(RECONCILERS) == {"bottom_up", "mint_shrink"}


def test_singular_training_errors():
    errors = np.random.default_rng(2).normal(size=(60, 14))
    errors[:, 3] = 0.0
    covariance, lam = shrinkage_covariance(errors)
    assert np.isfinite(covariance).all() and 0 <= lam <= 1
    assert covariance[3, 3] == pytest.approx(1e-8 * max(np.trace(covariance) / 14, 1))
    np.linalg.cholesky(covariance)


def test_reconciled_residuals_coherent():
    observed = _observed()
    fitted = forecast_mean(fit_nb2(observed), np.arange(132))
    mint = fit_mint(observed, fitted)
    residuals = reconciled_residuals(observed, fitted, S, mint)
    assert residuals.shape == (14, 132)
    np.testing.assert_allclose(
        residuals[0], residuals[1:].sum(axis=0), rtol=0, atol=1e-10
    )


def test_training_months_only():
    """Months >= 60 change neither the NB2 forecasts nor the MinT covariance."""
    observed = _observed()
    changed = observed.copy()
    changed[:, 60:] = np.random.default_rng(3).integers(0, 10**5, size=(14, 72))
    months = np.arange(132)
    fitted, fitted_changed = (
        forecast_mean(fit_nb2(x), months) for x in (observed, changed)
    )
    np.testing.assert_array_equal(fitted, fitted_changed)
    first, second = fit_mint(observed, fitted), fit_mint(changed, fitted_changed)
    np.testing.assert_array_equal(first.covariance, second.covariance)
    assert first.shrinkage == second.shrinkage and first.train_months == 60


def test_fit_mint_rejects_failed_forecasts():
    observed = _observed()
    fitted = forecast_mean(fit_nb2(observed), np.arange(132))
    fitted[5, 10] = np.nan
    with pytest.raises(ValueError, match="finite"):
        fit_mint(observed, fitted)


def test_standardize_uses_training_sd():
    residuals = np.random.default_rng(4).normal(size=(2, 132))
    out = standardize(residuals)
    np.testing.assert_allclose(
        out, residuals / residuals[:, :60].std(axis=1, ddof=1)[:, None]
    )
    changed = residuals.copy()
    changed[:, 60:] *= 100
    np.testing.assert_array_equal(standardize(changed)[:, :60], out[:, :60])
    residuals[1, :60] = 0.0
    with pytest.raises(ValueError, match="zero"):
        standardize(residuals)
