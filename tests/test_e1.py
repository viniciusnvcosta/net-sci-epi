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


def test_placebo_transition_cut_is_limited_to_the_first_100_evaluation_t():
    from headd_l0.e1 import arms_for_replicate

    cfg = load_config(Path("configs/e1_bench.toml"))
    arms = build_arms(cfg.n_placebos)
    assert tuple(
        a.name for a in arms_for_replicate(cfg, arms, "evaluation", "T", 0)
    ) == tuple(a.name for a in arms)
    assert len(arms_for_replicate(cfg, arms, "evaluation", "T", 99)) == 33
    assert tuple(
        a.name for a in arms_for_replicate(cfg, arms, "evaluation", "T", 100)
    ) == (
        "B0",
        "B1*",
        "B2",
    )
    assert len(arms_for_replicate(cfg, arms, "evaluation", "T", 199)) == 3
    assert len(arms_for_replicate(cfg, arms, "evaluation", "N", 199)) == 33
    assert len(arms_for_replicate(cfg, arms, "calibration", "N", 199)) == 33


def test_smoke_keeps_all_arms_and_subset_scoring_preserves_active_scores():
    from dataclasses import replace

    from headd_l0.e1 import arms_for_replicate

    cfg = load_config(Path("configs/e1_smoke.toml"))
    assert cfg.n_placebo_transition_per_cell is None
    counts = np.load(Path("tests/reference/data.npz"))["counts"].T.copy()
    graphs, _, _ = _inputs(cfg, np.random.SeedSequence(42))
    seed = np.random.SeedSequence(123)
    arms = build_arms(30)
    assert len(arms_for_replicate(cfg, arms, "evaluation", "T", 1)) == 33
    full, _, _ = _score(counts, cfg, arms, graphs, seed)
    cut_cfg = replace(cfg, n_placebo_transition_per_cell=1)
    reduced, _, audit = _score(
        counts,
        cut_cfg,
        arms,
        graphs,
        seed,
        {"partition": "evaluation", "label": "T", "replicate_index": 1},
    )
    assert reduced.shape == (3, 13, 72)
    assert audit["active_arms"] == ["B0", "B1*", "B2"]
    np.testing.assert_array_equal(reduced, full[:3])


def test_placebo_transition_limit_must_be_positive_and_at_most_transition_count():
    from dataclasses import replace

    cfg = load_config(Path("configs/e1_smoke.toml"))
    for invalid in (0, -1, 3, True, 1.5):
        try:
            replace(cfg, n_placebo_transition_per_cell=invalid)
        except ValueError:
            continue
        raise AssertionError(f"accepted invalid placebo transition limit: {invalid!r}")


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
