"""Verified graph inputs for a separately controlled exploratory SIR run."""

import json
from pathlib import Path

import numpy as np

from headd_l0._sim_validation_io import _sha256
from headd_l0.data import hierarchy
from headd_l0.detectors import rolling_zscore
from headd_l0.e1 import ArmSpec, ExperimentConfig, _score
from headd_l0.graph import _validate
from headd_l0.simulate import SimConfig, SimResult, simulate
from headd_l0.threshold import calibration_report, check_far

CANDIDATE_MANIFEST_SHA256 = (
    "7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0"
)


def load_graphs(
    manifest_path: Path,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Load candidate and all placebos after provenance and graph validation."""
    if _sha256(manifest_path) != CANDIDATE_MANIFEST_SHA256:
        raise ValueError("candidate manifest hash mismatch")
    metadata = json.loads(manifest_path.read_text())
    if tuple(metadata["region_names"]) != hierarchy().leaves:
        raise ValueError("region order mismatch")
    for name, digest in metadata["outputs"].items():
        if _sha256(manifest_path.parent / name) != digest:
            raise ValueError(f"output hash mismatch: {name}")
    for info in metadata["inputs"].values():
        path = Path(info["path"])
        if not path.is_absolute():
            path = manifest_path.parents[2] / path
        if _sha256(path) != info["sha256"]:
            raise ValueError(f"input hash mismatch: {path}")
    p4_info = metadata["inputs"]["p4_adjacency"]
    p4_path = Path(p4_info["path"])
    if _sha256(p4_path) != p4_info["sha256"]:
        raise ValueError("P4 hash mismatch")
    a = np.load(manifest_path.parent / "adjacency.npy", allow_pickle=False)
    w = np.load(manifest_path.parent / "W.npy", allow_pickle=False)
    placebos = np.load(manifest_path.parent / "placebos.npy", allow_pickle=False)
    p4 = np.load(p4_path, allow_pickle=False)
    _validate(a)
    _validate(p4)
    if a.shape != (13, 13) or not np.array_equal(w, a / a.sum(axis=1)[:, None]):
        raise ValueError("invalid candidate matrix")
    if placebos.shape != (30, 13, 13):
        raise ValueError("invalid placebo shape")
    seen = {a.tobytes()}
    for graph in placebos:
        _validate(graph)
        if (
            not np.array_equal(graph.sum(axis=1), a.sum(axis=1))
            or graph.tobytes() in seen
        ):
            raise ValueError("invalid placebo degrees or duplicate")
        seen.add(graph.tobytes())
    return a, w, p4, placebos


def score_replicate(
    counts: np.ndarray, graphs: dict[str, np.ndarray], seed: np.random.SeedSequence
) -> np.ndarray:
    """Score one shared panel with fixed arms and a causal z-score baseline."""
    config = ExperimentConfig(
        name="e1_smoke",
        run_id="exploratory",
        root_seed=20261028,
        output_dir=Path("results"),
        noise_types=("white",),
        epsilon_levels=(0, 0.2),
        n_transition=1,
        n_null=1,
        n_calibration=1,
        n_placebos=30,
        detectors=("pca", "lof", "knn", "hbos", "iforest", "mcd"),
        selection_k=5,
        graph_source="synthetic_cycle_smoke_only",
        endemic_source="fixed_profile_smoke_only",
    )
    arms = (
        ArmSpec("B1*", "reconciled", None),
        ArmSpec("B2", "reconciled", "observed"),
        ArmSpec("B2-P4", "reconciled", "p4"),
        *(
            ArmSpec(f"B2-placebo-{i:02d}", "reconciled", f"placebo-{i:02d}")
            for i in range(3)
        ),
    )
    result, _, audit = _score(counts, config, arms, graphs, seed)
    if not audit["fit_valid"] or not np.isfinite(result).all():
        raise ValueError("invalid NB2 or ensemble score")
    baseline = rolling_zscore(counts, window=12)[:, 60:]
    return np.concatenate([result, baseline[None, :, :]])


def simulate_replicate(
    weights: np.ndarray,
    epsilon: float,
    label: str,
    partition: str,
    index: int,
    endemic_hazard: tuple[float, ...],
) -> SimResult:
    """Simulate on the supplied candidate weights with stable partition seeds."""
    if partition not in ("pilot", "calibration", "evaluation") or label not in (
        "T",
        "N",
    ):
        raise ValueError("invalid partition or label")
    if epsilon not in (0.0, 0.2) or type(index) is not int or index < 0:
        raise ValueError("invalid cell address")
    address = (
        ("pilot", "calibration", "evaluation").index(partition),
        (0.0, 0.2).index(epsilon),
        ("T", "N").index(label),
        index,
    )
    sequence = np.random.SeedSequence(20261028, spawn_key=address)
    region_seed, simulation_seed = sequence.spawn(2)
    region = int(np.random.default_rng(region_seed).integers(13))
    config = SimConfig(
        noise="white",
        epsilon=epsilon,
        label=label,
        seed_region=region,
        endemic_hazard=endemic_hazard,
    )
    return simulate(config, weights, np.random.default_rng(simulation_seed))


ENDEMIC_MANIFEST_SHA256 = (
    "6cce8698b56d7b9ec4774e6ed0645bd6ab0ed78d08cbce51d2fc15605a9abbc0"
)
ENDEMIC_ARTIFACT_SHA256 = (
    "1f2a99787ce9e4cdd858fb6fe5a6c0931ed40d3d41d80a748380372aa0c47c3e"
)


def load_hazards(directory: Path) -> tuple[float, ...]:
    """Load the frozen P5 white calibration, rejecting altered or invalid data."""
    manifest = directory / "manifest.json"
    artifact = directory / "endemic_calibration.npz"
    if (
        _sha256(manifest) != ENDEMIC_MANIFEST_SHA256
        or _sha256(artifact) != ENDEMIC_ARTIFACT_SHA256
    ):
        raise ValueError("endemic calibration hash mismatch")
    metadata = json.loads(manifest.read_text())
    if (
        metadata["status"] != "ready"
        or metadata["config"]["noise"] != "white"
        or metadata["config"]["profile_id"] != "P5-IMPL-2026-10-19-v1"
        or metadata["artifact_sha256"][artifact.name] != ENDEMIC_ARTIFACT_SHA256
    ):
        raise ValueError("invalid endemic manifest")
    with np.load(artifact, allow_pickle=False) as saved:
        hazards = saved["hazards"]
        if (
            tuple(saved["names"]) != hierarchy().leaves
            or hazards.shape != (13,)
            or not np.isfinite(hazards).all()
            or (hazards < 0).any()
        ):
            raise ValueError("invalid endemic hazards")
        return tuple(float(value) for value in hazards)


def evaluate_far(
    calibration: np.ndarray,
    evaluation: np.ndarray,
    calibration_ids: range,
    evaluation_ids: range,
) -> list[dict]:
    """Calibrate and check each arm/region on complete disjoint null streams."""
    if calibration.shape != (200, 7, 13, 72) or evaluation.shape != (200, 7, 13, 72):
        raise ValueError("requires 200 null replicates per partition")
    if not np.isfinite(calibration).all() or not np.isfinite(evaluation).all():
        raise ValueError("scores must be finite")
    if len(set(calibration_ids)) != 200 or len(set(evaluation_ids)) != 200:
        raise ValueError("expected unique null addresses")
    if set(calibration_ids) & set(evaluation_ids):
        raise ValueError("null stream overlap")
    rows = []
    for arm in range(7):
        for region in range(13):
            fit = calibration_report(calibration[:, arm, region, :].ravel(), 1 / 60)
            check = check_far(
                evaluation[:, arm, region, :].ravel() > fit.threshold, 1 / 60, 1 / 300
            )
            rows.append(
                {
                    "arm": arm,
                    "region": region,
                    "threshold": fit.threshold,
                    "calibration_n": fit.n,
                    "n": check.n,
                    "alarms": check.alarms,
                    "observed_far": check.observed_far,
                    "passed": check.passed,
                }
            )
    return rows
