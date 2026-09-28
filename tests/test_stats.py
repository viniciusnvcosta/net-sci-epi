"""Independent resampling units, Bartlett HAC and gated follow-up inference."""

from pathlib import Path

import numpy as np
import pytest
from scipy.stats import norm, wilcoxon

from headd_l0.stats import (
    _cliff_interval,
    block_bootstrap,
    cliffs_delta,
    diebold_mariano,
    paired_bootstrap,
    placebo_rank,
    secondary_protocol,
    task_bootstrap,
)


def test_bootstrap_resamples_replicates():
    # Cell resampling would introduce variance; every intact replicate has mean5.
    delta = np.array([[0.0, 10.0], [10.0, 0.0], [2.0, 8.0]])
    result = paired_bootstrap(delta, np.random.default_rng(42), n_boot=500)
    assert (result.estimate, result.low, result.high, result.n_units) == (5, 5, 5, 3)


def test_task_bootstrap_keeps_method_pairs():
    baseline = np.linspace(0.20, 0.46, 13)
    delta = np.array(
        [-0.05, -0.03, -0.01, 0, 0.01, 0.02, 0.03, 0.04, -0.02, 0.05, 0.06, -0.04, 0.07]
    )
    paired = (baseline + delta) - baseline
    indices = np.random.default_rng(17).integers(0, 13, size=(101, 13))
    means = paired[indices].mean(axis=1)
    ci = task_bootstrap(paired, np.random.default_rng(17), n_boot=101)
    assert ci.n_units == 13 and np.ptp(means) > 0
    np.testing.assert_allclose(
        [ci.estimate, ci.low, ci.high],
        [paired.mean(), *np.quantile(means, [0.025, 0.975])],
    )


def test_block_bootstrap_preserves_region_blocks():
    delta = np.array([[0.0, 1.0, 2.0, 3.0], [100.0, 101.0, 102.0, 103.0]])
    # Whole circular blocks only rotate each region; cell or region resampling changes mean.
    ci = block_bootstrap(delta, 4, np.random.default_rng(4), n_boot=200)
    assert (ci.estimate, ci.low, ci.high, ci.n_units) == (51.5, 51.5, 51.5, 2)
    shorter = block_bootstrap(delta, 2, np.random.default_rng(4), n_boot=200)
    assert shorter.low < shorter.estimate < shorter.high
    assert shorter == block_bootstrap(delta, 2, np.random.default_rng(4), n_boot=200)


def test_placebo_ties_are_not_wins():
    assert placebo_rank(1.0, np.r_[np.zeros(29), 1.0]) == 29 / 30
    assert placebo_rank(0.0, np.zeros(30)) == 0


def test_hac_bartlett_manual():
    # d=[1,2,1,2], gamma0=.25, gamma1=-.1875, Bartlett weight=.5 -> HAC=.0625.
    stat, p = diebold_mariano(np.array([1.0, 2.0, 1.0, 2.0]), np.zeros(4), lag=1)
    assert stat == pytest.approx(12.0)
    assert p == pytest.approx(2 * norm.sf(12), rel=1e-12)
    reverse = diebold_mariano(np.zeros(4), np.array([1.0, 2.0, 1.0, 2.0]), lag=1)
    assert reverse[0] == -stat and reverse[1] == p


def test_dm_zero_variance_is_explicit():
    assert diebold_mariano(np.ones(20), np.ones(20), lag=12) == (0.0, 1.0)
    assert np.isnan(diebold_mariano(np.ones(20), np.zeros(20), lag=12)).all()


def test_cliff_ties_and_identical_samples():
    assert cliffs_delta(np.array([1, 1]), np.array([1, 1])) == 0
    assert cliffs_delta(np.array([1, 2]), np.array([2, 3])) == -0.75
    with np.load(Path(__file__).parent / "reference/stats.npz") as ref:
        assert cliffs_delta(ref["a"], ref["b"]) == pytest.approx(
            ref["cliffs"][0], abs=1e-12
        )


