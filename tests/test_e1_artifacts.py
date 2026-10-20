"""FAR failure retains paired timing denominators and censored outcomes."""

from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0.e1 import build_arms
from headd_l0.e1_artifacts import _artifacts, _far, _manifest, _outcomes
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


def test_inactive_placebo_rows_are_absent_while_far_and_primary_pairing_stay_complete(
    tmp_path,
):
    arms = build_arms(30)
    names = [arm.name for arm in arms]
    base = names[:3]
    records = []
    scores = []
    shared = {"onset": []}
    for partition, label, index, active in (
        ("calibration", "N", 0, names),
        ("evaluation", "N", 0, names),
        ("evaluation", "T", 99, names),
        ("evaluation", "T", 100, base),
    ):
        records.append(
            {
                "replicate_id": f"{partition}:{label}:{index}",
                "noise": "white",
                "epsilon": 0.0,
                "partition": partition,
                "label": label,
                "fit_valid": True,
                "replicate_index": index,
                "active_arms": active,
            }
        )
        row = np.broadcast_to(np.arange(72), (len(active), 13, 72)).copy()
        scores.append(row)
        onsets = np.full(13, -1)
        if label == "T":
            onsets[0] = 80
        shared["onset"].append(onsets)

    _artifacts(
        tmp_path,
        load_config(Path("configs/e1_smoke.toml")),
        records,
        scores,
        shared,
        arms,
        {"observed": np.eye(13)},
    )
    score_rows = pd.read_parquet(tmp_path / "scores.parquet")
    replicates = pd.read_parquet(tmp_path / "replicates.parquet")
    metrics = pd.read_parquet(tmp_path / "metrics.parquet")
    comparisons = pd.read_parquet(tmp_path / "comparisons.parquet")
    far = pd.read_parquet(tmp_path / "far.parquet")
    assert set(score_rows.query("replicate_id == 'evaluation:T:100'").arm) == set(base)
    audited = replicates.query("replicate_id == 'evaluation:T:100'").iloc[0]
    assert audited.replicate_index == 100
    assert list(audited.active_arms) == base
    assert len(metrics.query("replicate_id == 'evaluation:T:99'")) == 33 * 13
    assert len(metrics.query("replicate_id == 'evaluation:T:100'")) == 3 * 13
    assert len(comparisons.query("replicate_id == 'evaluation:T:99'")) == 32 * 13
    assert len(comparisons.query("replicate_id == 'evaluation:T:100'")) == 2 * 13
    assert len(far) == 33 * 13
    placebo = comparisons.query(
        "reference.str.startswith('B2-placebo')", engine="python"
    )
    primary = comparisons.query("reference == 'B1*'")
    assert len(placebo) == 30 * 13
    assert len(primary) == 2 * 13


def test_manifest_audits_fixed_subset_and_effective_pair_denominators():
    from dataclasses import replace

    cfg = replace(
        load_config(Path("configs/e1_bench.toml")),
        calibration_dirs=("cal-white", "cal-env", "cal-dem"),
    )
    streams = {
        name: np.random.SeedSequence(42, spawn_key=(index,))
        for index, name in enumerate(
            ("data", "calibration", "evaluation", "placebos", "detectors", "bootstrap")
        )
    }
    manifest = _manifest(cfg, streams, build_arms(30), "reference")
    changed = _manifest(
        replace(cfg, n_placebo_transition_per_cell=99),
        streams,
        build_arms(30),
        "reference",
    )
    policy = manifest["budget_policy"]
    assert policy["placebo_transition_limit_per_cell"] == 100
    assert policy["placebo_transition_indices"] == list(range(100))
    assert policy["primary_B2_vs_B1_transition_n_per_cell"] == 200
    assert policy["B2_vs_placebo_transition_n_per_cell"] == 100
    assert policy["calibration_n_per_arm_cell"] == 200
    assert policy["null_evaluation_n_per_arm_cell"] == 200
    assert manifest["config"]["n_placebo_transition_per_cell"] == 100
    assert manifest["config_sha256"] != changed["config_sha256"]
