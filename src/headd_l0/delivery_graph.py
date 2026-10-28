"""Build geographic review exports without altering candidate evidence."""

import os
import tempfile
from pathlib import Path

import networkx as nx
import numpy as np
import pandas as pd


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
    population: dict[str, int],
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
        or set(population) != {code for code, _ in regions}
        or any(type(value) is not int or value < 0 for value in population.values())
    ):
        raise ValueError("invalid graph or population binding")
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    graph = nx.DiGraph()
    for code, name in regions:
        graph.add_node(code, code=code, name=name, population=population[code])
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
