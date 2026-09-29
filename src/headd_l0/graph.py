"""Queen adjacency and connected labeled-degree placebo graphs (not uniform draws)."""

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from libpysal.weights import Queen

from headd_l0.data import hierarchy

CACHE_DIR = Path("data/processed/graph")
SWAP_BUDGET = {"accepted_per_edge": 10, "attempts_per_edge": 1000, "candidates": 10000}


def _validate(A: np.ndarray) -> nx.Graph:
    if (
        A.ndim != 2
        or A.shape[0] != A.shape[1]
        or len(A) < 2
        or not np.isin(A, [0, 1]).all()
        or not np.array_equal(A, A.T)
        or np.diag(A).any()
    ):
        raise ValueError("adjacency must be square, binary, symmetric and loop-free")
    network = nx.from_numpy_array(A)
    if not nx.is_connected(network):
        raise ValueError(
            f"disconnected adjacency: {list(nx.connected_components(network))}"
        )
    return network


def build_adjacency(regions: gpd.GeoDataFrame, names: tuple[str, ...]) -> np.ndarray:
    """Build connected Queen adjacency, ordering the ``name`` column by names.

    Empty, invalid or nonpolygon geometries are rejected without repair.
    """
    if (
        "name" not in regions
        or len(regions) != len(names)
        or regions.name.duplicated().any()
        or len(set(names)) != len(names)
        or set(regions.name) != set(names)
    ):
        raise ValueError("regions must match the unique canonical names exactly")
    ordered = regions.set_index("name").loc[list(names)]
    if (
        ordered.geometry.isna().any()
        or ordered.geometry.is_empty.any()
        or not ordered.geometry.is_valid.all()
        or not ordered.geom_type.isin(["Polygon", "MultiPolygon"]).all()
    ):
        raise ValueError("empty, invalid or nonpolygon geometries")
    A = Queen.from_dataframe(ordered, use_index=True, silence_warnings=True).full()[0]
    A = A.astype(np.uint8)
    _validate(A)
    return A


def row_normalize(A: np.ndarray) -> np.ndarray:
    """Return W with rows summing to one; reject islands or invalid adjacency."""
    _validate(A)
    return A / A.sum(axis=1, keepdims=True)


def _draw_placebos(
    A: np.ndarray, n: int, rng: np.random.Generator
) -> tuple[list[np.ndarray], dict]:
    _validate(A)
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    original = np.asarray(A, dtype=np.uint8)
    edges = np.column_stack(np.where(np.triu(original, 1)))
    m = len(edges)
    if m < 2:
        raise RuntimeError("placebo swap budget cannot produce a distinct graph")
    draws, attempts = [], []
    seen = {original.tobytes()}
    for candidate in range(SWAP_BUDGET["candidates"]):
        B, pairs = original.copy(), edges.copy()
        accepted = 0
        for attempt in range(1, SWAP_BUDGET["attempts_per_edge"] * m + 1):
            i, j = rng.choice(m, 2, replace=False)
            a, b = pairs[i]
            c, d = pairs[j]
            if rng.integers(2):
                c, d = d, c
            if len({a, b, c, d}) < 4 or B[a, c] or B[b, d]:
                continue
            B[a, b] = B[b, a] = B[c, d] = B[d, c] = 0
            B[a, c] = B[c, a] = B[b, d] = B[d, b] = 1
            if not nx.is_connected(nx.from_numpy_array(B)):
                B[a, c] = B[c, a] = B[b, d] = B[d, b] = 0
                B[a, b] = B[b, a] = B[c, d] = B[d, c] = 1
                continue
            pairs[i], pairs[j] = (a, c), (b, d)
            accepted += 1
            if accepted == SWAP_BUDGET["accepted_per_edge"] * m:
                break
        else:
            raise RuntimeError(
                f"placebo swap budget exhausted: {accepted}/{10 * m} accepted"
            )
        attempts.append(attempt)
        key = B.tobytes()
        if key not in seen:
            seen.add(key)
            draws.append(B)
            if len(draws) == n:
                distances = [int(np.count_nonzero(B != original) // 2) for B in draws]
                pairwise = [
                    int(np.count_nonzero(B != C) // 2)
                    for i, B in enumerate(draws)
                    for C in draws[i + 1 :]
                ]
                return draws, {
                    "budget": SWAP_BUDGET,
                    "candidates": candidate + 1,
                    "attempts": attempts,
                    "edge_distance": distances,
                    "pairwise_edge_distance": pairwise,
                    "sha256": [hashlib.sha256(B.tobytes()).hexdigest() for B in draws],
                    "uniform_sampling_claimed": False,
                }
    raise RuntimeError(f"placebo candidate budget exhausted: found {len(draws)}/{n}")


def placebos(A: np.ndarray, n: int, rng: np.random.Generator) -> list[np.ndarray]:
    """Draw n distinct connected nonoriginal graphs preserving each node degree.

    Each candidate starts at A and requires 10|E| accepted swaps, with at most
    1000|E| attempts. At most 10000 candidates; exhaustion raises RuntimeError.
    """
    return _draw_placebos(A, n, rng)[0]


def centralities(A: np.ndarray, names: tuple[str, ...]) -> pd.DataFrame:
    """Return named degree, betweenness and L2-normalized eigenvector centrality."""
    network = _validate(A)
    if len(names) != len(A) or len(set(names)) != len(names):
        raise ValueError("names must uniquely label adjacency")
    return pd.DataFrame(
        {
            "name": names,
            "degree": A.sum(axis=1),
            "betweenness": list(nx.betweenness_centrality(network).values()),
            "eigenvector": list(
                nx.eigenvector_centrality(network, max_iter=1000, tol=1e-12).values()
            ),
        }
    )


def export_graph(A: np.ndarray, names: tuple[str, ...], path: Path) -> None:
    """Write an undirected GEXF whose node IDs and labels are canonical names."""
    network = _validate(A)
    if len(names) != len(A) or len(set(names)) != len(names):
        raise ValueError("names must uniquely label adjacency")
    nx.write_gexf(nx.relabel_nodes(network, dict(enumerate(names))), path)


def _sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def adjacency() -> tuple[np.ndarray, tuple[str, ...]]:
    """Read the canonical processed cache, checking provenance, hash and topology."""
    manifest = json.loads((CACHE_DIR / "manifest.json").read_text())
    names = tuple(manifest.get("names", ()))
    if manifest["status"] != "ready":
        raise ValueError("graph cache is not ready")
    if (
        names != hierarchy().leaves
        or manifest["source"]["year"] != 2013
        or manifest["source"]["simplified"] is not False
        or manifest["source"]["geometry_level"] != "micro"
        or manifest["source"]["code_state"] != "PA"
        or manifest["contiguity"] != "queen"
    ):
        raise ValueError("incompatible graph cache names or source")
    if (
        _sha(CACHE_DIR / "adjacency.npy")
        != manifest["artifact_sha256"]["adjacency.npy"]
    ):
        raise ValueError("adjacency cache hash mismatch")
    A = np.load(CACHE_DIR / "adjacency.npy", allow_pickle=False)
    _validate(A)
    if A.shape != (len(names), len(names)):
        raise ValueError("incompatible graph cache shape")
    return A, names


if __name__ == "__main__":
    from headd_l0.graph_io import main

    raise SystemExit(main())
