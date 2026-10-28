import json
from types import SimpleNamespace

import numpy as np
import pytest

from headd_l0.exploratory_run import run_experiment


def test_experiment_preserves_inputs_and_blocks_inference(tmp_path, monkeypatch):
    from headd_l0 import exploratory_run as runner

    matrix = np.eye(13)
    placebo = np.repeat(matrix[None, :, :], 30, axis=0)
    monkeypatch.setattr(
        runner,
        "_verify_budget",
        lambda _: {"n_transition": 1, "placebo_ids": [0, 1, 2]},
    )
    monkeypatch.setattr(
        runner, "load_graphs", lambda _: (matrix, matrix, matrix, placebo)
    )
    monkeypatch.setattr(runner, "load_hazards", lambda _: (0.1,) * 13)
    seen = []

    def simulate(weights, epsilon, label, partition, index, hazards):
        seen.append((weights, epsilon, label, partition, index))
        return SimpleNamespace(counts=np.zeros((13, 132)), onset=np.full(13, -1))

    monkeypatch.setattr(runner, "simulate_replicate", simulate)
    monkeypatch.setattr(runner, "score_replicate", lambda *_: np.zeros((7, 13, 72)))
    budget = tmp_path / "budget.json"
    budget.write_text(json.dumps({"n_transition": 1, "placebo_ids": [0, 1, 2]}))
    manifest = tmp_path / "candidate.json"
    manifest.write_text("{}")
    (tmp_path / "manifest.json").write_text("{}")
    output = tmp_path / "output"
    run_experiment(manifest, tmp_path, budget, output)
    result = json.loads((output / "manifest.json").read_text())
    assert result["interpretation_allowed"] is False
    assert result["status"] == "exploratory"
    assert len(seen) == 802
    assert all(x[0] is matrix for x in seen)
    assert (output / "far.csv").is_file()
    with np.load(output / "scores.npz", allow_pickle=False) as saved:
        assert saved["epsilon_0_calibration_N"].shape == (200, 7, 13, 72)
        assert saved["epsilon_0_evaluation_N"].shape == (200, 7, 13, 72)
    assert result["source_sha256"]
    assert result["seed_addresses"]
    assert result["arm_names"] == [
        "B1*",
        "B2",
        "B2-P4",
        "B2-placebo-00",
        "B2-placebo-01",
        "B2-placebo-02",
        "zscore",
    ]
    assert len(result["region_names"]) == 13
    with pytest.raises(FileExistsError):
        run_experiment(manifest, tmp_path, budget, output)


