"""Behaviour checks for the isolated profile-likelihood diagnostic."""

import importlib.util
from pathlib import Path

import numpy as np


def _harness():
    path = Path("docs/evidence/2026-10-28-l0-delivery/nb2_profile_harness.py")
    spec = importlib.util.spec_from_file_location("nb2_profile_harness", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_boundary_and_interior_and_invalid_input():
    """Fixed subdispersed data reach the boundary; invalid input fails closed."""
    h = _harness()
    boundary = h.fit_profile(np.full(120, 50))
    assert boundary["valid"] and boundary["boundary"]
    rng = np.random.default_rng(321)
    sample = rng.negative_binomial(10, 10 / 60, size=600)
    interior = h.fit_profile(sample)
    assert interior["valid"] and not interior["boundary"]
    assert 0.04 < interior["alpha"] < 0.2
    assert not h.fit_profile(np.zeros(120))["valid"]
