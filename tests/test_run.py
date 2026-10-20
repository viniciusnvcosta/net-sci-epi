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


@pytest.mark.parametrize("column", ["auc_pr", "n_positive", "n_negative"])
def test_regional_gate_rejects_numeric_looking_strings_without_mutation(column):
    frame = evidence()
    frame[column] = frame[column].astype(object)
    region = frame.task == "ARAGUAIA"
    frame.loc[region, column] = frame.loc[region, column].map(str)
    original = frame.copy(deep=True)

    result = check_e0_star(True, frame, np.random.default_rng(8))

    assert not result.passed
    assert not result.conditions["thirteen_regional_tasks"]
    assert result.lower_bound is None
    pd.testing.assert_frame_equal(frame, original)


def test_regional_gate_ignores_pa_string_ap_type():
    frame = evidence()
    frame["auc_pr"] = frame["auc_pr"].astype(object)
    frame.loc[frame.task == "PA", "auc_pr"] = "undefined"
    result = check_e0_star(True, frame, np.random.default_rng(8))
    assert result.passed


@pytest.mark.parametrize("score", [False, True])
def test_cli_preparation_and_scoring_paths(tmp_path, monkeypatch, score):
    from types import SimpleNamespace

    from headd_l0 import run

    leaves = np.load(Path(__file__).parent / "reference/data.npz")["counts"].T.copy()
    leaves[0] = 0
    monkeypatch.setattr(run, "load_sivep", lambda path: SimpleNamespace(counts=leaves))
    config = tmp_path / "cli.toml"
    config.write_text(
        f'run_id="cli"\nroot_seed=42\nraw_dir="raw"\noutput_dir="{tmp_path}"\n'
    )
    monkeypatch.setattr(
        "sys.argv", ["headd_l0.run", *(["--score-e0"] if score else []), str(config)]
    )
    assert run.main() == 2
    manifest = json.loads((tmp_path / "cli/manifest.json").read_text())
    assert not manifest["interpretation_allowed"]
    assert (tmp_path / "cli/fits.parquet").exists() is score
    if score:
        assert manifest["failure_reason"] == "D5_forecast_unavailable"
    else:
        assert "status" not in manifest


def _smoke_config(tmp_path, run_id):
    from dataclasses import replace

    from headd_l0 import run

    assert hasattr(run, "ExperimentConfig"), "missing E1 runner configuration"
    cfg = run.load_config(Path("configs/e1_smoke.toml"))
    return replace(cfg, output_dir=tmp_path, run_id=run_id)


@pytest.fixture(scope="module")
def e1_runs(tmp_path_factory):
    import sys
    from collections import Counter
    from dataclasses import replace

    from headd_l0 import run
    from headd_l0.forecast import fit_nb2
    from headd_l0.reconcile import fit_mint
    from headd_l0.simulate import simulate

    cfg = _smoke_config(tmp_path_factory.mktemp("e1"), "first")
    tracked = {fn.__code__: fn.__name__ for fn in (simulate, fit_nb2, fit_mint)}
    calls = Counter()

    def count_real_calls(frame, event, _arg):
        if event == "call" and frame.f_code in tracked:
            calls[tracked[frame.f_code]] += 1

    previous = sys.getprofile()
    state = np.random.get_state()
    sys.setprofile(count_real_calls)
    try:
        first = run.run(cfg)
    finally:
        sys.setprofile(previous)
    records = pd.read_parquet(first.path / "replicates.parquet")
    assert calls == {
        "simulate": 12,
        "fit_nb2": 12,
        "fit_mint": int(records.fit_valid.sum()),
    }
    for before, after in zip(state, np.random.get_state(), strict=True):
        np.testing.assert_equal(before, after)
    second = run.run(
        replace(cfg, run_id="second"),
        arms=tuple(reversed(run.build_arms(cfg.n_placebos))),
    )
    return cfg, first, second


