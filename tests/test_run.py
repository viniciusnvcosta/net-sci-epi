"""E0* must reject incomplete, invalid or non-improving evidence."""

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from headd_l0.data import hierarchy
from headd_l0.run import E0Config, check_e0_star, load_config, run_preflight


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

    frame = evidence()
    if defect == "missing":
        frame = frame.drop(index=2)
    elif defect == "duplicate":
        frame = pd.concat([frame, frame.iloc[2:3]])
    elif defect == "single_class":
        frame.loc[2, "n_negative"] = 0
    elif defect == "nan":
        frame.loc[2, "auc_pr"] = np.nan
    else:
        frame.loc[2, "task"] = "unknown"
    result = check_e0_star(True, frame, np.random.default_rng(8))
    assert not result.passed and result.reasons


def test_e0_bootstrap_excludes_pa_and_pairs_by_name():

    frame = evidence()
    frame.loc[(frame.task == "PA") & (frame.arm == "B1*"), "auc_pr"] = 0
    result = check_e0_star(
        True, frame.sample(frac=1, random_state=3), np.random.default_rng(8)
    )
    assert result.lower_bound == pytest.approx(0.1)


def test_e0_rejects_different_labels_between_arms():

    frame = evidence()
    frame.loc[2, ["n_positive", "n_negative"]] = [11, 61]
    assert not check_e0_star(True, frame, np.random.default_rng(8)).passed


def test_e0_recorded_inconclusive(tmp_path):

    fixture = np.load(Path(__file__).parent / "reference/data.npz")
    cfg = E0Config(
        run_id="audit", root_seed=42, raw_dir=tmp_path / "raw", output_dir=tmp_path
    )
    result = run_preflight(cfg, fixture["counts"].T)
    manifest = json.loads((result / "manifest.json").read_text())
    assert manifest["gates"]["E0"]["status"] == "inconclusive"
    assert manifest["gates"]["E0_star"]["status"] == "pending"
    assert manifest["gates"]["E0_star"]["reasons"] == []
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

    config = tmp_path / "bad.toml"
    config.write_text(
        'run_id = "audit"\nroot_seed = 42\nraw_dir = "raw"\noutput_dir = "results"\nbaseline_id = "B1"\n'
    )
    with pytest.raises(ValueError):
        load_config(config)


@pytest.mark.parametrize(
    "field,value",
    [
        ("baseline_id", "B1"),
        ("reference_sha", "wrong"),
        ("run_id", "../escape"),
        ("run_id", "/absolute"),
        ("run_id", ""),
        ("run_id", 4),
        ("root_seed", -1),
        ("root_seed", True),
        ("root_seed", 1.5),
        ("root_seed", "42"),
        ("raw_dir", ""),
        ("raw_dir", 3),
        ("output_dir", ""),
        ("output_dir", None),
    ],
)
def test_config_direct_constructor_validates(field, value, tmp_path):
    kwargs = {
        "run_id": "audit",
        "root_seed": 42,
        "raw_dir": tmp_path / "raw",
        "output_dir": tmp_path,
    }
    kwargs[field] = value
    with pytest.raises(ValueError):
        E0Config(**kwargs)


@pytest.mark.parametrize("missing", ["run_id", "root_seed", "raw_dir", "output_dir"])
def test_config_requires_explicit_execution_fields(missing, tmp_path):
    values = {
        "run_id": "audit",
        "root_seed": 42,
        "raw_dir": "raw",
        "output_dir": "results",
    }
    del values[missing]
    config = tmp_path / "config.toml"
    config.write_text(
        "\n".join(f"{key} = {json.dumps(value)}" for key, value in values.items())
    )
    with pytest.raises(ValueError, match="configuration"):
        load_config(config)


def test_config_normalizes_paths_without_changing_seed(tmp_path):
    config = tmp_path / "config.toml"
    config.write_text(
        'run_id = "audit"\nroot_seed = 0\nraw_dir = "~/raw"\noutput_dir = "results"\n'
    )
    cfg = load_config(config)
    assert cfg.raw_dir == Path.home() / "raw"
    assert cfg.output_dir == Path("results")
    assert cfg.root_seed == 0


