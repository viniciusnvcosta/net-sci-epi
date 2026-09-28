"""Upper-tail calibration: pinned primitive, strict ties and independent nulls."""

import inspect
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import genpareto

from headd_l0.threshold import THRESHOLDS, calibrate, calibration_report, fit_tail


def test_gpd_parameters_match_reference():
    with np.load(Path(__file__).parent / "reference/evt.npz") as reference:
        fit = fit_tail(np.abs(reference["residuals"]))
        np.testing.assert_allclose(
            [fit.u, fit.shape, fit.scale], reference["gpd"], rtol=1e-7, atol=1e-9
        )
        assert fit.tail_fraction == pytest.approx(0.049)


def test_far_with_ties():
    null = np.repeat(np.arange(60, dtype=float), 10)
    threshold = THRESHOLDS["evt_gpd"](null, 1 / 60)
    assert np.mean(null > threshold) <= 1 / 60
    assert calibrate(np.ones(600), 1 / 60) == 1.0
    report = calibration_report(null, 1 / 60)
    assert report.n == 600
    assert report.achieved_far == np.mean(null > report.threshold)


@pytest.mark.parametrize(
    "bad", [np.array([]), np.array([np.nan]), np.array([np.inf]), np.ones((2, 3))]
)
def test_empty_or_nonfinite_rejected(bad):
    with pytest.raises(ValueError):
        calibrate(bad, 1 / 60)
    with pytest.raises(ValueError):
        fit_tail(bad)


@pytest.mark.parametrize("far", [0, -1, 1, np.nan])
def test_invalid_target_rejected(far):
    with pytest.raises(ValueError):
        calibrate(np.arange(600.0), far)


def test_insufficient_tail_reported():
    report = calibration_report(np.arange(60.0), 1 / 60)
    assert report.method == "empirical_insufficient_tail"
    assert report.threshold == 58.0
    assert report.achieved_far == pytest.approx(1 / 60)
    with pytest.raises(ValueError, match="insufficient_tail"):
        fit_tail(np.arange(60.0))


def test_no_evaluation_input():
    assert tuple(inspect.signature(calibrate).parameters) == (
        "null_scores",
        "target_far",
    )
    null = np.random.default_rng(5).exponential(size=2000)
    before = null.copy()
    threshold = calibrate(null, 1 / 60)
    np.testing.assert_array_equal(null, before)
    assert calibrate(null, 1 / 60) == threshold
    assert calibrate(null - 100, 1 / 60) == pytest.approx(threshold - 100, abs=1e-5)


def test_unconditional_tail_probability_and_empirical_adjustment():
    null = np.random.default_rng(80).exponential(size=4000)
    fit = fit_tail(null)
    report = calibration_report(null, 1 / 60)
    q = fit.u + genpareto.isf((1 / 60) / fit.tail_fraction, fit.shape, scale=fit.scale)
    empirical = np.sort(null)[len(null) - 1 - int(len(null) / 60)]
    assert report.threshold == pytest.approx(max(q, empirical))
    assert report.method == "evt_gpd"
    assert report.achieved_far <= 1 / 60


def test_far_on_independent_nulls():
    calibration_rng, evaluation_rng = [
        np.random.default_rng(s) for s in np.random.SeedSequence(321).spawn(2)
    ]
    report = calibration_report(calibration_rng.exponential(size=20000), 1 / 60)
    observed_far = np.mean(evaluation_rng.exponential(size=100000) > report.threshold)
    assert abs(observed_far - 1 / 60) < 1 / 300
    assert report.achieved_far <= report.target_far


def test_target_outside_fitted_tail_is_empirical():
    report = calibration_report(np.arange(2000.0), 0.2)
    assert report.method == "empirical_outside_tail"
    assert report.threshold == 1599.0


def test_degenerate_tail_is_reported():
    report = calibration_report(np.r_[np.zeros(5900), np.ones(100)], 1 / 60)
    assert report.method == "empirical_degenerate_tail"
    assert report.achieved_far <= 1 / 60


def test_far_bound_survives_floating_point_budget_rounding():
    target = np.nextafter(0.1, 0.0)
    report = calibration_report(np.arange(50.0), target)
    assert report.achieved_far <= target
    assert report.threshold == 45.0
