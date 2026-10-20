"""The E1 representation pipeline shares causal fits and component settings."""

from dataclasses import asdict
from pathlib import Path

import numpy as np

from headd_l0.e1 import _inputs, _score, build_arms
from headd_l0.run import load_config


def test_relational_arms_change_only_the_graph_representation():
    arms = build_arms(30)
    assert asdict(arms[0]) == {"name": "B0", "residuals": "base", "graph_id": None}
    assert asdict(arms[1]) == {
        "name": "B1*",
        "residuals": "reconciled",
        "graph_id": None,
    }
    assert asdict(arms[2]) == {
        "name": "B2",
        "residuals": "reconciled",
        "graph_id": "observed",
    }
    assert all(arm.residuals == "reconciled" and arm.graph_id for arm in arms[2:])
    assert len({arm.graph_id for arm in arms[2:]}) == 31


def test_scores_and_fitted_forecasts_have_no_future_data_dependency():
    cfg = load_config(Path("configs/e1_smoke.toml"))
    counts = np.load(Path("tests/reference/data.npz"))["counts"].T.copy()
    graphs, _, _ = _inputs(cfg, np.random.SeedSequence(42))
    seed = np.random.SeedSequence(123)
    arms = build_arms(30)[:3]
    original, shared, audit = _score(counts, cfg, arms, graphs, seed)
    changed = counts.copy()
    changed[:, 100:] += 10000
    later, later_shared, later_audit = _score(changed, cfg, arms, graphs, seed)
    assert audit["fit_valid"] and later_audit["fit_valid"]
    np.testing.assert_array_equal(original[:, :, :40], later[:, :, :40])
    assert not np.array_equal(original[:, :, 40:], later[:, :, 40:])
    for name in shared:
        np.testing.assert_array_equal(shared[name], later_shared[name])
    reverse, _, _ = _score(counts, cfg, tuple(reversed(arms)), graphs, seed)
    np.testing.assert_array_equal(original, reverse[::-1])
