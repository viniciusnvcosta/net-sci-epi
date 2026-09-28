"""Finite layer-0 anomalies following D-GT1; PA stays coherent under D5.

CDADE fbfa609 synthetic.py (Apache-2.0) supplies event types, magnitudes and
index/type/direction draw order. Durations are drawn after direction. Proposed
onsets are moved left only when needed to fit the full event in the test window.
Amplitudes retain the original evolving full-series std/mean: this is a ground
truth generator, never a fitted feature. Negative introduced counts are retained.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class InjectionConfig:
    """Original magnitudes with finite durations and an inclusive test window."""

    contamination: float = 0.05
    spike_magnitude: float = 3.0
    level_shift_delta: float = 2.0
    drift_slope: float = 0.05
    min_duration: int = 3
    max_duration: int = 6
    onset_months: tuple[int, int] = (60, 131)


@dataclass(frozen=True)
class InjectionEvent:
    """One event on a leaf (zero-based); kind 0=spike, 1=shift, 2=drift."""

    region: int
    kind: int
    proposed_onset: int
    onset: int
    duration: int
    direction: float
    amplitude: float


@dataclass(frozen=True)
class InjectionResult:
    """PA-first coherent panel, union labels, first onsets and event provenance."""

    counts: np.ndarray
    mask: np.ndarray
    onset: np.ndarray
    seed_region: int | None
    events: tuple[InjectionEvent, ...]


def inject_original_bounded(
    counts: np.ndarray, rng: np.random.Generator, cfg: InjectionConfig
) -> InjectionResult:
    """Inject into 13 leaves, then derive PA counts and the union of their masks.

    Args:
        counts: Finite [13, 132] leaf counts in canonical order, never mutated.
        rng: Shared stream, advanced through each leaf; no independent PA draw.
        cfg: Magnitudes, event count and finite durations.

    Returns:
        [14,132] counts/mask and [14] first onsets (-1 if absent). Overlaps add;
        adjusted onsets may coincide. A single-class PA is reported, not redrawn.
    """
    values = np.asarray(counts, dtype=float)
    start, end = cfg.onset_months
    n_events = max(1, round(cfg.contamination * 132))
    if (
        values.shape != (13, 132)
        or not np.isfinite(values).all()
        or not 60 <= start <= end <= 131
        or not 1 <= cfg.min_duration <= cfg.max_duration <= end - start + 1
        or not 0 < cfg.contamination <= 1
        or n_events > end - start + 1
    ):
        raise ValueError("invalid layer-0 panel or injection configuration")
    out = values.copy()
    mask = np.zeros(values.shape, dtype=bool)
    events = []
    for region in range(13):
        proposed = rng.choice(np.arange(start, end + 1), size=n_events, replace=False)
        kinds = rng.integers(0, 3, size=n_events)
        for raw_onset, kind in zip(proposed, kinds, strict=True):
            direction = float(rng.choice([-1.0, 1.0]))
            duration = (
                1
                if kind == 0
                else int(rng.integers(cfg.min_duration, cfg.max_duration + 1))
            )
            onset = min(int(raw_onset), end - duration + 1)
            if kind == 2:
                amplitude = (
                    direction * cfg.drift_slope * (float(out[region].mean()) or 1.0)
                )
                offset = np.arange(1, duration + 1, dtype=float) * amplitude
            else:
                magnitude = cfg.spike_magnitude if kind == 0 else cfg.level_shift_delta
                amplitude = direction * magnitude * (float(out[region].std()) or 1.0)
                offset = amplitude
            out[region, onset : onset + duration] += offset
            mask[region, onset : onset + duration] = True
            events.append(
                InjectionEvent(
                    region,
                    int(kind),
                    int(raw_onset),
                    onset,
                    duration,
                    direction,
                    amplitude,
                )
            )
    panel = np.vstack([out.sum(axis=0), out])
    labels = np.vstack([mask.any(axis=0), mask])
    onsets = np.where(labels.any(axis=1), labels.argmax(axis=1), -1)
    return InjectionResult(panel, labels, onsets, None, tuple(events))
