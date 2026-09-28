"""E0* must reject incomplete, invalid or non-improving evidence."""

import numpy as np
import pandas as pd
import pytest

from headd_l0.data import hierarchy


def evidence(delta=0.1):
    return pd.DataFrame(
        [
            {
                "task": name,
                "arm": arm,
                "auc_pr": 0.4 + (delta if arm == "B1*" else 0),
                "n_positive": 10,
                "n_negative": 62,
            }
            for name in ("PA", *hierarchy().leaves)
            for arm in ("B1*", "zscore")
        ]
    )


def test_e0_star_requires_all_conditions():
    from headd_l0.run import check_e0_star

    rng = np.random.default_rng(8)
    result = check_e0_star(True, evidence(), rng)
    assert result.passed and result.lower_bound == pytest.approx(0.1)
    assert result.conditions["trivial_baseline"]
    assert not check_e0_star(False, evidence(), rng).passed
    assert not check_e0_star(True, evidence(-0.1), rng).passed
    assert not check_e0_star(True, evidence(0), rng).passed


@pytest.mark.parametrize(
    "defect", ["missing", "duplicate", "single_class", "nan", "unknown"]
)
def test_e0_rejects_invalid_task_evidence(defect):
    from headd_l0.run import check_e0_star

    frame = evidence()
    if defect == "missing":
        frame = frame.iloc[1:]
    elif defect == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif defect == "single_class":
        frame.loc[0, "n_negative"] = 0
    elif defect == "nan":
        frame.loc[0, "auc_pr"] = np.nan
    else:
        frame.loc[0, "task"] = "unknown"
    result = check_e0_star(True, frame, np.random.default_rng(8))
    assert not result.passed and result.reasons


def test_e0_bootstrap_excludes_pa_and_pairs_by_name():
    from headd_l0.run import check_e0_star

    frame = evidence()
    frame.loc[(frame.task == "PA") & (frame.arm == "B1*"), "auc_pr"] = 0
    result = check_e0_star(
        True, frame.sample(frac=1, random_state=3), np.random.default_rng(8)
    )
    assert result.lower_bound == pytest.approx(0.1)


def test_e0_rejects_different_labels_between_arms():
    from headd_l0.run import check_e0_star

    frame = evidence()
    frame.loc[0, ["n_positive", "n_negative"]] = [11, 61]
    assert not check_e0_star(True, frame, np.random.default_rng(8)).passed


def test_e0_recorded_inconclusive(tmp_path):
    import json
    from pathlib import Path

    from headd_l0.run import E0Config, run_preflight

    fixture = np.load(Path(__file__).parent / "reference/data.npz")
    cfg = E0Config(run_id="audit", output_dir=tmp_path)
    result = run_preflight(cfg, fixture["counts"].T)
    manifest = json.loads((result / "manifest.json").read_text())
    assert manifest["gates"]["E0"]["status"] == "inconclusive"
    assert manifest["gates"]["E0_star"]["status"] == "failed"
    assert "single_class:PA" in manifest["gates"]["E0_star"]["reasons"]
    assert manifest["interpretation_allowed"] is False
    assert manifest["baseline_id"] == "B1*"
    assert manifest["reference_sha"].startswith("fbfa609")
    assert manifest["negative_injected_cells"] > 0
    saved = np.load(result / "injection.npz")
    np.testing.assert_allclose(saved["counts"][0], saved["counts"][1:].sum(axis=0))
    tasks = pd.read_parquet(result / "tasks.parquet")
    assert len(tasks) == 14
    assert tasks.loc[tasks.task == "PA", "n_negative"].item() == 0
    with pytest.raises(FileExistsError):
        run_preflight(cfg, fixture["counts"].T)


def test_e0_config_rejects_wrong_baseline(tmp_path):
    from headd_l0.run import load_config

    config = tmp_path / "bad.toml"
    config.write_text('baseline_id = "B1"\n')
    with pytest.raises(ValueError):
        load_config(config)
