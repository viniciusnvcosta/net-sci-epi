"""Fixed G4 orchestration, causal summaries and immutable publication."""

import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from headd_l0 import sim_validation as validation
from headd_l0.simulate import SimConfig, simulate

MANIFEST = Path("tests/reference/gao_manifest.json")


def _rows():
    return [
        {
            "noise": noise,
            "label": label,
            "replicate": i,
            "CV": 0.0,
            "CV_valid": False,
            "AR1": 0.0,
            "AR1_valid": False,
        }
        for noise, label in validation.CELLS
        for i in range(64)
    ]


def _config(tmp_path, simulation=None):
    path = tmp_path / "g4.toml"
    path.write_text(
        f'run_id = "evidence"\noutput_dir = "{tmp_path}"\n'
        f'simulation_config = "{simulation or "configs/simulation.toml"}"\n'
        f'archive_path = "{tmp_path / "absent.zip"}"\n'
        f'supplement_path = "{tmp_path / "absent.pdf"}"\n'
    )
    return path


@pytest.mark.parametrize(
    "override",
    [
        "\nroot_seed = 7",
        "\ntesting_rate = 1",
        "\nepsilon = 0.2",
        "\nregions = 13",
        "\nreplicates_per_noise_label = 1",
        '\nprofile_id = "other"',
    ],
)
def test_config_rejects_frozen_design_overrides(tmp_path, override):
    path = _config(tmp_path)
    path.write_text(path.read_text() + override)
    with pytest.raises(ValueError, match="configuration"):
        validation._load_config(path)


@pytest.mark.parametrize(
    "old,new",
    [("42", "43"), ("64", "63"), ("0.5", "1.0"), ("P5-IMPL-2026-10-19-v1", "other")],
)
def test_referenced_design_is_frozen(tmp_path, old, new):
    simulation = tmp_path / "simulation.toml"
    simulation.write_text(Path("configs/simulation.toml").read_text().replace(old, new))
    with pytest.raises(ValueError, match="frozen"):
        validation._load_config(_config(tmp_path, simulation))


def test_seed_addresses_match_the_manifest():
    seeds = list(validation._monthly_seeds())
    assert validation.CELLS == (
        ("white", "T"),
        ("white", "N"),
        ("env", "T"),
        ("env", "N"),
        ("dem", "T"),
        ("dem", "N"),
    )
    assert len(seeds) == 384
    for cell, (noise, label) in enumerate(validation.CELLS):
        for replicate in range(64):
            entry = seeds[cell * 64 + replicate]
            assert entry[:3] == (noise, label, replicate)
            assert entry[3].entropy == 42
            assert entry[3].spawn_key == (1, cell, replicate)
    expected = np.random.SeedSequence(42).spawn(3)[1].spawn(6)[0].spawn(64)[0]
    assert np.array_equal(seeds[0][3].generate_state(8), expected.generate_state(8))


def test_window_excludes_onset_and_n_uses_design_month():
    manifest = json.loads(MANIFEST.read_text())
    month = validation._design_month(manifest)
    assert month == 75
    counts = np.zeros(132, dtype=int)
    counts[63:75] = np.arange(1, 13)
    stats = validation._window_statistics(counts, month)
    assert stats["window_start"] == 63
    assert stats["window_end_exclusive"] == 75
    assert stats["CV"] == pytest.approx(np.std(np.arange(1, 13), ddof=1) / 6.5)
    assert stats["AR1"] == pytest.approx(1)
    counts[75:] = 999999
    assert validation._window_statistics(counts, month) == stats
    assert stats["CV_valid"] and stats["AR1_valid"]


def test_undefined_statistics_have_validity_counts_and_null_medians():
    stats = validation._window_statistics(np.zeros(132), 75)
    assert not stats["CV_valid"] and not stats["AR1_valid"]
    summary = validation._summaries(pd.DataFrame(_rows()))
    assert len(summary) == 6
    for row in summary.to_dict("records"):
        assert row["requested"] == row["completed"] == 64
        assert row["CV_valid_count"] == row["AR1_valid_count"] == 0
        assert row["CV_invalid_count"] == row["AR1_invalid_count"] == 64
        assert pd.isna(row["CV_median"]) and pd.isna(row["AR1_median"])


