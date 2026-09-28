# ABOUTME: Summing matrix S, bottom-up and MinT(Shrink) reconciliation of count forecasts.
# ABOUTME: Also builds the coherent, training-standardised residuals the detectors consume (D5).
"""Hierarchical reconciliation fixed by decisions D2 and D5.

``summing_matrix`` and bottom-up are ported from CDADE
``cdade/reconciliation/summing_matrix.py`` at fbfa609 (Apache-2.0). MinT(Shrink)
follows Wickramasuriya, Athanasopoulos & Hyndman (2019): the one-step-ahead
training errors give W1 = e'e / n, shrunk towards its diagonal with the
Schafer & Strimmer (2005) lambda as computed by ``hts::MinT``. Rows are ordered
PA then the 13 leaves. Only count forecasts are reconciled, never scores.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np

from headd_l0.data import Hierarchy


@dataclass(frozen=True)
class MinTFit:
    """Shrunk error covariance ``[14, 14]`` estimated on the training months."""

    covariance: np.ndarray
    shrinkage: float
    train_months: int


def summing_matrix(hierarchy: Hierarchy) -> np.ndarray:
    """Return S ``[n_leaves + 1, n_leaves]``: a row of ones, then the identity."""
    n_leaves = len(hierarchy.leaves)
    return np.vstack([np.ones((1, n_leaves)), np.eye(n_leaves)])


def shrinkage_covariance(errors: np.ndarray) -> tuple[np.ndarray, float]:
    """Shrink the error covariance towards its diagonal (MinT(Shrink)).

    Args:
        errors: Training errors ``[n_train, n_series]``.

    Returns:
        ``(W, lambda)`` with ``W = lambda diag(W1) + (1 - lambda) W1`` and a floor of
        ``1e-8 * max(trace(W) / n_series, 1)`` on the diagonal. A series with zero
        variance contributes zero correlation; lambda is 1 when every correlation is 0.
    """
    n, p = errors.shape
    w1 = errors.T @ errors / n
    sd = np.sqrt(np.diag(w1))
    scale = np.where(sd > 0, sd, 1.0)
    xs = np.where(sd > 0, errors / scale, 0.0)
    correlation = xs.T @ xs / n
    variance = (xs.T**2 @ xs**2 - (xs.T @ xs) ** 2 / n) / (n * (n - 1))
    off = ~np.eye(p, dtype=bool)
    denominator = float((correlation[off] ** 2).sum())
    lam = (
        1.0
        if denominator == 0
        else min(max(variance[off].sum() / denominator, 0.0), 1.0)
    )
    covariance = lam * np.diag(np.diag(w1)) + (1 - lam) * w1
    floor = 1e-8 * max(np.trace(covariance) / p, 1.0)
    np.fill_diagonal(covariance, np.maximum(np.diag(covariance), floor))
    return covariance, lam


def _bottom_up(
    base: np.ndarray, S: np.ndarray, _covariance: np.ndarray | None
) -> np.ndarray:
    return S @ base[1:]


def _mint_shrink(
    base: np.ndarray, S: np.ndarray, covariance: np.ndarray | None
) -> np.ndarray:
    if covariance is None:
        raise ValueError("mint_shrink needs the training error covariance")
    weighted = np.linalg.solve(covariance, S)  # W^-1 S
    gain = np.linalg.solve(S.T @ weighted, weighted.T)  # (S' W^-1 S)^-1 S' W^-1
    return S @ (gain @ base)


RECONCILERS: dict[
    str, Callable[[np.ndarray, np.ndarray, np.ndarray | None], np.ndarray]
] = {
    "bottom_up": _bottom_up,
    "mint_shrink": _mint_shrink,
}


def reconcile(
    base: np.ndarray,
    S: np.ndarray,
    method: str,
    *,
    covariance: np.ndarray | None = None,
) -> np.ndarray:
    """Project base forecasts ``[14, time]`` onto the coherent subspace.

    Args:
        base: Base forecasts in count units, rows PA then leaves.
        S: Summing matrix from :func:`summing_matrix`.
        method: ``"bottom_up"`` or ``"mint_shrink"``.
        covariance: Training error covariance, required by ``mint_shrink``.

    Returns:
        Coherent forecasts with the shape of ``base``; values are not clipped.
    """
    if method not in RECONCILERS:
        raise ValueError(f"unknown reconciliation method: {method}")
    return RECONCILERS[method](base, S, covariance)


def fit_mint(
    observed: np.ndarray, fitted: np.ndarray, train_months: int = 60
) -> MinTFit:
    """Estimate the MinT(Shrink) covariance from training-month errors only.

    Args:
        observed: Coherent counts ``[14, n_months]``.
        fitted: NB2 means ``[14, n_months]`` from ``forecast.forecast_mean``.
        train_months: Number of leading months used.

    Raises:
        ValueError: If a training forecast is not finite (a failed NB2 fit).
    """
    errors = (observed - fitted)[:, :train_months]
    if not np.isfinite(errors).all():
        raise ValueError("training forecasts must be finite; check NB2Fit.converged")
    covariance, lam = shrinkage_covariance(errors.T)
    return MinTFit(covariance=covariance, shrinkage=lam, train_months=train_months)


def reconciled_residuals(
    observed: np.ndarray, fitted: np.ndarray, S: np.ndarray, fit: MinTFit
) -> np.ndarray:
    """Return ``y - P mu`` ``[14, n_months]``, coherent because y and P mu both are."""
    return observed - reconcile(fitted, S, "mint_shrink", covariance=fit.covariance)


def standardize(residuals: np.ndarray, train_months: int = 60) -> np.ndarray:
    """Divide each series by its training-month standard deviation (ddof = 1).

    Raises:
        ValueError: If a series has zero training standard deviation.
    """
    scale = residuals[:, :train_months].std(axis=1, ddof=1)
    if (scale == 0).any():
        raise ValueError(
            f"zero training standard deviation in rows {np.flatnonzero(scale == 0)}"
        )
    return residuals / scale[:, None]
