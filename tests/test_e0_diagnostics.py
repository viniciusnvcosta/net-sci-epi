"""Behavioral coverage for the read-only historical artifact audit."""

import hashlib
import json
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

from headd_l0.data import hierarchy
from headd_l0.e0_diagnostics import diagnose_e0

PINNED = (
    "manifest.json",
    "metrics.parquet",
    "far.parquet",
    "detector_fits.parquet",
    "pa_diagnostics.json",
)
TASKS = ["PA", *hierarchy().leaves]
ARMS = ["B1*", "zscore"]


def pin(source, evidence):
    value = json.loads(evidence.read_text())
    value["artifact_sha256"] = {
        name: hashlib.sha256((source / name).read_bytes()).hexdigest()
        for name in PINNED
    }
    evidence.write_text(json.dumps(value))


@pytest.fixture
def artifacts(tmp_path):
    source = tmp_path / "fixture"
    source.mkdir()
    evidence = tmp_path / "evidence.json"
    identity = {
        "run_id": "fixture",
        "git_sha": "abc",
        "reference_sha": "def",
        "root_seed": 42,
    }
    manifest = {
        "config": {"run_id": "fixture", "root_seed": 42},
        "git_sha": "abc",
        "reference_sha": "def",
        "baseline_id": "B1*",
        "gates": {
            "E0_star": {"status": "failed", "lower_bound": -0.2},
            "FAR": {"status": "failed"},
        },
        "interpretation_allowed": False,
    }
    (source / "manifest.json").write_text(json.dumps(manifest))
    evidence.write_text(json.dumps({**identity, "schema_version": 1}))
    metrics = []
    for i, task in enumerate(TASKS):
        for arm in ARMS:
            ap = 0.5 if arm == "zscore" else (0.51 if i == 13 else 0.38)
            metrics.append(
                {
                    "task": task,
                    "arm": arm,
                    "auc_pr": ap if i else np.nan,
                    "ap_status": "defined" if i else "single_class",
                    "n_positive": 36 if i else 72,
                    "n_negative": 36 if i else 0,
                    "prevalence": 0.5 if i else 1.0,
                    "window_start": 60,
                    "window_end": 131,
                    "in_gate": bool(i),
                    "fit_valid": True,
                    "fallback_used": False,
                    "null_model": "nb2",
                }
            )
    pd.DataFrame(metrics).to_parquet(source / "metrics.parquet")
    far = [
        {
            "task": task,
            "arm": arm,
            "threshold": 0.5,
            "target_far": 1 / 60,
            "tolerance": 1 / 300,
            "observed_far": 0.0,
            "achieved_far": 0.0,
            "n": 14400,
            "method": "evt_gpd",
            "passed": False,
            "null_model": "nb2",
            "fit_valid": True,
            "fallback_used": False,
        }
        for task in TASKS[1:]
        for arm in ARMS
    ]
    pd.DataFrame(far).to_parquet(source / "far.parquet")
    pd.DataFrame(
        [
            {
                "task": task,
                "converged": True,
                "valid": True,
                "alpha": 0.1,
                "train_start": 0,
                "train_end": 59,
                "fallback_used": False,
                "fallback_status": "not_needed",
            }
            for task in TASKS
        ]
    ).to_parquet(source / "fits.parquet")
    pd.DataFrame(
        [{"task": task, "detector": "pca", "seed": 1} for task in TASKS]
    ).to_parquet(source / "detector_fits.parquet")
    (source / "pa_diagnostics.json").write_text("{}")
    pd.DataFrame(
        [
            {
                "panel_id": f"{partition}:{i:03}",
                "partition": partition,
                "entropy": 42,
                "spawn_key": [stream, i],
                "model": "nb2",
                "all_fits_valid": True,
                "fallback_used": False,
            }
            for stream, partition in enumerate(("calibration", "evaluation"))
            for i in range(200)
        ]
    ).to_parquet(source / "null_partitions.parquet")
    np.savez(
        source / "forecast.npz",
        coefficients=np.zeros((14, 6)),
        alpha=np.ones(14),
        converged=np.ones(14, dtype=bool),
        means=np.ones((14, 132)),
    )
    mask = np.zeros((14, 132), dtype=bool)
    mask[0, 60:] = True
    mask[1:, 60:96] = True
    np.savez(
        source / "injection.npz",
        counts=np.ones((14, 132)),
        mask=mask,
        onset=np.full(14, 60),
    )
    for partition in ("injected", "calibration", "evaluation"):
        shape = (2, 14, 72) if partition == "injected" else (200, 2, 14, 72)
        np.savez(
            source / f"scores_{partition}.npz",
            scores=np.zeros(shape),
            arms=ARMS,
            tasks=TASKS,
            all_fits_valid=True,
            fallback_used=False,
        )
    pin(source, evidence)
    return source, evidence


