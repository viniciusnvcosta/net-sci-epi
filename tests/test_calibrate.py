"""Training-only endemic fitting, fixed streams, and reproducible artifacts."""

import json
import subprocess
from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

from headd_l0.data import LEAVES

ROOT = Path(__file__).parents[1]


def _seeds():
    calibration = np.random.SeedSequence(42).spawn(3)[2]
    return tuple(tuple(region.spawn(128)) for region in calibration.spawn(13))


def test_calibration_uses_only_training_counts_and_returns_canonical_order():
    from headd_l0.calibrate import calibrate

    counts = np.repeat(np.arange(100, 1400, 100)[:, None], 132, axis=1)
    changed = counts.copy()
    changed[:, 60:] = 10**9
    result = calibrate(counts[::-1], LEAVES[::-1], _seeds(), noise="env")
    future_changed = calibrate(changed, LEAVES, _seeds(), noise="env")
    assert result.names == LEAVES
    np.testing.assert_array_equal(result.target_medians, np.arange(100, 1400, 100))
    for field in ("hazards", "simulated_medians", "errors", "iterations"):
        np.testing.assert_array_equal(
            getattr(result, field), getattr(future_changed, field)
        )
    assert (result.hazards > 0).all()
    assert (result.hazards <= 1 / 7).all()
    assert (result.iterations <= 30).all()
    np.testing.assert_array_equal(
        result.errors, result.simulated_medians - result.target_medians
    )
    assert (np.abs(result.errors) <= 0.1 * result.target_medians).all()
    with pytest.raises(FrozenInstanceError):
        result.names = ()


@pytest.mark.parametrize("noise", ["white", "env", "dem"])
def test_null_candidate_counts_match_independent_single_region_simulations(noise):
    from headd_l0.calibrate import _draws, _null_training_counts
    from headd_l0.simulate import SimConfig, simulate

    seeds = _seeds()[0]
    draws = _draws(seeds)
    low = _null_training_counts(0, noise, draws)
    high = _null_training_counts(0.001, noise, draws)
    np.testing.assert_array_equal(low, _null_training_counts(0, noise, draws))
    assert low.shape == high.shape == (128, 60)
    assert not np.array_equal(low, high)
    for i in (0, 127):
        expected = simulate(
            SimConfig(noise=noise, label="N", endemic_hazard=0.001),
            np.zeros((1, 1)),
            np.random.default_rng(seeds[i]),
        )
        np.testing.assert_array_equal(high[i], expected.counts[0, :60])


def test_zero_target_can_finish_at_the_fixed_lower_endpoint():
    from headd_l0.calibrate import calibrate

    result = calibrate(np.zeros((13, 60)), LEAVES, _seeds(), noise="env")
    np.testing.assert_array_equal(result.hazards, 0)
    np.testing.assert_array_equal(result.iterations, 0)
    assert (np.abs(result.errors) <= 1).all()


def test_unbracketed_target_fails_without_widening_the_hazard_interval():
    from headd_l0.calibrate import calibrate

    with pytest.raises(ValueError, match="ARAGUAIA.*bracket"):
        calibrate(np.full((13, 60), 10**12), LEAVES, _seeds())


@pytest.mark.parametrize("bad", ["names", "months", "counts", "replicates"])
def test_invalid_calibration_inputs_are_rejected(bad):
    from headd_l0.calibrate import calibrate

    counts, names, seeds = np.ones((13, 60)), LEAVES, _seeds()
    if bad == "names":
        names = (*LEAVES[:-1], LEAVES[0])
    elif bad == "months":
        counts = counts[:, :59]
    elif bad == "counts":
        counts[0, 0] = -1
    else:
        seeds = tuple(region[:127] for region in seeds)
    with pytest.raises(ValueError):
        calibrate(counts, names, seeds)


