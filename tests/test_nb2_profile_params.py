"""Regress the diagnostic candidate on the preserved difficult replicate."""

import importlib.util
from pathlib import Path

import numpy as np


def test_high_mean_failed_replicate_has_valid_profile():
    """The profile for seed 204, index 2 must complete its full grid."""
    path = Path("docs/evidence/2026-10-28-l0-delivery/nb2_profile_params.py")
    spec = importlib.util.spec_from_file_location("profile_params", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rng = np.random.default_rng(204)
    for _ in range(3):
        counts = rng.negative_binomial(1 / 0.0005, 1 / (1 + 0.0005 * 3300), 600)
    result = module.fit_profile(counts)
    assert result["valid"] and not result["boundary"]
    assert np.isfinite(result["alpha"]) and result["alpha"] > 0
