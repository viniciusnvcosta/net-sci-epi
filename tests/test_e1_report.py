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
    frame = primary_comparisons()
    frame.to_parquet(run / "comparisons.parquet", index=False)
    pd.DataFrame(
        [
            {
                "noise": "white",
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
            for epsilon in (0.0, 0.2)
            for arm in ["B0", "B1*", "B2", *(f"B2-placebo-{p:02d}" for p in range(30))]
            for task in hierarchy().leaves
        ]
    ).to_parquet(run / "far.parquet", index=False)
    manifest.update(
        status="completed",
        interpretation_allowed=True,
        config={
            "name": "e1_bench",
            "n_transition": 200,
            "n_null": 200,
            "n_calibration": 200,
            "n_placebo_transition_per_cell": 100,
            "noise_types": ["white"],
            "epsilon_levels": [0.0, 0.2],
        },
        seeds={"bootstrap": {"entropy": 42, "spawn_key": [5]}},
        budget_policy={"placebo_transition_indices": list(range(100))},
    )
    for name in ("E0_star", "G4", "scientific_ratification", "D5", "FAR"):
        manifest["gates"][name] = {"status": "passed"}
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
    assert inference["cells"][1]["estimate"] == 4
    assert inference["cells"][1]["n_units"] == 200
    assert inference["cells"][1]["placebo_n_units"] == 100
    assert inference["hypothesis_supported"] is None


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
        manifest["gates"]["D_REACH"]["cells"][0]["fraction"] = 0.4
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
