"""Verified graph inputs for a separately controlled exploratory SIR run."""

import json
from pathlib import Path

import numpy as np

from headd_l0._sim_validation_io import _sha256
from headd_l0.data import hierarchy
from headd_l0.detectors import rolling_zscore
from headd_l0.e1 import ArmSpec, ExperimentConfig, _score
from headd_l0.graph import _validate

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