def test_manifest_git_identity_does_not_depend_on_working_directory(
    tmp_path, monkeypatch
):
    root = Path(__file__).resolve().parents[1]
    expected = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    fixture = np.load(root / "tests/reference/data.npz")
    monkeypatch.chdir(tmp_path)
    cfg = E0Config(
        run_id="foreign-cwd",
        root_seed=42,
        raw_dir=tmp_path / "raw",
        output_dir=tmp_path,
    )
    result = run_preflight(cfg, fixture["counts"].T)
    assert json.loads((result / "manifest.json").read_text())["git_sha"] == expected


def test_regional_gate_allows_single_class_pa_with_undefined_ap():
    frame = evidence()
    frame.loc[frame.task == "PA", ["auc_pr", "n_positive", "n_negative"]] = [
        np.nan,
        72,
        0,
    ]
    result = check_e0_star(True, frame, np.random.default_rng(8))
    assert result.passed
    assert result.conditions["thirteen_regional_tasks"]
    assert result.lower_bound == pytest.approx(0.1)


def test_regional_gate_allows_omitting_pa():
    frame = evidence().query("task != 'PA'")
    assert check_e0_star(True, frame, np.random.default_rng(8)).passed


@pytest.mark.parametrize("defect", ["duplicate", "unknown"])
def test_regional_gate_rejects_structurally_invalid_pa_rows(defect):
    frame = evidence()
    if defect == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    else:
        frame.loc[0, "task"] = "unknown"
    assert not check_e0_star(True, frame, np.random.default_rng(8)).passed


@pytest.mark.parametrize(
    "column,value",
    [
        ("n_positive", 10.5),
        ("n_positive", 0),
        ("n_negative", 61),
        ("auc_pr", 1.1),
        ("arm", "wrong"),
    ],
)
def test_regional_gate_rejects_malformed_regional_evidence(column, value):
    frame = evidence()
    if column == "n_positive" and isinstance(value, float):
        frame[column] = frame[column].astype(float)
    frame.loc[2, column] = value
    result = check_e0_star(True, frame, np.random.default_rng(8))
    assert not result.passed
    assert not result.conditions["thirteen_regional_tasks"]


def test_preflight_reports_window_prevalence_pa_and_unchanged_injection(tmp_path):
    from headd_l0.inject import InjectionConfig, inject_original_bounded

    fixture = np.load(Path(__file__).parent / "reference/data.npz")
    leaves = fixture["counts"].T
    cfg = E0Config("audit", 42, tmp_path / "raw", tmp_path)
    path = run_preflight(cfg, leaves)
    manifest = json.loads((path / "manifest.json").read_text())
    saved = np.load(path / "injection.npz")
    direct = inject_original_bounded(
        leaves, np.random.default_rng(42), InjectionConfig()
    )
    np.testing.assert_array_equal(saved["counts"], direct.counts)
    np.testing.assert_array_equal(saved["mask"], direct.mask)
    np.testing.assert_array_equal(saved["onset"], direct.onset)
    tasks = pd.read_parquet(path / "tasks.parquet")
    assert tasks.task.tolist() == ["PA", *hierarchy().leaves]
    assert tasks.n_positive.tolist() == [
        72,
        29,
        29,
        26,
        18,
        22,
        22,
        20,
        15,
        21,
        17,
        20,
        21,
        14,
    ]
    assert tasks.n_negative.tolist() == [
        0,
        43,
        43,
        46,
        54,
        50,
        50,
        52,
        57,
        51,
        55,
        52,
        51,
        58,
    ]
    assert (tasks.denominator == 72).all()
    assert (tasks.window_start == 60).all()
    assert (tasks.window_end == 131).all()
    np.testing.assert_allclose(tasks.positive_prevalence, tasks.n_positive / 72)
    assert tasks.role.tolist() == ["descriptive", *(["regional"] * 13)]
    assert tasks.in_gate.tolist() == [False, *([True] * 13)]
    pa = json.loads((path / "pa_diagnostics.json").read_text())
    assert pa == {
        "positive_prevalence": 1.0,
        "union_coverage_months": 72,
        "denominator": 72,
        "counts_coherent": True,
        "labels_union_coherent": True,
    }
    assert manifest["e0_star_revision"] == "D-E0*-R1"
    assert (
        manifest["e0_star_decision_commit"]
        == "50f8b3f29bacc4747329addf80cee6719fe3c7fc"
    )
    assert manifest["gates"]["E0_star"]["components"] == "not_evaluated"
    assert manifest["gates"]["E0_star"]["trivial_baseline"] == "not_evaluated"
    assert manifest["negative_injected_cells"] == 110
    assert manifest["adjusted_onsets"] == 2
