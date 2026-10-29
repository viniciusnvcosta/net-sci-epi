"""Build geographic review exports without altering candidate evidence."""

import csv
import json
import os
import subprocess
import tempfile
from datetime import UTC, datetime
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
    candidate_hash = _sha256(manifest_path)
    source_files = sorted(Path(__file__).parent.glob("*.py"))
    source_hashes = {p.name: _sha256(p) for p in source_files}
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
        "candidate_manifest_sha256": candidate_hash,
        "source_sha256": source_hashes,
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "node_order": [name for _, name in regions],
        "population": "pending",
        "outputs": {p.name: _sha256(p) for p in stage.iterdir()},
    }
    (stage / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    if (
        _sha256(manifest_path) != candidate_hash
        or {p.name: _sha256(p) for p in source_files} != source_hashes
    ):
        raise ValueError("source changed during export")
    _publish(stage, output)


def read_sidra_2010(path: Path) -> pd.DataFrame:
    """Read SIDRA 1378 total-population rows and validate the state total."""
    with path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))
    if (
        len(rows) < 7
        or "Tabela 1378" not in rows[0][0]
        or "População residente" not in rows[1][0]
    ):
        raise ValueError("invalid SIDRA table")
    if [rows[i][5] for i in (3, 4, 5)] != ["2010", "Total", "Total"]:
        raise ValueError("2010, situação Total e sexo Total required")
    expected_notes = {
        "1 - Dados do Universo.",
        "2 - A categoria Pessoa responsável inclui as pessoas Sem declaração de compartilhamento de responsabilidade pelo domicílio.",
    }
    if not expected_notes.issubset({r[0] for r in rows if len(r) == 1}):
        raise ValueError("missing SIDRA notes")
    state = [r for r in rows if r and r[0] == "UF" and len(r) >= 7 and r[1] == "15"]
    municipal = [r for r in rows if r and r[0] == "MU"]
    if len(state) != 1 or len(municipal) != 143:
        raise ValueError("invalid state or municipal coverage")
    data = []
    for row in municipal:
        if (
            len(row) != 7
            or len(row[1]) != 7
            or not row[1].isdigit()
            or not row[1].startswith("15")
            or row[3:5] != ["Total", "Total"]
            or row[6] != "Pessoas"
            or not row[5].isdigit()
        ):
            raise ValueError("invalid municipal SIDRA row")
        data.append({"municipality": row[1][:6], "population": int(row[5])})
    result = pd.DataFrame(data)
    if result.municipality.duplicated().any() or not state[0][5].isdigit():
        raise ValueError("duplicate municipality or invalid state total")
    if int(result.population.sum()) != int(state[0][5]):
        raise ValueError("municipal and state totals disagree")
    return result


def export_candidate_with_population(
    manifest_path: Path, population_path: Path, output: Path
) -> None:
    """Publish the candidate and verified 2010 regional population without replacement."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    candidate_hash = _sha256(manifest_path)
    population_hash = _sha256(population_path)
    source_files = sorted(Path(__file__).parent.glob("*.py"))
    source_hashes = {p.name: _sha256(p) for p in source_files}
    a, w, _, _ = load_graphs(manifest_path)
    metadata = json.loads(manifest_path.read_text())
    crosswalk = pd.DataFrame(metadata["municipality_region"])
    if len(crosswalk) != 144:
        raise ValueError("candidate crosswalk must contain 144 municipalities")
    census = read_sidra_2010(population_path)
    population = aggregate_population(census, crosswalk, {"150475": "150680"})
    codes = {name: str(code) for code, name in PA_HEALTH_REGIONS_2013.items()}
    regions = [(codes[name], name) for name in hierarchy().leaves]
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    export_graph(a, w, regions, population, stage / "candidate.graphml")
    np.save(stage / "adjacency.npy", a)
    np.save(stage / "W.npy", w)
    manifest = {
        "status": "candidate_graph_population_complete",
        "interpretation_allowed": False,
        "candidate_manifest_sha256": candidate_hash,
        "population_source_sha256": population_hash,
        "population_source": str(population_path),
        "population_year": 2010,
        "population_citation": "IBGE, Censo Demográfico 2010, Tabela SIDRA 1378",
        "population_universe": "Dados do Universo",
        "population_notes": [
            "1 - Dados do Universo.",
            "2 - A categoria Pessoa responsável inclui as pessoas Sem declaração de compartilhamento de responsabilidade pelo domicílio.",
        ],
        "sidra_query_url": "https://apisidra.ibge.gov.br/values/k/1136872706",
        "sidra_query_label_as_supplied": "https://apisidra.ibge.gov.br/values/k/239831783",
        "query_independently_verified": False,
        "population_method": "143 municipios de 2010; Mojuí dos Campos e Santarém associados ao ancestral Santarém, contado uma vez na região 15002",
        "population_total": int(census.population.sum()),
        "population_regions": population,
        "source_sha256": source_hashes,
        "git_commit": subprocess.run(
            ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
        ).stdout.strip(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "node_order": [name for _, name in regions],
        "outputs": {p.name: _sha256(p) for p in stage.iterdir()},
    }
    (stage / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    )
    if (
        _sha256(manifest_path) != candidate_hash
        or _sha256(population_path) != population_hash
        or {p.name: _sha256(p) for p in source_files} != source_hashes
    ):
        raise ValueError("source changed during export")
    load_graphs(manifest_path)
    _publish(stage, output)
