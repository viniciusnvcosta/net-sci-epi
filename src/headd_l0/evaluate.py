"""Detection timing, eligible-month FAR and metrics using supplied alarms.

AP and simplified NAB follow CDADE fbfa609 evaluation/metrics.py (Apache-2.0).
The original test-median threshold is excluded: callers supply calibrated alarms.
"""

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score


@dataclass(frozen=True)
class DetectionOutcome:
    """Detection within the onset window; no onset has no timing denominator."""

    detected: bool
    first_alarm: int | None
    onset: int
    delay: float | None
    lead: float | None
    restricted_lead: float | None
    censored: bool


def _binary(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values)
    if values.ndim != 1 or not len(values) or not np.isin(values, [0, 1]).all():
        raise ValueError("expected a nonempty binary vector")
    return values.astype(bool)


def _classification(
    labels: np.ndarray, scores: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    labels = _binary(labels)
    scores = np.asarray(scores, dtype=float)
    if scores.shape != labels.shape or not np.isfinite(scores).all():
        raise ValueError("scores must be finite and aligned with labels")
    return labels, scores


def detection_outcome(
    alarms: np.ndarray, onset: int, pre: int = 12, post: int = 12
) -> DetectionOutcome:
    """Find the first alarm in an inclusive onset-centred observation window.

    Args:
        alarms: Alarms on the observed timeline; caller masks unmonitored months.
        onset: Event month, or -1 for no event (excluded from detection denominators).
        pre: Maximum months before onset.
        post: Maximum months after onset.

    Returns:
        Lead = onset-alarm. Misses are censored at the clipped window end plus
        one, with restricted_lead retaining them in paired comparisons.
    """
    alarms = _binary(alarms)
    if pre < 0 or post < 0 or onset < -1 or onset >= len(alarms):
        raise ValueError("invalid onset or detection window")
    if onset == -1:
        return DetectionOutcome(False, None, onset, None, None, None, False)
    start, end = max(0, onset - pre), min(len(alarms) - 1, onset + post)
    hits = np.flatnonzero(alarms[start : end + 1])
    if not len(hits):
        return DetectionOutcome(
            False, None, onset, None, None, float(onset - end - 1), True
        )
    first = int(start + hits[0])
    lead = float(onset - first)
    return DetectionOutcome(True, first, onset, -lead, lead, lead, False)


def observed_far(alarms: np.ndarray, eligible: np.ndarray) -> float:
    """Return alarm fraction over eligible monitored null months only.

    Args:
        alarms: Binary monthly alarms.
        eligible: Aligned mask excluding warmup or unobserved months.
    """
    alarms, eligible = _binary(alarms), _binary(eligible)
    if alarms.shape != eligible.shape or not eligible.any():
        raise ValueError("eligible must align and include at least one month")
    return float(alarms[eligible].mean())


def auc_pr(labels: np.ndarray, scores: np.ndarray) -> float:
    """Compute average precision; require both classes for discrimination.

    Args:
        labels: Binary reference labels for the evaluation interval.
        scores: Aligned anomaly scores, higher means more anomalous.
    """
    labels, scores = _classification(labels, scores)
    if np.unique(labels).size != 2:
        raise ValueError("AP discrimination requires both classes")
    return float(average_precision_score(labels, scores))


def nab_simplified(labels: np.ndarray, alarms: np.ndarray, window: int = 4) -> float:
    """Return the legacy simplified NAB formula using caller-supplied alarms.

    Args:
        labels: Binary event labels (rising edges define onsets).
        alarms: Calibrated binary alarms, not thresholded from evaluation scores.
        window: Symmetric onset window half-width.

    Notes:
        Each alarm near any onset earns one point, false alarms cost .11,
        and the onset-normalized result is clipped to [0,1]. This is not full NAB.
    """
    labels, alarms = _binary(labels), _binary(alarms)
    if labels.shape != alarms.shape or window < 0:
        raise ValueError("alarms must align and window must be nonnegative")
    onsets = np.flatnonzero(np.diff(np.r_[0, labels.astype(int)]) == 1)
    if not len(onsets):
        return 0.0
    times = np.flatnonzero(alarms)
    near = (np.abs(times[:, None] - onsets) <= window).any(axis=1)
    score = (int(near.sum()) - 0.11 * int((~near).sum())) / len(onsets)
    return float(np.clip(score, 0, 1))


def classification_metrics(
    labels: np.ndarray, scores: np.ndarray, alarms: np.ndarray
) -> dict[str, float | None]:
    """Report AP/ROC, precision/recall/F1 and simplified NAB without point adjustment.

    Args:
        labels: Binary reference labels.
        scores: Finite aligned anomaly scores.
        alarms: Alarms from the independently calibrated threshold.

    Returns:
        Undefined single-class discrimination metrics are None, not perfect AP.
    """
    labels, scores = _classification(labels, scores)
    alarms = _binary(alarms)
    if alarms.shape != labels.shape:
        raise ValueError("alarms must align with labels")
    tp = int(np.sum(alarms & labels))
    precision = tp / int(alarms.sum()) if alarms.any() else 0.0
    recall = tp / int(labels.sum()) if labels.any() else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    both = np.unique(labels).size == 2
    return {
        "auc_pr": auc_pr(labels, scores) if both else None,
        "roc_auc": float(roc_auc_score(labels, scores)) if both else None,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "nab_simplified": nab_simplified(labels, alarms),
    }
