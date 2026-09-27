"""GPD upper-tail fitting and conservative calibration using null scores only."""

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.stats import genpareto


@dataclass(frozen=True)
class TailFit:
    """POT threshold, GPD parameters and observed unconditional tail mass."""

    u: float
    shape: float
    scale: float
    tail_fraction: float


@dataclass(frozen=True)
class Calibration:
    """Threshold and empirical FAR on calibration observations (not evaluation)."""

    threshold: float
    target_far: float
    achieved_far: float
    n: int
    method: str


class _TailError(ValueError):
    """A valid sample cannot support the requested GPD fit."""


def _scores(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("scores must be a nonempty finite vector")
    return values


def fit_tail(scores: np.ndarray, tail_fraction: float = 0.05) -> TailFit:
    """Fit positive exceedances with fixed GPD location zero.

    Args:
        scores: Higher-is-more-anomalous calibration scores; never absolute-valued.
        tail_fraction: Fraction defining the order-statistic threshold.

    Returns:
        Fit with the actual strict-exceedance fraction, accounting for ties.

    Raises:
        ValueError: Invalid input, fewer than 20 exceedances, or degenerate fit.
    """
    scores = _scores(scores)
    if not 0 < tail_fraction < 1:
        raise ValueError("tail_fraction must be in (0, 1)")
    n_tail = max(1, int(tail_fraction * len(scores)))
    u = float(np.sort(scores)[-n_tail])
    excess = scores[scores > u] - u
    if len(excess) < 20:
        raise _TailError("insufficient_tail")
    if np.ptp(excess) == 0:
        raise _TailError("degenerate_tail")
    try:
        shape, _, scale = genpareto.fit(excess, floc=0)
    except (ValueError, RuntimeError, FloatingPointError) as exc:
        raise _TailError("degenerate_tail") from exc
    if not np.isfinite([shape, scale]).all() or scale <= 0:
        raise _TailError("degenerate_tail")
    return TailFit(u, float(shape), float(scale), len(excess) / len(scores))


def calibration_report(null_scores: np.ndarray, target_far: float) -> Calibration:
    """Calibrate a strict ``score > threshold`` alarm on nulls.

    Args:
        null_scores: Independent calibration-null scores; no evaluation data.
        target_far: Target false-alarm fraction in (0, 1).

    Returns:
        Diagnostic with a named empirical fallback if a GPD is unsupported.
        The bound applies to calibration FAR, not an unseen evaluation sample.
    """
    scores = _scores(null_scores)
    if not 0 < target_far < 1:
        raise ValueError("target_far must be in (0, 1)")
    allowed = int(np.floor(target_far * len(scores)))
    empirical = float(np.sort(scores)[len(scores) - allowed - 1])
    threshold, method = empirical, "evt_gpd"
    try:
        tail = fit_tail(scores)
    except _TailError as exc:
        method = f"empirical_{exc}"
    else:
        if target_far >= tail.tail_fraction:
            method = "empirical_outside_tail"
        else:
            quantile = tail.u + genpareto.isf(
                target_far / tail.tail_fraction, tail.shape, scale=tail.scale
            )
            if np.isfinite(quantile):
                threshold = max(empirical, float(quantile))
            else:
                method = "empirical_degenerate_tail"
    achieved = float(np.mean(scores > threshold))
    return Calibration(threshold, target_far, achieved, len(scores), method)


def calibrate(null_scores: np.ndarray, target_far: float) -> float:
    """Return the calibrated threshold; use calibration_report for provenance."""
    return calibration_report(null_scores, target_far).threshold


THRESHOLDS: dict[str, Callable[[np.ndarray, float], float]] = {"evt_gpd": calibrate}