def test_e1_configs_load_without_running_the_bench(tmp_path):
    from headd_l0 import run

    cfg = _smoke_config(tmp_path, "smoke")
    assert (cfg.noise_types, cfg.epsilon_levels) == (("white",), (0.0, 0.2))
    assert (cfg.n_transition, cfg.n_null, cfg.n_calibration, cfg.n_placebos) == (
        2,
        2,
        2,
        30,
    )
    bench = run.load_config(Path("configs/e1_bench.toml"))
    assert (bench.noise_types, bench.epsilon_levels) == (
        ("white", "env", "dem"),
        (0, 0.05, 0.2),
    )
    assert (
        bench.n_transition,
        bench.n_null,
        bench.n_calibration,
        bench.n_placebos,
    ) == (500, 500, 200, 30)
    assert set(bench.detectors) == {"pca", "lof", "knn", "hbos", "iforest", "mcd"}
    assert bench.selection_k == 5
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize(
    "field,value",
    [
        ("detectors", ("missing",)),
        ("selector", "missing"),
        ("threshold", "missing"),
        ("reconciliation", "missing"),
        ("root_seed", True),
        ("run_id", "../escape"),
        ("noise_types", ("wrong",)),
        ("n_null", 0),
        ("target_far", 0.1),
    ],
)
def test_e1_configuration_rejects_invalid_execution(field, value, tmp_path):
    from dataclasses import replace

    cfg = _smoke_config(tmp_path, "invalid")
    with pytest.raises(ValueError):
        replace(cfg, **{field: value})


def test_e1_has_exact_matrix_and_shared_replicates(e1_runs):
    _, first, _ = e1_runs
    records = pd.read_parquet(first.path / "replicates.parquet")
    scores = pd.read_parquet(first.path / "scores.parquet")
    metrics = pd.read_parquet(first.path / "metrics.parquet")
    arms = {"B0", "B1*", "B2", *(f"B2-placebo-{i:02d}" for i in range(30))}
    assert set(scores.arm) == arms
    assert len(records) == 12  # Eight evaluation + four calibration; twins aren't N.
    assert records.replicate_id.is_unique
    assert records.groupby(["epsilon", "partition", "label"]).size().tolist() == [2] * 6
    assert set(records.noise) == {"white"}
    assert len(metrics) == 8 * 33 * 13
    assert len(scores) == 12 * 33 * 13 * 72
    assert (scores.groupby(["replicate_id", "task"]).arm.nunique() == 33).all()
    assert metrics.groupby(["replicate_id", "task"]).onset.nunique().eq(1).all()
    assert (
        metrics.groupby(["replicate_id", "task"])
        .timing_denominator.nunique()
        .eq(1)
        .all()
    )
    assert scores.score.notna().any(), "smoke must execute the real scoring pipeline"
    assert metrics.loc[metrics.onset == -1, "restricted_lead"].isna().all()
    missed = metrics.query("onset >= 0 and not detected and alarm_available")
    assert missed.censored.all()
    assert missed.restricted_lead.notna().all()


def test_e1_saved_data_replays_from_disjoint_named_streams(e1_runs):
    from headd_l0.graph import row_normalize
    from headd_l0.simulate import SimConfig, simulate

    _, first, _ = e1_runs
    manifest = json.loads((first.path / "manifest.json").read_text())
    records = pd.read_parquet(first.path / "replicates.parquet")
    shared = np.load(first.path / "shared.npz")
    graph = np.load(first.path / "graphs.npz")["observed"]
    keys = [tuple(x) for x in records.spawn_key]
    assert len(set(keys)) == 12
    assert {
        key[0] for key in records.query("partition == 'calibration'").spawn_key
    } == {1}
    assert {key[0] for key in records.query("partition == 'evaluation'").spawn_key} == {
        2
    }
    for i, row in records.iterrows():
        seed = np.random.SeedSequence(int(row.entropy), spawn_key=tuple(row.spawn_key))
        result = simulate(
            SimConfig(
                noise=row.noise,
                label=row.label,
                epsilon=row.epsilon,
                seed_region=int(row.seed_region),
            ),
            row_normalize(graph),
            np.random.default_rng(seed),
        )
        np.testing.assert_array_equal(shared["counts"][i], result.counts)
        np.testing.assert_array_equal(shared["twin_counts"][i], result.twin_counts)
        np.testing.assert_array_equal(shared["onset"][i], result.onset)
    assert manifest["work"]["simulation_calls"] == 12
    assert manifest["work"]["forecast_fits"] == 12
    assert manifest["work"]["mint_fits"] == int(records.fit_valid.sum())
    assert manifest["work"]["pool_fits"] < int(records.fit_valid.sum()) * 33 * 13
    coherent = shared["coherent_forecasts"][records.fit_valid]
    np.testing.assert_allclose(coherent[:, 0], coherent[:, 1:].sum(axis=1), atol=1e-9)


