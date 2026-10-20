"""FAR failure retains paired timing denominators and censored outcomes."""

from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0.e1 import build_arms
from headd_l0.e1_artifacts import _far, _outcomes
from headd_l0.run import load_config


def test_far_failure_retains_all_arms_and_censored_timing():
    cfg = load_config(Path("configs/e1_smoke.toml"))
    arms = build_arms(30)
    records = pd.DataFrame(
        [
            {
                "replicate_id": partition + label,
                "noise": "white",
                "epsilon": 0.0,
                "partition": partition,
                "label": label,
                "fit_valid": True,
            }
            for partition, label in (
                ("calibration", "N"),
                ("evaluation", "N"),
                ("evaluation", "T"),
            )
        ]
    )
    scores = np.zeros((3, 33, 13, 72))
    scores[0] = np.arange(72)
    scores[1, :, :, -1] = 71  # One / 72 eligible months is inside the FAR band.
    scores[1, 2] = 71  # B2 alone fails on independent evaluation nulls.
    onsets = np.full((3, 13), -1)
    onsets[2, 0] = 80
    far = _far(cfg, records, scores, arms)
    metrics, comparisons = _outcomes(cfg, records, scores, onsets, arms, far)
    assert not far.query("arm == 'B2'").passed.any()
    assert far.query("arm != 'B2'").passed.all()
    assert len(metrics) == 2 * 33 * 13
    assert len(comparisons) == 32 * 13
    assert not comparisons.far_comparable.any()
    reached = metrics.query("label == 'T' and onset == 80")
    assert len(reached) == 33
    assert reached.censored.all()
    assert reached.timing_denominator.eq(1).all()
    assert reached.restricted_lead.eq(-13).all()
    absent = metrics.query("onset == -1")
    assert absent.timing_denominator.eq(0).all()
    assert absent.restricted_lead.isna().all()


def test_missing_forecasts_explicitly_block_timing_even_when_null_far_passes():
    cfg = load_config(Path("configs/e1_smoke.toml"))
    arms = build_arms(30)
    records = pd.DataFrame(
        [
            {
                "replicate_id": "failed-T",
                "noise": "white",
                "epsilon": 0.0,
                "partition": "evaluation",
                "label": "T",
                "fit_valid": False,
            }
        ]
    )
    from headd_l0.data import hierarchy

    far = pd.DataFrame(
        [
            {
                "noise": "white",
                "epsilon": 0.0,
                "arm": arm.name,
                "task": task,
                "threshold": 1.0,
                "passed": True,
            }
            for arm in arms
            for task in hierarchy().leaves
        ]
    )
    metrics, comparisons = _outcomes(
        cfg,
        records,
        np.full((1, 33, 13, 72), np.nan),
        np.full((1, 13), 80),
        arms,
        far,
    )
    assert metrics.timing_denominator.eq(1).all()
    assert metrics.restricted_lead.isna().all()
    assert not metrics.censored.any()
    assert not comparisons.paired_eligible.any()
    assert comparisons.blocked_reason.str.contains("D5").all()


def test_missing_calibration_preserves_available_scores_without_inventing_alarms():
    from headd_l0.data import hierarchy

    cfg = load_config(Path("configs/e1_smoke.toml"))
    arms = build_arms(30)
    records = pd.DataFrame(
        [
            {
                "replicate_id": "valid-T",
                "noise": "white",
                "epsilon": 0.0,
                "partition": "evaluation",
                "label": "T",
                "fit_valid": True,
            }
        ]
    )
    far = pd.DataFrame(
        [
            {
                "noise": "white",
                "epsilon": 0.0,
                "arm": arm.name,
                "task": task,
                "threshold": None,
                "passed": False,
            }
            for arm in arms
            for task in hierarchy().leaves
        ]
    )
    metrics, comparisons = _outcomes(
        cfg,
        records,
        np.zeros((1, 33, 13, 72)),
        np.full((1, 13), 80),
        arms,
        far,
    )
    assert metrics.score_available.all()
    assert not metrics.alarm_available.any()
    assert metrics.restricted_lead.isna().all()
    assert not metrics.censored.any()
    assert not comparisons.paired_eligible.any()
    assert comparisons.blocked_reason.str.contains("FAR").all()