def test_friedman_stops_all_followups():
    rng = np.random.default_rng(42)
    state = repr(rng.bit_generator.state)
    result = secondary_protocol(np.ones((13, 3)), np.ones((13, 60, 3)), rng)
    assert result.stop_reason == "friedman_not_significant"
    assert result.friedman["p_value"] == 1
    assert result.wilcoxon == result.dm == result.cliffs == {}
    assert repr(rng.bit_generator.state) == state
    with np.load(Path(__file__).parent / "reference/stats.npz") as ref:
        original = secondary_protocol(ref["auc_pr"], np.ones((14, 60, 6)), rng)
    assert original.friedman["stat"] == pytest.approx(5.836734693877531, abs=1e-12)
    assert original.friedman["p_value"] == pytest.approx(0.32243093781203774, abs=1e-12)
    assert original.dm == original.cliffs == {}


def test_secondary_significant_followups_and_zero_wilcoxon():
    base = np.linspace(0.1, 0.3, 13)
    auc = np.column_stack([base, base, base + 0.5])
    losses = np.random.default_rng(8).integers(0, 2, size=(13, 60, 3)).astype(float)
    result = secondary_protocol(auc, losses, np.random.default_rng(42))
    assert result.stop_reason is None
    assert result.wilcoxon["0:1"]["p_value"] == 1
    assert result.wilcoxon["0:2"]["p_value"] == pytest.approx(
        wilcoxon(auc[:, 0], auc[:, 2]).pvalue
    )
    assert result.wilcoxon["0:2"]["alpha"] == pytest.approx(0.05 / 3)
    assert result.wilcoxon["0:2"]["significant"]
    assert len(result.dm["0:2"]) == 13
    expected = diebold_mariano(losses[0, :, 0], losses[0, :, 2], 12)
    np.testing.assert_allclose(
        [result.dm["0:2"][0]["stat"], result.dm["0:2"][0]["p_value"]], expected
    )
    assert result.cliffs["0:2"]["delta"] == -1
    assert result.cliffs["0:2"]["low"] == result.cliffs["0:2"]["high"] == -1


def test_invalid_inputs_rejected():
    with pytest.raises(ValueError):
        paired_bootstrap(np.ones(3), np.random.default_rng(1))
    with pytest.raises(ValueError):
        task_bootstrap(np.array([np.nan]), np.random.default_rng(1))
    with pytest.raises(ValueError):
        block_bootstrap(np.ones((2, 3)), 0, np.random.default_rng(1))
    with pytest.raises(ValueError):
        placebo_rank(1, np.array([]))
    with pytest.raises(ValueError):
        diebold_mariano(np.ones(10), np.ones(10), 12)
    with pytest.raises(ValueError):
        cliffs_delta(np.array([]), np.ones(2))
    with pytest.raises(ValueError):
        secondary_protocol(
            np.ones((4, 2)), np.ones((4, 60, 2)), np.random.default_rng(1)
        )


def test_dm_decimal_constant_differences_are_undefined():
    assert np.isnan(diebold_mariano(np.full(20, 0.1), np.zeros(20), lag=12)).all()


def test_cliff_interval_resamples_paired_regions():
    x = np.array([0.1, 0.3, 0.7, 0.8])
    y = np.array([0.2, 0.1, 0.5, 0.9])
    indices = np.random.default_rng(17).integers(0, 4, size=(101, 4))
    draws = []
    for row in indices:
        differences = [int(x[i] > y[j]) - int(x[i] < y[j]) for i in row for j in row]
        draws.append(sum(differences) / 16)
    expected = np.quantile(draws, [0.025, 0.975])
    ci = _cliff_interval(x, y, np.random.default_rng(17), n_boot=101)
    np.testing.assert_allclose([ci.low, ci.high], expected)
    assert ci.low < ci.high
