"""Causal competence/diversity selection for B1* (decision D6).

Q and exhaustive subset scoring follow CDADE fbfa609 selection/diversity.py
and selector.py (Apache-2.0). Time alignment and window competence are corrected:
selection at t consumes votes only through t-1, never outbreak labels.
"""

from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from river.drift import ADWIN


@dataclass(frozen=True)
class SelectionConfig:
    """Previous-window length, subset size, competence weight and ADWIN delta."""

    window: int = 12
    k: int = 5
    alpha: float = 0.5
    drift_delta: float = 0.002


@dataclass(frozen=True)
class SelectionResult:
    """Blended scores [time], selected indices [time,k] and causal diagnostics.

    Competence is [time,detector], drift [time]. Training scores are NaN to
    exclude warmup from evaluation. Active warmup indices are lexicographic.
    """

    scores: np.ndarray
    active: np.ndarray
    competence: np.ndarray
    drift: np.ndarray


def _binary(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values)
    if values.ndim != 1 or not np.isin(values, [0, 1]).all():
        raise ValueError("predictions and labels must be binary vectors")
    return values.astype(bool)


def q_statistic(pred_a: np.ndarray, pred_b: np.ndarray, labels: np.ndarray) -> float:
    """Return Q of classifier correctness, or zero for a zero denominator.

    Args:
        pred_a: First classifier's binary votes.
        pred_b: Second classifier's binary votes.
        labels: Reference votes; stream callers supply only pseudo-labels.
    """
    a, b, y = _binary(pred_a), _binary(pred_b), _binary(labels)
    if a.shape != b.shape or a.shape != y.shape:
        raise ValueError("binary vectors must have equal lengths")
    a, b = a == y, b == y
    n11, n00 = int(np.sum(a & b)), int(np.sum(~a & ~b))
    n10, n01 = int(np.sum(a & ~b)), int(np.sum(~a & b))
    denominator = n11 * n00 + n10 * n01
    return (n11 * n00 - n10 * n01) / denominator if denominator else 0.0


def _validate_config(cfg: SelectionConfig, size: int) -> None:
    if not (
        1 <= cfg.k <= size
        and cfg.window >= 1
        and 0 <= cfg.alpha <= 1
        and 0 < cfg.drift_delta < 1
    ):
        raise ValueError("invalid selector configuration for this pool")


def select_subset(
    competence: np.ndarray,
    predictions: np.ndarray,
    labels: np.ndarray,
    cfg: SelectionConfig,
) -> np.ndarray:
    """Exhaustively maximize competence/diversity, breaking ties lexicographically.

    Args:
        competence: Competence vector [detector].
        predictions: Binary votes [detector, time] in the previous window.
        labels: Majority pseudo-label vector [time].
        cfg: Selection configuration.
    """
    competence = np.asarray(competence, dtype=float)
    predictions = np.asarray(predictions)
    labels = _binary(labels)
    if competence.ndim != 1 or not np.isfinite(competence).all():
        raise ValueError("competence must be a finite vector")
    _validate_config(cfg, len(competence))
    if (
        predictions.shape != (len(competence), len(labels))
        or not np.isin(predictions, [0, 1]).all()
    ):
        raise ValueError("predictions must be binary [detector,time]")
    best_score, best = -np.inf, tuple(range(cfg.k))
    for subset in combinations(range(len(competence)), cfg.k):
        pairs = list(combinations(subset, 2))
        diversity = 0.0
        if pairs:
            mean_q = np.mean(
                [q_statistic(predictions[i], predictions[j], labels) for i, j in pairs]
            )
            diversity = 0.5 * (1 - mean_q)
        value = (
            cfg.alpha * competence[list(subset)].mean() + (1 - cfg.alpha) * diversity
        )
        if value > best_score:
            best_score, best = value, subset
    return np.asarray(best, dtype=int)


def _competence(votes: np.ndarray, labels: np.ndarray) -> np.ndarray:
    if not labels.any():
        return np.mean(~votes, axis=0)
    tp = (votes & labels[:, None]).sum(axis=0)
    precision = np.divide(
        tp, votes.sum(axis=0), out=np.zeros(votes.shape[1]), where=votes.sum(axis=0) > 0
    )
    recall = tp / labels.sum()
    return 0.5 * (precision + recall)


def select_stream(
    scores: np.ndarray, train_end: int, cfg: SelectionConfig
) -> SelectionResult:
    """Select and blend each month's scores using strictly previous-window votes.

    Args:
        scores: Finite [time,detector] scores, higher means more anomalous.
        train_end: Exclusive training cutoff for scaling and .95 vote quantiles.
        cfg: Causal window, subset and drift settings.

    Returns:
        Frozen result. ADWIN observes mean previous-window competence after each
        decision; drift at t clears the window and sets competence .5 at t+1.
        Training min/max stays fixed; constant training columns normalize to zero.
    """
    scores = np.asarray(scores, dtype=float)
    if scores.ndim != 2 or not np.isfinite(scores).all():
        raise ValueError("scores must be a finite [time,detector] matrix")
    n, size = scores.shape
    if not 1 <= train_end <= n:
        raise ValueError("train_end must identify a nonempty training prefix")
    _validate_config(cfg, size)
    lo = scores[:train_end].min(axis=0)
    span = np.ptp(scores[:train_end], axis=0)
    normalized = np.divide(scores - lo, span, out=np.zeros_like(scores), where=span > 0)
    cutoffs = np.quantile(normalized[:train_end], 0.95, axis=0)
    votes = normalized > cutoffs
    labels = votes.mean(axis=1) > 0.5
    blended = np.full(n, np.nan)
    active = np.tile(np.arange(cfg.k), (n, 1))
    competence = np.full((n, size), 0.5)
    drift = np.zeros(n, dtype=bool)
    detector = ADWIN(delta=cfg.drift_delta)
    reset_start = 0
    for t in range(train_end, n):
        start = max(reset_start, t - cfg.window)
        if start < t:
            competence[t] = _competence(votes[start:t], labels[start:t])
            active[t] = select_subset(
                competence[t], votes[start:t].T, labels[start:t], cfg
            )
        blended[t] = normalized[t, active[t]].mean()
        detector.update(float(competence[t].mean()))
        drift[t] = detector.drift_detected
        if drift[t]:
            reset_start = t + 1
    return SelectionResult(blended, active, competence, drift)


SELECTORS: dict[str, Callable[[np.ndarray, int, SelectionConfig], SelectionResult]] = {
    "meta_des": select_stream,
}