def test_cli_writes_calibration_and_complete_provenance(raw_dir, tmp_path):
    from headd_l0 import calibrate, data, simulate

    config = tmp_path / "endemic.toml"
    processed = tmp_path / "data/processed/endemic"
    results = tmp_path / "results"
    config.write_text(
        f'raw_dir = "{raw_dir}"\nprocessed_dir = "{processed}"\n'
        f'output_dir = "{results}"\nrun_id = "endemic-test"\n'
        'root_seed = 42\nnoise = "env"\nprofile_id = "P5-IMPL-2026-10-19-v1"\n'
    )
    originals = {
        name: sha256((raw_dir / name).read_bytes()).hexdigest()
        for name in data.RAW_FILES
    }
    assert calibrate.main([str(config)]) == 0
    artifact = np.load(processed / "endemic_calibration.npz")
    manifest = json.loads((processed / "manifest.json").read_text())
    assert manifest == json.loads((results / "endemic-test/manifest.json").read_text())
    assert tuple(artifact["names"]) == LEAVES
    bundle = data.load_sivep(raw_dir)
    np.testing.assert_array_equal(
        artifact["target_medians"], np.median(bundle.counts[:, :60], axis=1)
    )
    assert manifest["input_sha256"] == originals
    assert manifest["config_sha256"] == sha256(config.read_bytes()).hexdigest()
    for module in (calibrate, data, simulate):
        path = Path(module.__file__)
        assert (
            manifest["code_sha256"][path.name] == sha256(path.read_bytes()).hexdigest()
        )
    assert (
        manifest["git_sha"]
        == subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
        ).strip()
    )
    assert isinstance(manifest["git_dirty"], bool)
    assert manifest["timestamp_utc"]
    assert manifest["train_months"] == 60
    assert manifest["replicates_per_candidate"] == 128
    assert manifest["names"] == list(LEAVES)
    assert manifest["seeds"][0][0] == {"entropy": 42, "spawn_key": [2, 0, 0]}
    assert manifest["seeds"][-1][-1] == {"entropy": 42, "spawn_key": [2, 12, 127]}
    assert manifest["status"] == "ready"
    assert manifest["interpretation_allowed"] is False
    assert (
        manifest["artifact_sha256"]["endemic_calibration.npz"]
        == sha256((processed / "endemic_calibration.npz").read_bytes()).hexdigest()
    )
    assert originals == {
        name: sha256((raw_dir / name).read_bytes()).hexdigest()
        for name in data.RAW_FILES
    }
    with pytest.raises(FileExistsError):
        calibrate.main([str(config)])


def test_shipped_config_loads_as_a_frozen_approved_calibration():
    from headd_l0.calibrate import load_config

    cfg = load_config(ROOT / "configs/endemic_calibration.toml")
    assert cfg.processed_dir.is_relative_to("data/processed")
    with pytest.raises(FrozenInstanceError):
        cfg.noise = "dem"


def test_cli_preserves_failure_provenance_without_a_calibrated_artifact(tmp_path):
    from conftest import hr_rows, write_raw

    from headd_l0.calibrate import main

    raw = tmp_path / "raw"
    rows = hr_rows()
    rows["testperhr"] = 10**12
    write_raw(raw, rows)
    config = tmp_path / "failure.toml"
    processed = tmp_path / "processed"
    config.write_text(
        f'raw_dir = "{raw}"\nprocessed_dir = "{processed}"\n'
        f'output_dir = "{tmp_path / "results"}"\nrun_id = "failed"\n'
        "root_seed = 42\n"
    )
    assert main([str(config)]) == 2
    manifest = json.loads((processed / "manifest.json").read_text())
    assert manifest["status"] == "failed"
    assert "bracket" in manifest["error"]
    assert not (processed / "endemic_calibration.npz").exists()


@pytest.mark.parametrize(
    "change",
    [{"root_seed": True}, {"root_seed": -1}, {"noise": "pink"}, {"run_id": ".."}],
)
def test_invalid_cli_configuration_is_rejected(change):
    from headd_l0.calibrate import CalibrationConfig

    values = {
        "raw_dir": Path("data/raw"),
        "processed_dir": Path("data/processed/endemic"),
        "output_dir": Path("results"),
        "run_id": "endemic",
        "root_seed": 42,
    }
    with pytest.raises(ValueError):
        CalibrationConfig(**(values | change))