def test_independent_n_is_not_the_t_twin():
    seeds = list(validation._monthly_seeds())
    t_seed, n_seed = seeds[0][3], seeds[64][3]
    t = simulate(SimConfig(), np.zeros((1, 1)), np.random.default_rng(t_seed))
    replay = simulate(SimConfig(), np.zeros((1, 1)), np.random.default_rng(t_seed))
    n = simulate(SimConfig(label="N"), np.zeros((1, 1)), np.random.default_rng(n_seed))
    zero = simulate(
        SimConfig(testing_rate=0), np.zeros((1, 1)), np.random.default_rng(t_seed)
    )
    one = simulate(
        SimConfig(testing_rate=1), np.zeros((1, 1)), np.random.default_rng(t_seed)
    )
    assert np.array_equal(t.counts, replay.counts)
    assert np.array_equal(n.counts, n.twin_counts)
    assert not np.array_equal(n.counts, t.twin_counts)
    assert t.onset.tolist() == [75] and n.onset.tolist() == [-1]
    assert all(validation._technical_checks(t, zero, one, 75, 72).values())


@pytest.mark.parametrize("change", ["missing", "duplicate", "wrong_id"])
def test_partial_or_duplicate_coverage_cannot_complete(change):
    rows = _rows()
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[-1] = rows[0]
    else:
        rows[-1]["replicate"] = 64
    with pytest.raises(ValueError, match="coverage"):
        validation._summaries(pd.DataFrame(rows))


def test_summaries_use_only_valid_values():
    rows = _rows()
    rows[0].update(CV=2, CV_valid=True, AR1=-0.5, AR1_valid=True)
    rows[1].update(CV=4, CV_valid=True)
    summary = validation._summaries(pd.DataFrame(rows)).iloc[0]
    assert summary["CV_median"] == 3 and summary["CV_valid_count"] == 2
    assert summary["AR1_median"] == -0.5 and summary["AR1_valid_count"] == 1


def test_publication_refuses_destination_appearing_at_commit(tmp_path):
    stage, destination = tmp_path / "stage", tmp_path / "destination"
    stage.mkdir()
    (stage / "manifest.json").write_bytes(b"candidate")
    destination.mkdir()
    (destination / "manifest.json").write_bytes(b"competitor")
    with pytest.raises(FileExistsError):
        validation._publish(stage, destination)
    assert (destination / "manifest.json").read_bytes() == b"competitor"
    assert (stage / "manifest.json").read_bytes() == b"candidate"


def test_publication_succeeds_without_destination(tmp_path):
    stage, destination = tmp_path / "stage", tmp_path / "destination"
    stage.mkdir()
    (stage / "evidence").write_bytes(b"closed evidence")
    validation._publish(stage, destination)
    assert not stage.exists()
    assert (destination / "evidence").read_bytes() == b"closed evidence"


def _fake_simulate(cfg, weights, rng):
    assert weights.shape == (1, 1) and cfg.epsilon == 0
    assert isinstance(rng, np.random.Generator)
    counts = np.tile(np.arange(1, 133), (1, 1))
    if cfg.testing_rate == 0:
        counts = counts * 0
    params = {
        "projection": {
            phase: {"steps": 700, "clipped_coordinates": [[0, 0]], "fraction": 0.0}
            for phase in ("burn_in", "outbreak", "twin")
        },
        "scientific_ratification": "pending",
        "G4": "pending",
        "interpretation_allowed": False,
    }
    return SimpleNamespace(
        label=cfg.label,
        counts=counts,
        twin_counts=counts.copy(),
        onset=np.array([75 if cfg.label == "T" else -1]),
        params=params,
    )


@pytest.mark.parametrize("source_status", ["passed", "pending", "failed"])
def test_complete_evidence_still_requires_scientific_review(
    tmp_path, monkeypatch, source_status
):
    monkeypatch.setattr(validation, "simulate", _fake_simulate)
    source = {
        "status": source_status,
        "source_archive_verification": source_status,
        "archive": {"status": "passed"},
        "supplement": {"status": source_status},
        "equation_fixture": {"status": "passed"},
        "G4": "pending",
        "interpretation_allowed": False,
        "reasons": [],
    }
    monkeypatch.setattr(validation, "verify_sources", lambda *args: source)
    output = validation.run_validation(_config(tmp_path))
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["run_status"] == "completed"
    assert manifest["G4"] == ("failed" if source_status == "failed" else "pending")
    assert manifest["scientific_review"] == "not_requested"
    assert manifest["interpretation_allowed"] is False
    assert manifest["source_checks"] == source
    assert (
        manifest["profile_manifest_status"]
        == json.loads(MANIFEST.read_text())["status"]
    )
    assert not (output / "inference.json").exists()
    assert len(pd.read_parquet(output / "replicates.parquet")) == 384
    assert len(pd.read_parquet(output / "summary.parquet")) == 6
    assert manifest["simulator_calls"] == 1152
    with np.load(output / "counts.npz", allow_pickle=False) as arrays:
        assert arrays["counts"].shape == (3, 2, 64, 132)
        assert arrays["twin_counts"].shape == (3, 2, 64, 132)
        assert arrays["noise"].tolist() == ["white", "env", "dem"]
        assert arrays["label"].tolist() == ["T", "N"]
        assert arrays["theta_zero_counts"].sum() == 0
    for name, sha in manifest["artifact_sha256"].items():
        assert validation._sha256(output / name) == sha


