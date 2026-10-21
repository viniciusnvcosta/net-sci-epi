"""The report persists descriptive evidence before returning its scientific gate."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from test_stats import primary_comparisons

from headd_l0.data import hierarchy


def blocked_run(tmp_path):
    """Minimal preserved execution envelope, without fabricated bench metrics."""
    run = tmp_path / "blocked"
    run.mkdir()
    manifest = {
        "status": "blocked",
        "git_sha": "a" * 40,
        "interpretation_allowed": False,
        "bench": {"status": "not_executed"},
        "gates": {
            "E0": {"status": "inconclusive"},
            "E0_star": {"status": "failed"},
            "G4": {"status": "pending"},
            "scientific_ratification": {"status": "pending"},
            "D_REACH": {
                "status": "passed",
                "cells": [
                    {
                        "noise": "white",
                        "epsilon": 0.2,
                        "n": 200,
                        "reached": 165,
                        "fraction": 0.825,
                    }
                ],
            },
        },
    }
    (run / "manifest.json").write_text(json.dumps(manifest))
    return run, manifest


def test_blocked_cli_persists_descriptive_tables_figure_and_limitations(tmp_path):
    run, _ = blocked_run(tmp_path)
    result = subprocess.run(
        [sys.executable, "-m", "headd_l0.e1_report", str(run)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 2, result.stderr
    assert "interpretation blocked" in result.stdout.lower()
    report = run / "report"
    gates = pd.read_parquet(report / "gates.parquet")
    assert gates.loc[gates.gate == "E0_star", "status"].item() == "failed"
    assert not gates.interpretation_allowed.any()
    reach = pd.read_parquet(report / "reach.parquet")
    assert reach.n.tolist() == [200]
    assert reach.fraction.tolist() == [0.825]
    assert not reach.interpretation_allowed.any()
    assert (report / "reach.png").stat().st_size > 100
    limitations = (report / "limitations.md").read_text()
    assert "not_executed" in limitations and "B1*" in limitations
    assert not (report / "inference.json").exists()
    output = json.loads((report / "manifest.json").read_text())
    assert output["interpretation_allowed"] is False
    assert (
        output["source_manifest_sha256"]
        == hashlib.sha256((run / "manifest.json").read_bytes()).hexdigest()
    )


def test_report_refuses_tampered_artifact(tmp_path):
    from headd_l0.e1_report import export_report

    run, manifest = blocked_run(tmp_path)
    (run / "metrics.parquet").write_bytes(b"changed")
    manifest["artifact_sha256"] = {"metrics.parquet": "0" * 64}
    (run / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="hash"):
        export_report(run)
    assert not (run / "report").exists()


def test_notebook_executes_blocked_export_without_stored_outputs(tmp_path):
    run, _ = blocked_run(tmp_path)
    notebook = json.loads(Path("notebooks/e1_results.ipynb").read_text())
    assert notebook["nbformat"] == 4
    namespace = {"RUN_DIR": run}
    with pytest.raises(SystemExit) as exit_info:
        for cell in notebook["cells"]:
            if cell["cell_type"] == "code":
                assert cell["outputs"] == [] and cell["execution_count"] is None
                exec(  # noqa: S102 - execute the versioned notebook
                    compile("".join(cell["source"]), "e1_results.ipynb", "exec"),
                    namespace,
                )
    assert exit_info.value.code == 2
    assert (run / "report" / "limitations.md").exists()


def authorized_run(tmp_path):
    """All runner gates passed with complete independently measured null FAR."""
    run, manifest = blocked_run(tmp_path)
    source = primary_comparisons()
    frames = []
    for noise in ("white", "env", "dem"):
        for epsilon in (0.0, 0.05, 0.2):
            cell = source.loc[source.epsilon == (0 if epsilon == 0 else 0.2)].copy()
            cell["noise"], cell["epsilon"] = noise, epsilon
            cell["replicate_id"] = cell.replicate_id.map(
                lambda value, noise=noise, epsilon=epsilon: (
                    f"{noise}:{epsilon:g}:evaluation:T:{value.rsplit(':', 1)[1]}"
                )
            )
            frames.append(cell)
    frame = pd.concat(frames, ignore_index=True)
    frame.to_parquet(run / "comparisons.parquet", index=False)
    pd.DataFrame(
        [
            {
                "noise": noise,
                "epsilon": epsilon,
                "arm": arm,
                "task": task,
                "target_far": 1 / 60,
                "tolerance": 1 / 300,
                "passed": True,
                "complete": True,
                "observed_far": 1 / 60,
                "calibration_n": 14400,
                "n": 14400,
            }
            for noise in ("white", "env", "dem")
            for epsilon in (0.0, 0.05, 0.2)
            for arm in ["B0", "B1*", "B2", *(f"B2-placebo-{p:02d}" for p in range(30))]
            for task in hierarchy().leaves
        ]
    ).to_parquet(run / "far.parquet", index=False)
    manifest.update(
        status="completed",
        bench={"status": "completed"},
        interpretation_allowed=True,
        config={
            "name": "e1_bench",
            "n_transition": 200,
            "n_null": 200,
            "n_calibration": 200,
            "n_placebo_transition_per_cell": 100,
            "noise_types": ["white", "env", "dem"],
            "epsilon_levels": [0.0, 0.05, 0.2],
        },
        seeds={"bootstrap": {"entropy": 42, "spawn_key": [5]}},
        budget_policy={"placebo_transition_indices": list(range(100))},
    )
    for name in ("E0_star", "G4", "scientific_ratification", "D5", "FAR"):
        manifest["gates"][name] = {"status": "passed"}
    manifest["gates"]["D_REACH"]["cells"] = [
        {
            "noise": noise,
            "epsilon": epsilon,
            "n": 200,
            "reached": 0 if epsilon == 0 else 165,
            "fraction": 0 if epsilon == 0 else 0.825,
        }
        for noise in ("white", "env", "dem")
        for epsilon in (0.0, 0.05, 0.2)
    ]
    refresh_manifest(run, manifest)
    return run, manifest


def refresh_manifest(run, manifest):
    manifest["artifact_sha256"] = {
        name: hashlib.sha256((run / name).read_bytes()).hexdigest()
        for name in ("comparisons.parquet", "far.parquet")
    }
    (run / "manifest.json").write_text(json.dumps(manifest))


def test_authorized_export_adds_primary_inference_and_returns_zero(tmp_path):
    from headd_l0.e1_report import export_report

    run, _ = authorized_run(tmp_path)
    assert export_report(run) == 0
    inference = json.loads((run / "report" / "inference.json").read_text())
    assert {(cell["noise"], cell["epsilon"]) for cell in inference["cells"]} == {
        (noise, epsilon)
        for noise in ("white", "env", "dem")
        for epsilon in (0.0, 0.05, 0.2)
    }
    assert inference["cells"][1]["estimate"] == 4
    assert inference["cells"][1]["n_units"] == 200
    assert inference["cells"][1]["placebo_n_units"] == 100
    assert inference["hypothesis_supported"] is None


@pytest.mark.parametrize("alarm_count, observed", [(192, 192 / 14400), (288, 0.02)])
def test_authorized_export_accepts_both_inclusive_far_limits(
    tmp_path, alarm_count, observed
):
    from headd_l0.e1_report import export_report

    run, manifest = authorized_run(tmp_path)
    far = pd.read_parquet(run / "far.parquet")
    far["alarms"] = alarm_count
    far["observed_far"] = observed
    far.to_parquet(run / "far.parquet", index=False)
    refresh_manifest(run, manifest)
    assert export_report(run) == 0
    assert (run / "report" / "inference.json").exists()


def test_blocked_envelope_explicitly_marks_bench_sizes_unavailable(tmp_path):
    from headd_l0.e1_report import export_report

    # Mirrors the preserved Task 6 envelope: no effective_sizes and no bench run.
    run, _ = blocked_run(tmp_path)
    assert export_report(run) == 2
    sizes = pd.read_parquet(run / "report" / "effective_sizes.parquet")
    assert len(sizes) == 1
    assert sizes.bench_status.tolist() == ["not_executed"]
    assert sizes.availability.tolist() == ["unavailable"]
    assert sizes.provenance.tolist() == ["bench"]
    assert sizes.n.isna().all() and sizes.valid.isna().all()
    assert not sizes.interpretation_allowed.any()
    reach = pd.read_parquet(run / "report" / "reach.parquet")
    assert reach.provenance.tolist() == ["technical_reach"]
    assert reach.n.tolist() == [200]


def test_smoke_sizes_keep_their_technical_provenance(tmp_path):
    from headd_l0.e1_report import export_report

    run, manifest = blocked_run(tmp_path)
    manifest["config"] = {"name": "e1_smoke"}
    manifest["effective_sizes"] = [
        {
            "noise": "white",
            "epsilon": 0.2,
            "partition": "evaluation",
            "label": "T",
            "n": 2,
            "valid": 0,
        }
    ]
    (run / "manifest.json").write_text(json.dumps(manifest))
    assert export_report(run) == 2
    sizes = pd.read_parquet(run / "report" / "effective_sizes.parquet")
    assert sizes.provenance.tolist() == ["technical_smoke"]
    assert sizes.availability.tolist() == ["available"]
    assert sizes.n.tolist() == [2] and sizes.valid.tolist() == [0]


@pytest.mark.parametrize(
    "defect",
    [
        "reach",
        "reach_fraction",
        "far",
        "budget",
        "incomplete",
        "missing_hash",
        "missing_cell",
    ],
)
def test_manifest_permission_cannot_override_failed_or_missing_evidence(
    tmp_path, defect
):
    from headd_l0.e1_report import export_report

    run, manifest = authorized_run(tmp_path)
    if defect == "reach":
        manifest["gates"]["D_REACH"]["status"] = "failed"
    elif defect == "reach_fraction":
        next(
            row
            for row in manifest["gates"]["D_REACH"]["cells"]
            if row["epsilon"] == 0.2
        )["fraction"] = 0.4
    elif defect == "far":
        far = pd.read_parquet(run / "far.parquet")
        far.loc[0, "observed_far"] = 0.5
        far.to_parquet(run / "far.parquet", index=False)
    elif defect == "budget":
        manifest["budget_policy"]["placebo_transition_indices"][-1] = 100
    elif defect == "incomplete":
        manifest["status"] = "running"
    elif defect == "missing_cell":
        comparisons = pd.read_parquet(run / "comparisons.parquet")
        comparisons.loc[comparisons.epsilon != 0].to_parquet(
            run / "comparisons.parquet", index=False
        )
    refresh_manifest(run, manifest)
    if defect == "missing_hash":
        del manifest["artifact_sha256"]["comparisons.parquet"]
        (run / "manifest.json").write_text(json.dumps(manifest))
    assert export_report(run) == 2
    assert not (run / "report" / "inference.json").exists()


@pytest.mark.parametrize(
    "defect",
    [
        "incomplete_config",
        "bench_not_executed",
        "missing_region",
        "wrong_id",
        "missing_column",
    ],
)
def test_inference_evidence_failure_publishes_only_complete_blocked_report(
    tmp_path, defect
):
    from headd_l0.e1_report import export_report

    run, manifest = authorized_run(tmp_path)
    comparisons = pd.read_parquet(run / "comparisons.parquet")
    if defect == "incomplete_config":
        manifest["config"].update(noise_types=["white"], epsilon_levels=[0.0, 0.2])
        comparisons = comparisons.loc[
            (comparisons.noise == "white") & (comparisons.epsilon != 0.05)
        ]
        far = pd.read_parquet(run / "far.parquet")
        far.loc[(far.noise == "white") & (far.epsilon != 0.05)].to_parquet(
            run / "far.parquet", index=False
        )
        manifest["gates"]["D_REACH"]["cells"] = [
            row
            for row in manifest["gates"]["D_REACH"]["cells"]
            if row["noise"] == "white" and row["epsilon"] != 0.05
        ]
    elif defect == "bench_not_executed":
        manifest["bench"]["status"] = "not_executed"
    elif defect == "missing_region":
        comparisons = comparisons.iloc[1:]
    elif defect == "wrong_id":
        comparisons.loc[0, "replicate_id"] = "white:0:evaluation:T:9999"
    else:
        comparisons = comparisons.drop(columns="paired_eligible")
    comparisons.to_parquet(run / "comparisons.parquet", index=False)
    refresh_manifest(run, manifest)
    assert export_report(run) == 2
    report = run / "report"
    output = json.loads((report / "manifest.json").read_text())
    assert output["interpretation_allowed"] is False
    assert output["blocking_reasons"]
    assert not pd.read_parquet(report / "gates.parquet").interpretation_allowed.any()
    assert not (report / "inference.json").exists()
    assert all(
        hashlib.sha256((report / name).read_bytes()).hexdigest() == digest
        for name, digest in output["artifact_sha256"].items()
    )
    before = (report / "manifest.json").read_bytes()
    assert export_report(run) == 2
    assert (report / "manifest.json").read_bytes() == before


def test_interrupted_publication_leaves_no_partial_report_and_can_retry(
    tmp_path, monkeypatch
):
    from headd_l0.e1_report import export_report

    run, _ = authorized_run(tmp_path)
    real = pd.DataFrame.to_parquet
    writes = 0

    def interrupt_once(frame, *args, **kwargs):
        nonlocal writes
        writes += 1
        if writes == 2:
            raise OSError("simulated interrupted publication")
        return real(frame, *args, **kwargs)

    monkeypatch.setattr(pd.DataFrame, "to_parquet", interrupt_once)
    with pytest.raises(OSError, match="interrupted publication"):
        export_report(run)
    assert not (run / "report").exists()
    assert not list(run.glob(".report-*"))
    assert export_report(run) == 0
    assert (
        json.loads((run / "report" / "manifest.json").read_text())[
            "interpretation_allowed"
        ]
        is True
    )
