"""Paired resampling and the ordered secondary inference protocol.

Cliff's point statistic and rank-test primitives follow CDADE fbfa609
(evaluation/stats.py, Apache-2.0). RNG, HAC and stopping behavior are corrected.
"""

from dataclasses import dataclass
from itertools import combinations

import numpy as np
from scipy.stats import friedmanchisquare, norm, rankdata, wilcoxon


@dataclass(frozen=True)
class BootstrapResult:
    """Point estimate, percentile95% interval and number of sampled units."""

    estimate: float
    low: float
    high: float
    n_units: int


@dataclass(frozen=True)
class SecondaryResult:
    """Ordered test results; empty follow-up dictionaries mean not executed."""

    friedman: dict
    wilcoxon: dict
    dm: dict
    cliffs: dict
    stop_reason: str | None


def _finite(values: np.ndarray, ndim: int) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    if values.ndim != ndim or not values.size or not np.isfinite(values).all():
        raise ValueError(f"expected a nonempty finite {ndim}-D array")
    return values


def _interval(estimate: float, draws: np.ndarray, units: int) -> BootstrapResult:
    low, high = np.quantile(draws, [0.025, 0.975])
    return BootstrapResult(float(estimate), float(low), float(high), units)


def task_bootstrap(
    delta: np.ndarray, rng: np.random.Generator, n_boot: int = 10000
) -> BootstrapResult:
    """Resample already-paired task differences; layer0 callers exclude PA.

    Args:
        delta: One paired difference per region/task (13regions under D-GT1).
        rng: Caller-owned random generator.
        n_boot: Number of bootstrap draws.
    """
    delta = _finite(delta, 1)
    if n_boot < 1:
        raise ValueError("n_boot must be positive")
    indices = rng.integers(0, len(delta), size=(n_boot, len(delta)))
    return _interval(delta.mean(), delta[indices].mean(axis=1), len(delta))


def paired_bootstrap(
    delta: np.ndarray, rng: np.random.Generator, n_boot: int = 10000
) -> BootstrapResult:
    """Resample replicates, retaining all regional deltas in each replicate.

    Args:
        delta: Finite paired differences [replicate,region], within one stratum.
        rng: Caller-owned random generator.
        n_boot: Number of draws; caller stratifies by epsilon/noise.
    """
    delta = _finite(delta, 2)
    return task_bootstrap(delta.mean(axis=1), rng, n_boot)


def block_bootstrap(
    delta: np.ndarray, block_length: int, rng: np.random.Generator, n_boot: int = 10000
) -> BootstrapResult:
    """Resample circular temporal blocks within each region; never pool regions.

    Args:
        delta: Already-paired differences [region,time].
        block_length: Contiguous block length, at most the series length.
        rng: Caller-owned random generator.
        n_boot: Number of resamples.

    Returns:
        CI for the grand mean; n_units counts retained region series, not
        independent months or an effective sample size.
    """
    delta = _finite(delta, 2)
    regions, time = delta.shape
    if not 1 <= block_length <= time or n_boot < 1:
        raise ValueError("invalid block length or bootstrap count")
    n_blocks = (time + block_length - 1) // block_length
    draws = np.empty(n_boot)
    for b in range(n_boot):
        starts = rng.integers(0, time, size=(regions, n_blocks))
        indices = ((starts[:, :, None] + np.arange(block_length)) % time).reshape(
            regions, -1
        )[:, :time]
        draws[b] = np.take_along_axis(delta, indices, axis=1).mean()
    return _interval(delta.mean(), draws, regions)


def placebo_rank(real: float, placebo: np.ndarray) -> float:
    """Return fraction of placebo effects strictly below the observed effect."""
    placebo = _finite(placebo, 1)
    if not np.isfinite(real):
        raise ValueError("real effect must be finite")
    return float(np.mean(real > placebo))


def diebold_mariano(
    loss_a: np.ndarray, loss_b: np.ndarray, lag: int
) -> tuple[float, float]:
    """Compare loss_a-loss_b with Bartlett/Newey-West long-run variance.

    Args:
        loss_a: First finite loss sequence, in predeclared units.
        loss_b: Aligned second loss sequence.
        lag: Maximum autocovariance lag, strictly less than sample size.

    Returns:
        Normal-reference statistic and two-sided p-value. Identical losses give
        (0,1); nonzero constant differences give (NaN,NaN), an undefined variance
        status that the protocol serializes explicitly (never fabricated infinity).
    """
    a, b = _finite(loss_a, 1), _finite(loss_b, 1)
    if a.shape != b.shape or not 0 <= lag < len(a) or len(a) < 2:
        raise ValueError("aligned losses and a valid lag are required")
    d = a - b
    if np.ptp(d) == 0:
        return (0.0, 1.0) if d[0] == 0 else (float("nan"), float("nan"))
    mean = float(d.mean())
    centered = d - mean
    n = len(d)
    variance = float(centered @ centered / n)
    for k in range(1, lag + 1):
        variance += 2 * (1 - k / (lag + 1)) * float(centered[k:] @ centered[:-k] / n)
    if variance <= 0:
        return (0.0, 1.0) if mean == 0 else (float("nan"), float("nan"))
    statistic = mean / np.sqrt(variance / n)
    return float(statistic), float(2 * norm.sf(abs(statistic)))