def test_cli_reports_pending_or_invalid_evidence(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(validation, "simulate", _fake_simulate)
    config = _config(tmp_path)
    monkeypatch.setattr("sys.argv", ["sim_validation", str(config)])
    assert validation.main() == 2
    assert "pending" in capsys.readouterr().err
    assert validation.main() != 0  # occupied destination
    assert "exists" in capsys.readouterr().err
    config.write_text("unknown = 1\n")
    assert validation.main() != 0
    assert "configuration" in capsys.readouterr().err


def test_noninteger_generation_cannot_publish(tmp_path, monkeypatch):
    def invalid(cfg, weights, rng):
        result = _fake_simulate(cfg, weights, rng)
        result.counts = result.counts.astype(float) + 0.5
        return result

    monkeypatch.setattr(validation, "simulate", invalid)
    with pytest.raises(ValueError, match="integer counts"):
        validation.run_validation(_config(tmp_path))
    assert not (tmp_path / "evidence").exists()
    stages = list(tmp_path.glob(".evidence-*"))
    assert len(stages) == 1
    assert json.loads((stages[0] / "failure.json").read_text())["G4"] == "failed"


def test_runtime_failure_keeps_staging_and_cli_reason(tmp_path, monkeypatch, capsys):
    def failing(*args):
        raise RuntimeError("realization white:T:0 failed")

    monkeypatch.setattr(validation, "simulate", failing)
    monkeypatch.setattr("sys.argv", ["sim_validation", str(_config(tmp_path))])
    assert validation.main() == 2
    assert "white:T:0 failed" in capsys.readouterr().err
    assert not (tmp_path / "evidence").exists()
    failure = next(tmp_path.glob(".evidence-*/failure.json"))
    assert json.loads(failure.read_text())["interpretation_allowed"] is False


def test_run_refuses_competing_destination_and_keeps_stage(tmp_path, monkeypatch):
    original_publish = validation._publish
    destination = tmp_path / "evidence"

    def race(stage, final):
        assert (stage / "manifest.json").exists()
        destination.mkdir()
        (destination / "manifest.json").write_bytes(b"competing evidence")
        original_publish(stage, final)

    monkeypatch.setattr(validation, "simulate", _fake_simulate)
    monkeypatch.setattr(validation, "_publish", race)
    with pytest.raises(FileExistsError):
        validation.run_validation(_config(tmp_path))
    assert (destination / "manifest.json").read_bytes() == b"competing evidence"
    assert len(list(tmp_path.glob(".evidence-*/failure.json"))) == 1


def test_technical_failure_is_never_scientifically_eligible(tmp_path, monkeypatch):
    def wrong_onset(cfg, weights, rng):
        result = _fake_simulate(cfg, weights, rng)
        result.onset = np.array([0])
        return result

    monkeypatch.setattr(validation, "simulate", wrong_onset)
    path = validation.run_validation(_config(tmp_path))
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["G4"] == "failed"
    assert manifest["technical_checks"]["onset_matches_design"] is False
    assert manifest["interpretation_allowed"] is False


def test_changed_realization_label_cannot_replace_t_coverage(tmp_path, monkeypatch):
    def null_substitution(cfg, weights, rng):
        result = _fake_simulate(cfg, weights, rng)
        result.label = "N"
        result.onset = np.array([-1])
        return result

    monkeypatch.setattr(validation, "simulate", null_substitution)
    with pytest.raises(ValueError, match="label"):
        validation.run_validation(_config(tmp_path))
    assert not (tmp_path / "evidence").exists()
