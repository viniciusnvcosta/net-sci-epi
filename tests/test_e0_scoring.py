"""Null partition isolation and approved E0* scoring integration."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from headd_l0.run import E0Config


def test_null_partitions_preserve_train_and_coherent_integer_counts():
    from headd_l0 import e0_scoring as run
    from headd_l0.forecast import fit_nb2

    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T
    counts = np.vstack((leaves.sum(axis=0), leaves))
    fit = fit_nb2(counts)
    assert hasattr(run, "_null_panels"), "null partition builder missing"
    calibration, evaluation = np.random.SeedSequence(42).spawn(2)
    first = run._null_panels(fit, counts, calibration, 200)
    second = run._null_panels(fit, counts, evaluation, 200)
    assert first[:, 1:].shape == (200, 13, 132)
    assert np.issubdtype(first.dtype, np.integer) and (first >= 0).all()
    np.testing.assert_array_equal(first[:, 0], first[:, 1:].sum(axis=1))
    np.testing.assert_array_equal(
        first[:, :, :60], np.broadcast_to(counts[:, :60], (200, 14, 60))
    )
    assert not np.array_equal(first[:, :, 60:], second[:, :, 60:])
    np.testing.assert_array_equal(
        first, run._null_panels(fit, counts, calibration, 200)
    )


def test_e0_scoring_real_components_preserve_stream_and_report_prevalence(tmp_path):
    from headd_l0 import e0_scoring as run
    from headd_l0.inject import InjectionConfig, inject_original_bounded

    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T
    assert hasattr(run, "_score_e0"), "scoring integration missing"
    cfg = E0Config("scored", 42, tmp_path, tmp_path)
    result = run._score_e0(cfg, leaves, n=1)
    manifest = json.loads((result / "manifest.json").read_text())
    assert manifest["status"] == "completed"
    assert manifest["settings"].get("feature_names") == [
        "residual",
        "residual_lag1",
        "residual_change",
    ]
    assert manifest["component_evidence"]["passed"]
    assert manifest["component_evidence"]["git_sha"] == manifest["git_sha"]
    assert not manifest["interpretation_allowed"]
    assert manifest["fallback_status"] == "pending_specification_not_used"
    saved = np.load(result / "injection.npz")
    direct = inject_original_bounded(
        leaves, np.random.default_rng(42), InjectionConfig()
    )
    np.testing.assert_array_equal(saved["counts"], direct.counts)
    assert (saved["counts"] < 0).sum() == 110
    metrics = pd.read_parquet(result / "metrics.parquet")
    assert len(metrics) == 28
    assert metrics.loc[metrics.task == "PA", "auc_pr"].isna().all()
    np.testing.assert_allclose(metrics.prevalence, metrics.n_positive / 72)
    assert (metrics.window_start == 60).all() and (metrics.window_end == 131).all()
    far = pd.read_parquet(result / "far.parquet")
    assert len(far) == 26 and set(far.arm) == {"B1*", "zscore"}
    assert (far.target_far == 1 / 60).all() and (far.tolerance == 1 / 300).all()
    ids = pd.read_parquet(result / "null_partitions.parquet")
    assert ids.panel_id.is_unique
    assert set(ids.partition) == {"calibration", "evaluation"}
    with pytest.raises(FileExistsError):
        run._score_e0(cfg, leaves, n=1)


def test_e0_scoring_waits_for_pa_decision(tmp_path, monkeypatch):
    from headd_l0 import e0_scoring as run

    assert hasattr(run, "_score_e0"), "scoring integration missing"
    monkeypatch.setattr(run, "DECISION_SHA", "0" * 40)
    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T
    with pytest.raises(ValueError, match="decision"):
        run._score_e0(E0Config("blocked", 42, tmp_path, tmp_path), leaves, n=1)
    assert not (tmp_path / "blocked").exists()


def test_null_nonconvergence_is_reported_before_scores(tmp_path):
    from headd_l0 import e0_scoring as run

    assert hasattr(run, "_score_e0"), "scoring integration missing"
    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T.copy()
    leaves[0] = 0
    result = run._score_e0(E0Config("failed", 42, tmp_path, tmp_path), leaves, n=1)
    manifest = json.loads((result / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert "ARAGUAIA" in manifest["failed_fits"]
    assert manifest["failure_reason"] == "D5_forecast_unavailable"
    assert manifest["fallback_status"] == "pending_specification"
    assert not (result / "metrics.parquet").exists()
    assert not (result / "null_calibration.npz").exists()
    fits = pd.read_parquet(result / "fits.parquet")
    assert not fits.loc[fits.task == "ARAGUAIA", "valid"].item()


def test_calibration_thresholds_are_independent_of_evaluation_nulls():
    from headd_l0.e0_scoring import _calibrate_scores

    rng = np.random.default_rng(9)
    calibration = rng.exponential(size=(10, 2, 1, 72))
    evaluation = rng.exponential(size=(10, 2, 1, 72))
    first = _calibrate_scores(calibration, evaluation, ["region"])
    second = _calibrate_scores(calibration, evaluation + 1e6, ["region"])
    np.testing.assert_array_equal(first.threshold, second.threshold)
    np.testing.assert_array_equal(first.achieved_far, second.achieved_far)
    assert (second.observed_far == 1).all()
    assert (first.observed_far < 1).all()


def test_null_fit_uses_training_only():
    from headd_l0.e0_scoring import _null_panels
    from headd_l0.forecast import fit_nb2

    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T
    counts = np.vstack((leaves.sum(axis=0), leaves))
    changed = counts.copy()
    changed[:, 60:] *= 1000
    first = _null_panels(fit_nb2(counts), counts, np.random.SeedSequence(5), 2)
    second = _null_panels(fit_nb2(changed), changed, np.random.SeedSequence(5), 2)
    np.testing.assert_array_equal(first, second)


def test_component_evidence_rejects_code_changes_during_checks(tmp_path, monkeypatch):
    from types import SimpleNamespace

    from headd_l0 import e0_scoring

    root = tmp_path / "repo"
    (root / "src/headd_l0").mkdir(parents=True)
    (root / "tests").mkdir()
    source = root / "src/headd_l0/e0_scoring.py"
    source.write_text("before")
    (root / "pyproject.toml").write_text("")
    (root / "uv.lock").write_text("")
    monkeypatch.setattr(e0_scoring, "__file__", str(source))

    def change_source(*args, **kwargs):
        source.write_text("after")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(e0_scoring.subprocess, "run", change_source)
    monkeypatch.setattr(
        e0_scoring.subprocess, "check_output", lambda *args, **kwargs: "abc\n"
    )
    evidence = e0_scoring._component_evidence(tmp_path)
    assert not evidence["passed"]
    assert evidence["exit_code"] == 0


def test_scoring_rejects_stale_component_evidence(tmp_path, monkeypatch):
    from headd_l0 import e0_scoring

    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T
    monkeypatch.setattr(
        e0_scoring,
        "_component_evidence",
        lambda path: {"passed": True, "source_sha256": "stale"},
    )
    with pytest.raises(ValueError, match="component evidence"):
        e0_scoring._score_e0(E0Config("stale", 42, tmp_path, tmp_path), leaves, n=1)
    manifest = json.loads((tmp_path / "stale/manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert not (tmp_path / "stale/metrics.parquet").exists()