def cliffs_delta(x: np.ndarray, y: np.ndarray) -> float:
    """Return P(x>y)-P(x<y), counting ties as zero."""
    x, y = _finite(x, 1), _finite(y, 1)
    return float(np.sign(x[:, None] - y).mean())


def _cliff_interval(
    x: np.ndarray, y: np.ndarray, rng: np.random.Generator, n_boot: int = 10000
) -> BootstrapResult:
    indices = rng.integers(0, len(x), size=(n_boot, len(x)))
    a, b = x[indices], y[indices]
    draws = np.sign(a[:, :, None] - b[:, None, :]).mean(axis=(1, 2))
    return _interval(cliffs_delta(x, y), draws, len(x))


def secondary_protocol(
    auc_pr: np.ndarray, losses: np.ndarray, rng: np.random.Generator
) -> SecondaryResult:
    """Run Friedman, Wilcoxon/Bonferroni, task-wise DM, then Cliff intervals.

    Args:
        auc_pr: Per-task AP [task,method], already aggregated over replicate seeds.
        losses: [task,time,method] squared binary-alarm errors (experiment plan).
        rng: Generator for paired region resampling of Cliff's95% intervals.

    Returns:
        Serializable dictionaries keyed by 'i:j'. DM entries retain task indices
        and use predeclared lag12. No follow-up runs if Friedman p>.05.
    """
    auc = _finite(auc_pr, 2)
    tasks, methods = auc.shape
    if tasks < 2 or methods < 3 or np.any((auc < 0) | (auc > 1)):
        raise ValueError("Friedman needs >=2 tasks and >=3 methods with valid AP")
    if np.all(np.ptp(auc, axis=1) == 0):
        statistic, p = 0.0, 1.0
    else:
        ranks = rankdata(-auc, axis=1, method="average")
        statistic, p = friedmanchisquare(*ranks.T)
    friedman = {
        "stat": float(statistic),
        "p_value": float(p),
        "significant": bool(p <= 0.05),
    }
    if p > 0.05:
        return SecondaryResult(friedman, {}, {}, {}, "friedman_not_significant")
    losses = _finite(losses, 3)
    if losses.shape[0] != tasks or losses.shape[2] != methods or losses.shape[1] <= 12:
        raise ValueError(
            "losses must align and include more than12 monthly observations"
        )
    if not np.isin(losses, [0.0, 1.0]).all():
        raise ValueError("secondary losses must be squared binary-alarm errors (0 or1)")
    pairs = list(combinations(range(methods), 2))
    alpha = 0.05 / len(pairs)
    wx, dm, cliffs = {}, {}, {}
    for i, j in pairs:
        key = f"{i}:{j}"
        if np.array_equal(auc[:, i], auc[:, j]):
            stat, pval = 0.0, 1.0
        else:
            stat, pval = wilcoxon(auc[:, i], auc[:, j], alternative="two-sided")
        wx[key] = {
            "stat": float(stat),
            "p_value": float(pval),
            "alpha": alpha,
            "significant": bool(pval < alpha),
        }
    for i, j in pairs:
        entries = []
        for task in range(tasks):
            stat, pval = diebold_mariano(losses[task, :, i], losses[task, :, j], 12)
            defined = np.isfinite(stat) and np.isfinite(pval)
            entries.append(
                {
                    "task": task,
                    "lag": 12,
                    "stat": stat if defined else None,
                    "p_value": pval if defined else None,
                    "status": "ok" if defined else "zero_hac_variance",
                }
            )
        dm[f"{i}:{j}"] = entries
    for i, j in pairs:
        ci = _cliff_interval(auc[:, i], auc[:, j], rng)
        cliffs[f"{i}:{j}"] = {
            "delta": ci.estimate,
            "low": ci.low,
            "high": ci.high,
            "n_units": ci.n_units,
        }
    return SecondaryResult(friedman, wx, dm, cliffs, None)
