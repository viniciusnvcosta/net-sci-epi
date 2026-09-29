# ABOUTME: Causal local, neighbor and early-warning features on standardized residuals.
# ABOUTME: Preserves the full month axis with zero warmup values and explicit EWS validity.
"""Causal features for the B0/B1*/B2 residual representations (D5).

Inputs are standardized residuals, not counts. The caller excludes month zero
from training/evaluation because lag-one features there use a zero placeholder.
For local Moran, months before a complete trailing ``window`` have zero
placeholders and are ineligible; eligibility starts at ``window - 1``. EWS
returns an elementwise validity mask. Neither routine backfills warmup months.
"""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FeatureBatch:
    """Features aligned to all input months, with axes ``[nodes, months, features]``.

    Attributes:
        values: Feature values. Undefined and warmup cells hold finite zero.
        months: Zero-based input month indices.
        names: Stable feature column names, in the order of the final axis.
    """

    values: np.ndarray
    months: np.ndarray
    names: tuple[str, ...]


def _residuals_array(residuals: np.ndarray) -> np.ndarray:
    array = np.asarray(residuals, dtype=float)
    if array.ndim != 2 or not all(array.shape) or not np.isfinite(array).all():
        raise ValueError("residuals must be a nonempty finite [nodes, time] array")
    return array


def local_features(residuals: np.ndarray) -> FeatureBatch:
    """Return current, lag-one and change features from standardized residuals.

    Args:
        residuals: Standardized residuals ``[nodes, time]``, including PA if
            present. The caller excludes month zero when lag-one is required.

    Returns:
        Full-axis feature batch ``[nodes, time, 3]``. Lag one at month zero is
        zero, so the initial change equals the initial residual.
    """
    x = _residuals_array(residuals)
    lag = np.zeros_like(x)
    lag[:, 1:] = x[:, :-1]
    values = np.stack((x, lag, x - lag), axis=-1)
    return FeatureBatch(
        values, np.arange(x.shape[1]), ("residual", "residual_lag1", "residual_change")
    )


def neighbor_features(
    residuals: np.ndarray, W: np.ndarray, window: int = 12
) -> FeatureBatch:
    """Return neighbor and trailing local-Moran features for leaf residuals.

    Args:
        residuals: Standardized residuals ``[leaves, time]``; no PA row.
        W: Row-normalized leaf-neighbor matrix with no self loops.
        window: Number of trailing months averaged for local Moran.

    Returns:
        Full-axis batch ``[leaves, time, 4]``. Neighbor lag one is zero at
        month zero. Moran is zero before ``window - 1`` and those months are
        ineligible for evaluation. A zero spatial variance gives Moran zero.
    """
    x = _residuals_array(residuals)
    weights = np.asarray(W, dtype=float)
    if not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive integer")
    if (
        weights.shape != (x.shape[0], x.shape[0])
        or not np.isfinite(weights).all()
        or np.any(weights < 0)
        or not np.allclose(np.diag(weights), 0)
        or not np.allclose(weights.sum(axis=1), 1)
    ):
        raise ValueError("W must be a finite row-normalized matrix without self loops")

    neighbor_now = weights @ x
    neighbor_lag = np.zeros_like(x)
    neighbor_lag[:, 1:] = neighbor_now[:, :-1]
    centered = x - x.mean(axis=0, keepdims=True)
    m2 = np.mean(centered**2, axis=0)
    instant_moran = np.zeros_like(x)
    nonconstant = m2 > 0
    instant_moran[:, nonconstant] = (
        centered[:, nonconstant]
        * (weights @ centered[:, nonconstant])
        / m2[nonconstant]
    )
    trailing_moran = np.zeros_like(x)
    for month in range(window - 1, x.shape[1]):
        trailing_moran[:, month] = instant_moran[
            :, month - window + 1 : month + 1
        ].mean(axis=1)
    values = np.stack(
        (neighbor_now, neighbor_lag, x - neighbor_now, trailing_moran), axis=-1
    )
    return FeatureBatch(
        values,
        np.arange(x.shape[1]),
        ("neighbor_now", "neighbor_lag1", "neighbor_difference", "local_moran"),
    )


def rolling_ews(series: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    """Compute causal SD, CV, AR1, skewness and Pearson kurtosis.

    Uses sample SD (``ddof=1``), Pearson correlation of overlapping lag-one
    vectors, and uncorrected standardized central moments for skewness and
    kurtosis (normal kurtosis 3). Complete trailing windows are required.
    SD needs at least 2 samples, AR1 and skewness at least 3, and kurtosis at
    least 4. A zero mean makes CV invalid; zero variance makes AR1, skewness
    and kurtosis invalid. Invalid cells hold zero with a false mask.

    Args:
        series: One finite residual series ``[time]``.
        window: Complete trailing window length.

    Returns:
        ``(values, valid)`` arrays, both ``[time, 5]``. The second array is
        boolean and identifies each defined statistic and eligible month.
    """
    x = np.asarray(series, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError("series must be a finite [time] array")
    if not isinstance(window, int) or window < 1:
        raise ValueError("window must be a positive integer")
    values = np.zeros((x.size, 5), dtype=float)
    valid = np.zeros((x.size, 5), dtype=bool)
    for month in range(window - 1, x.size):
        sample = x[month - window + 1 : month + 1]
        mean = float(sample.mean())
        centered = sample - mean
        m2 = float(np.mean(centered**2))
        if window >= 2:
            sd = float(np.std(sample, ddof=1))
            values[month, 0] = sd
            valid[month, 0] = True
            if mean != 0:
                values[month, 1] = sd / mean
                valid[month, 1] = True
        if window >= 3 and m2 > 0:
            before, after = sample[:-1], sample[1:]
            centered_before = before - before.mean()
            centered_after = after - after.mean()
            denominator = float(
                np.linalg.norm(centered_before) * np.linalg.norm(centered_after)
            )
            if denominator > 0:
                values[month, 2] = float(centered_before @ centered_after / denominator)
                valid[month, 2] = True
            values[month, 3] = float(np.mean(centered**3) / m2**1.5)
            valid[month, 3] = True
            if window >= 4:
                values[month, 4] = float(np.mean(centered**4) / m2**2)
                valid[month, 4] = True
    return values, valid


FEATURES: dict[str, Callable[..., FeatureBatch]] = {
    "local": local_features,
    "neighbors": neighbor_features,
}