def test_paired_regional_summary_excludes_pa(artifacts):
    source, evidence = artifacts
    report = diagnose_e0(source, evidence)
    assert report["interpretation_allowed"] is False
    assert [row["task"] for row in report["regional_ap"]] == TASKS[1:]
    assert len(report["regional_ap"]) == 13
    assert report["n_regions_b1_lower"] == 12
    assert report["mean_delta_ap"] == pytest.approx(-0.11)
    assert report["regional_ap"][0]["n_positive"] == 36
    assert report["regional_ap"][0]["prevalence"] == 0.5
    assert set(report["pinned_sha256"]) == set(
        json.loads(evidence.read_text())["artifact_sha256"]
    )
    assert report["historical_gates"]["E0_star"]["lower_bound"] == -0.2
    assert report["score_checks"]["ap_disagreements"]
    assert len(report["score_checks"]["pa_ap"]) == 2
    assert all(
        row["stored_ap"] is None and row["recomputed_ap"] is None
        for row in report["score_checks"]["pa_ap"]
    )


@pytest.mark.parametrize(
    "name",
    [
        "fits.parquet",
        "null_partitions.parquet",
        "forecast.npz",
        "injection.npz",
        "scores_injected.npz",
        "scores_calibration.npz",
        "scores_evaluation.npz",
    ],
)
def test_consumed_auxiliary_artifacts_have_observed_hashes(artifacts, name):
    source, evidence = artifacts
    before = diagnose_e0(source, evidence)
    path = source / name
    assert (
        before["observed_sha256"][name] == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert name not in before["pinned_sha256"]
    if name.endswith(".parquet"):
        pd.read_parquet(path).to_parquet(path, compression="gzip")
    else:
        with np.load(path, allow_pickle=False) as saved:
            arrays = {key: saved[key] for key in saved.files}
        np.savez_compressed(path, **arrays)
    after = diagnose_e0(source, evidence)
    assert after["observed_sha256"][name] != before["observed_sha256"][name]
    assert (
        after["observed_sha256"][name] == hashlib.sha256(path.read_bytes()).hexdigest()
    )
    assert after["pinned_sha256"] == before["pinned_sha256"]


def test_metric_row_order_is_irrelevant(artifacts):
    source, evidence = artifacts
    expected = diagnose_e0(source, evidence)["regional_ap"]
    path = source / "metrics.parquet"
    pd.read_parquet(path).iloc[::-1].to_parquet(path)
    pin(source, evidence)
    assert diagnose_e0(source, evidence)["regional_ap"] == expected


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "duplicate",
        "nonfinite",
        "unknown",
        "counts",
        "paired",
        "window",
        "prevalence",
    ],
)
def test_missing_duplicate_nonfinite_or_unknown_regional_rows_rejected(
    artifacts, defect
):
    source, evidence = artifacts
    path = source / "metrics.parquet"
    rows = pd.read_parquet(path)
    if defect == "missing":
        rows = rows.drop(2)
    elif defect == "duplicate":
        rows = pd.concat([rows, rows.iloc[[2]]])
    else:
        column, value = {
            "nonfinite": ("auc_pr", np.inf),
            "unknown": ("task", "OTHER"),
            "counts": ("n_positive", -1),
            "paired": ("n_positive", 35),
            "window": ("window_end", 130),
            "prevalence": ("prevalence", 0.1),
        }[defect]
        rows.loc[2, column] = value
    rows.to_parquet(path)
    pin(source, evidence)
    with pytest.raises(ValueError):
        diagnose_e0(source, evidence)


@pytest.mark.parametrize(
    "defect", ["missing", "changed", "identity", "reference", "seed", "hash_set"]
)
def test_missing_or_changed_pinned_artifact_rejected(artifacts, defect):
    source, evidence = artifacts
    if defect == "missing":
        (source / "pa_diagnostics.json").unlink()
    elif defect == "changed":
        (source / "pa_diagnostics.json").write_text('{"changed":true}')
    else:
        value = json.loads(evidence.read_text())
        key = {
            "identity": "run_id",
            "reference": "reference_sha",
            "seed": "root_seed",
            "hash_set": "artifact_sha256",
        }[defect]
        value[key] = {} if defect == "hash_set" else "wrong"
        evidence.write_text(json.dumps(value))
    with pytest.raises(ValueError):
        diagnose_e0(source, evidence)


