"""Literal behavior of CDADE fbfa609 synthetic.py, Apache-2.0; tests only.

Keeps the full-series amplitudes and persistent shift/drift defect. Never used
by the corrected pipeline. Compared byte-for-byte numerically to exported data.
"""

import numpy as np


def inject_original(series, rng):
    n = len(series)
    indices = rng.choice(n, size=max(1, round(0.05 * n)), replace=False)
    types = rng.integers(0, 3, size=len(indices))
    out = series.copy().astype(float)
    mask = np.zeros(n, dtype=bool)
    for idx, kind in zip(indices, types, strict=True):
        std = float(np.std(out)) or 1.0
        mean = float(np.mean(out)) or 1.0
        direction = rng.choice([-1.0, 1.0])
        if kind == 0:
            out[idx] += direction * 3.0 * std
            mask[idx] = True
        elif kind == 1:
            out[idx:] += direction * 2.0 * std
            mask[idx:] = True
        else:
            out[idx:] += (
                np.arange(1, n - idx + 1, dtype=float) * 0.05 * mean * direction
            )
            mask[idx:] = True
    return out, mask