def test_experiment_failure_never_publishes(tmp_path, monkeypatch):
    from headd_l0 import exploratory_run as runner

    matrix = np.eye(13)
    monkeypatch.setattr(
        runner,
        "_verify_budget",
        lambda _: {"n_transition": 1, "placebo_ids": [0, 1, 2]},
    )
    monkeypatch.setattr(
        runner,
        "load_graphs",
        lambda _: (matrix, matrix, matrix, np.repeat(matrix[None], 30, axis=0)),
    )
    monkeypatch.setattr(runner, "load_hazards", lambda _: (0.1,) * 13)
    monkeypatch.setattr(
        runner,
        "simulate_replicate",
        lambda *_: (_ for _ in ()).throw(ValueError("invalid NB2")),
    )
    with pytest.raises(ValueError, match="invalid NB2"):
        run_experiment(tmp_path / "m", tmp_path, tmp_path / "budget", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_source_change_during_experiment_fails_closed(tmp_path, monkeypatch):
    from headd_l0 import exploratory_run as runner

    matrix = np.eye(13)
    monkeypatch.setattr(
        runner,
        "_verify_budget",
        lambda _: {"n_transition": 1, "placebo_ids": [0, 1, 2]},
    )
    monkeypatch.setattr(
        runner,
        "load_graphs",
        lambda _: (matrix, matrix, matrix, np.repeat(matrix[None], 30, axis=0)),
    )
    monkeypatch.setattr(runner, "load_hazards", lambda _: (0.1,) * 13)
    monkeypatch.setattr(
        runner,
        "simulate_replicate",
        lambda *_: SimpleNamespace(counts=np.zeros((13, 132)), onset=np.full(13, -1)),
    )
    monkeypatch.setattr(runner, "score_replicate", lambda *_: np.zeros((7, 13, 72)))
    identities = iter([{"file": "before"}, {"file": "after"}])
    monkeypatch.setattr(runner, "_source_identity", lambda: next(identities))
    with pytest.raises(ValueError, match="source changed"):
        run_experiment(tmp_path / "m", tmp_path, tmp_path / "budget", tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_budget_rejects_failed_pilot(tmp_path, monkeypatch):
    import hashlib

    from headd_l0 import exploratory_run as runner

    pilot = tmp_path / "pilot.json"
    pilot.write_text(json.dumps({"status": "failed"}))
    budget = tmp_path / "budget.json"
    budget.write_text(
        json.dumps(
            {
                "n_transition": 1,
                "placebo_ids": [0],
                "pilot_manifest": str(pilot),
                "pilot_manifest_sha256": hashlib.sha256(pilot.read_bytes()).hexdigest(),
            }
        )
    )

    def git(cmd, **kwargs):
        if "--show-toplevel" in cmd:
            return SimpleNamespace(stdout=str(tmp_path))
        return SimpleNamespace(stdout=budget.read_bytes())

    monkeypatch.setattr(runner.subprocess, "run", git)
    with pytest.raises(ValueError, match="pilot"):
        runner._verify_budget(budget)


def test_pilot_records_failure_without_claiming_completion(tmp_path, monkeypatch):
    from headd_l0 import exploratory_run as runner

    matrix = np.eye(13)
    monkeypatch.setattr(
        runner,
        "load_graphs",
        lambda _: (matrix, matrix, matrix, np.repeat(matrix[None], 30, axis=0)),
    )
    monkeypatch.setattr(runner, "load_hazards", lambda _: (0.1,) * 13)
    monkeypatch.setattr(
        runner,
        "measure_pilot",
        lambda *_: (_ for _ in ()).throw(ValueError("invalid NB2")),
    )
    manifest = tmp_path / "candidate.json"
    manifest.write_text("{}")
    (tmp_path / "manifest.json").write_text("{}")
    output = tmp_path / "pilot"
    runner.run_pilot(manifest, tmp_path, output)
    result = json.loads((output / "manifest.json").read_text())
    assert result["status"] == "pilot_failed"
    assert result["interpretation_allowed"] is False
    assert "invalid NB2" in result["error"]


def test_pilot_projection_labels_extrapolation(tmp_path, monkeypatch):
    from headd_l0 import exploratory_run as runner

    matrix = np.eye(13)
    monkeypatch.setattr(
        runner,
        "load_graphs",
        lambda _: (matrix, matrix, matrix, np.repeat(matrix[None], 30, axis=0)),
    )
    monkeypatch.setattr(runner, "load_hazards", lambda _: (0.1,) * 13)
    arms = {
        key: 2.0
        for key in [
            "B1*",
            "B2",
            "B2-P4",
            "B2-placebo-00",
            "B2-placebo-01",
            "B2-placebo-02",
            "zscore",
        ]
    }
    rows = [
        {
            "epsilon": e,
            "label": label,
            "simulation_seconds": 1.0,
            "scoring_seconds": 3.0,
            "arm_seconds": arms,
        }
        for e in (0.0, 0.2)
        for label in ("T", "N")
    ]
    monkeypatch.setattr(runner, "measure_pilot", lambda *_: rows)
    manifest = tmp_path / "candidate.json"
    manifest.write_text("{}")
    (tmp_path / "manifest.json").write_text("{}")
    out = tmp_path / "pilot"
    runner.run_pilot(manifest, tmp_path, out)
    result = json.loads((out / "manifest.json").read_text())
    assert result["status"] == "pilot_complete"
    assert result["d_cost_status"] == "pending"
    assert result["cost_projection"]["seconds"] > 0
    assert "extrapol" in result["cost_projection"]["limitation"]
