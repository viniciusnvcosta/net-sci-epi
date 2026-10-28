"""Verified graph inputs for a separately controlled exploratory SIR run."""

import json
from pathlib import Path

import numpy as np

from headd_l0._sim_validation_io import _sha256
from headd_l0.data import hierarchy
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
