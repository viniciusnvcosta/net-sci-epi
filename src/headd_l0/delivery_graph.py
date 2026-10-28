"""Build geographic review exports without altering candidate evidence."""

import json
import os
import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd

from headd_l0._sim_validation_io import _publish, _sha256
from headd_l0.data import hierarchy
from headd_l0.exploratory import load_graphs
from headd_l0.graph_io import PA_HEALTH_REGIONS_2013


def aggregate_population(
    source: pd.DataFrame, crosswalk: pd.DataFrame, ancestors: dict[str, str]
) -> dict[str, int]:
    """Aggregate source-year units once when descendants share a region."""
    if (
        source.municipality.duplicated().any()
        or crosswalk.municipality.duplicated().any()
    ):
        raise ValueError("duplicate municipality")
    if (source.population < 0).any() or (source.population % 1 != 0).any():
        raise ValueError("invalid population")
    current = set(crosswalk.municipality)
    if not set(ancestors).issubset(current):
        raise ValueError("unknown descendant")
    mapped = crosswalk.copy()
    mapped["ancestor"] = mapped.municipality.map(lambda x: ancestors.get(x, x))
    if (mapped.groupby("ancestor").region.nunique() != 1).any():
        raise ValueError("ancestor crosses region")
    mapping = mapped[["ancestor", "region"]].drop_duplicates()
    if set(mapping.ancestor) != set(source.municipality):
        raise ValueError("population coverage mismatch")
    joined = mapping.merge(
        source, left_on="ancestor", right_on="municipality", validate="one_to_one"
    )
    return {
        str(k): int(v) for k, v in joined.groupby("region").population.sum().items()
    }


def export_graph(
    a: np.ndarray,
    w: np.ndarray,
    regions: list[tuple[str, str]],
    population: dict[str, int] | None,
    output: Path,
) -> None:
    """Write the Queen graph with one weighted directed arc per matrix entry."""
    n = len(regions)
    if (
        a.shape != (n, n)
        or w.shape != (n, n)
        or not np.isin(a, [0, 1]).all()
        or not np.array_equal(a, a.T)
        or np.any(np.diag(a))
        or np.any(a.sum(axis=1) == 0)
        or not nx.is_connected(nx.from_numpy_array(a))
        or not np.array_equal(w, a / a.sum(axis=1)[:, None])
        or len({code for code, _ in regions}) != n
        or (population is not None and set(population) != {code for code, _ in regions})
        or (
            population is not None
            and any(
                type(value) is not int or value < 0 for value in population.values()
            )
        )
    ):
        raise ValueError("invalid graph or population binding")
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    graph = nx.DiGraph()
    for code, name in regions:
        attrs = {"code": code, "name": name}
        if population is not None:
            attrs["population"] = population[code]
        graph.add_node(code, **attrs)
    for i, (code, _) in enumerate(regions):
        for j, (other, _) in enumerate(regions):
            if a[i, j]:
                graph.add_edge(code, other, type="queen", weight=float(w[i, j]))
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{output.name}-", dir=output.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            nx.write_graphml(graph, handle)
        os.link(temporary, output)
    finally:
        Path(temporary).unlink()


def export_candidate_without_population(manifest_path: Path, output: Path) -> None:
    """Publish a candidate-bound graph explicitly marked population-pending."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    a, w, _, _ = load_graphs(manifest_path)
    codes = {name: str(code) for code, name in PA_HEALTH_REGIONS_2013.items()}
    regions = [(codes[name], name) for name in hierarchy().leaves]
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    export_graph(a, w, regions, None, stage / "candidate.graphml")
    np.save(stage / "adjacency.npy", a)
    np.save(stage / "W.npy", w)
    manifest = {
        "status": "partial_population_pending",
        "interpretation_allowed": False,
        "candidate_manifest_sha256": _sha256(manifest_path),
        "node_order": [name for _, name in regions],
        "population": "pending",
        "outputs": {p.name: _sha256(p) for p in stage.iterdir()},
    }
    (stage / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    _publish(stage, output)