@pytest.mark.parametrize(
    "alarms,expected", [(192, True), (288, True), (191, False), (289, False)]
)
def test_far_inclusive_boundaries(artifacts, alarms, expected):
    source, evidence = artifacts
    with np.load(source / "scores_evaluation.npz", allow_pickle=False) as saved:
        arrays = {key: saved[key] for key in saved.files}
    arrays["scores"][:, 0, 1].flat[:alarms] = 1.0
    np.savez(source / "scores_evaluation.npz", **arrays)
    row = next(
        row
        for row in diagnose_e0(source, evidence)["far"]
        if row["task"] == TASKS[1] and row["arm"] == "B1*"
    )
    assert row["recomputed_passed"] is expected
    assert row["recomputed_far"] == alarms / 14400
    assert row["stored_observed_far"] == 0.0
    assert row["observed_matches"] is (alarms == 0)


def test_read_only_and_favorable_fixture_never_authorize_inference(artifacts):
    source, evidence = artifacts
    path = source / "manifest.json"
    value = json.loads(path.read_text())
    value.update(
        interpretation_allowed=True,
        gates={"E0_star": {"status": "passed", "lower_bound": 0.1}},
    )
    path.write_text(json.dumps(value))
    rows = pd.read_parquet(source / "metrics.parquet")
    rows.loc[(rows.task != "PA") & (rows.arm == "B1*"), "auc_pr"] = 0.9
    rows.to_parquet(source / "metrics.parquet")
    pin(source, evidence)
    before = {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }
    report = diagnose_e0(source, evidence)
    assert report["mean_delta_ap"] > 0
    assert report["interpretation_allowed"] is False
    assert report["fits"]["n_valid"] == 14
    assert report["forecast"]["means_positive_finite"] is True
    assert report["partitions"]["disjoint_ids"] is True
    assert before == {
        p.relative_to(source): p.read_bytes() for p in source.rglob("*") if p.is_file()
    }


@pytest.mark.parametrize(
    "defect",
    ["score_axis", "score_finite", "partition_ids", "partition_streams", "labels"],
)
def test_invalid_auxiliary_artifact_rejected(artifacts, defect):
    source, evidence = artifacts
    if defect.startswith("partition"):
        path = source / "null_partitions.parquet"
        rows = pd.read_parquet(path)
        column = "panel_id" if defect == "partition_ids" else "spawn_key"
        rows.at[200, column] = rows.at[0, column]
        rows.to_parquet(path)
    else:
        path = source / (
            "injection.npz" if defect == "labels" else "scores_injected.npz"
        )
        with np.load(path, allow_pickle=False) as saved:
            arrays = {key: saved[key] for key in saved.files}
        if defect == "score_axis":
            arrays["tasks"] = arrays["tasks"][::-1]
        elif defect == "score_finite":
            arrays["scores"][0, 1, 0] = np.nan
        else:
            arrays["mask"][1, 60] = False
        np.savez(path, **arrays)
    with pytest.raises(ValueError):
        diagnose_e0(source, evidence)


@pytest.mark.parametrize(
    "defect", ["entropy", "duplicate_key", "duplicate_key_other_entropy"]
)
def test_null_partition_entropy_and_spawn_keys_rejected(artifacts, defect):
    source, evidence = artifacts
    path = source / "null_partitions.parquet"
    rows = pd.read_parquet(path)
    if defect != "duplicate_key":
        rows.at[1, "entropy"] = 43
    if defect != "entropy":
        rows.at[1, "spawn_key"] = rows.at[0, "spawn_key"]
    rows.to_parquet(path)
    with pytest.raises(ValueError):
        diagnose_e0(source, evidence)


def test_cli_emits_strict_json_or_nonzero_error(artifacts):
    source, evidence = artifacts
    cmd = [
        sys.executable,
        "-m",
        "headd_l0.e0_diagnostics",
        "--source",
        str(source),
        "--evidence",
        str(evidence),
    ]
    good = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert good.returncode == 0, good.stderr
    report = json.loads(good.stdout, parse_constant=lambda value: pytest.fail(value))
    assert report["schema_version"] == 1
    assert report["interpretation_allowed"] is False
    evidence.unlink()
    bad = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert bad.returncode != 0
    assert bad.stdout == ""
    assert bad.stderr.strip()