def test_e1_manifest_and_artifacts_are_deterministic_under_arm_reordering(e1_runs):
    from hashlib import sha256

    _, first, second = e1_runs
    manifests = [
        json.loads((r.path / "manifest.json").read_text()) for r in (first, second)
    ]
    required = {
        "config",
        "config_sha256",
        "git_sha",
        "git_dirty",
        "versions",
        "seeds",
        "simulation_profile",
        "graph_hashes",
        "partitions",
        "gates",
        "effective_sizes",
        "artifact_sha256",
        "nondeterministic_fields",
    }
    assert required <= manifests[0].keys()
    for result, manifest in zip((first, second), manifests, strict=True):
        for name, digest in manifest["artifact_sha256"].items():
            assert sha256((result.path / name).read_bytes()).hexdigest() == digest
        assert manifest["interpretation_allowed"] is False
        assert manifest["gates"]["G4"]["status"] == "pending"
        assert manifest["gates"]["E0_star"]["status"] == "failed"
        assert len(set(manifest["graph_hashes"].values())) == 31
        assert manifest["settings"]["detectors"] == ["pca", "knn", "hbos"]
        assert manifest["settings"]["selection"]["k"] == 2
        assert manifest["graph_source"] == "synthetic_cycle_smoke_only"
        assert manifest["endemic_source"] == "fixed_profile_smoke_only"
        for key in manifest["nondeterministic_fields"]:
            target = manifest
            parts = key.split(".")
            for part in parts[:-1]:
                target = target[part]
            del target[parts[-1]]
    assert manifests[0] == manifests[1]
    pd.testing.assert_frame_equal(first.metrics, second.metrics)


def test_e1_thresholds_use_only_calibration_and_far_blocks_comparisons(e1_runs):
    from headd_l0.threshold import calibration_report

    _, first, _ = e1_runs
    scores = pd.read_parquet(first.path / "scores.parquet")
    far = pd.read_parquet(first.path / "far.parquet")
    metrics = pd.read_parquet(first.path / "metrics.parquet")
    comparisons = pd.read_parquet(first.path / "comparisons.parquet")
    assert len(far) == 2 * 33 * 13
    assert not far.passed.all()
    assert len(comparisons) == 4 * 32 * 13
    for row in far.itertuples():
        selected = scores.loc[
            (scores.epsilon == row.epsilon)
            & (scores.arm == row.arm)
            & (scores.task == row.task)
        ]
        calibration = (
            selected.query("partition == 'calibration'").score.dropna().to_numpy()
        )
        evaluation = (
            selected.query("partition == 'evaluation' and label == 'N'")
            .score.dropna()
            .to_numpy()
        )
        if len(calibration) and len(evaluation):
            expected = calibration_report(calibration, 1 / 60)
            assert row.threshold == expected.threshold
            assert row.calibration_n == len(calibration)
            assert row.n == len(evaluation)
            assert row.observed_far == np.mean(evaluation > row.threshold)
    failed = far.loc[~far.passed]
    for row in failed.itertuples():
        affected = comparisons.loc[
            (comparisons.epsilon == row.epsilon)
            & (comparisons.task == row.task)
            & ((comparisons.arm == row.arm) | (comparisons.reference == row.arm))
        ]
        assert not affected.far_comparable.any()
        assert affected.blocked_reason.str.contains("FAR").all()
    assert not comparisons.interpretation_allowed.any()
    assert not metrics.interpretation_allowed.any()
    assert set(metrics.arm) == set(far.arm)


def test_e1_run_is_immutable(e1_runs):
    from headd_l0 import run

    cfg, first, _ = e1_runs
    before = (first.path / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        run.run(cfg)
    assert (first.path / "manifest.json").read_bytes() == before
