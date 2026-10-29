import networkx as nx
import numpy as np
import pandas as pd
import pytest

from headd_l0.delivery_graph import aggregate_population, export_graph


def test_pre2013_aggregation():
    crosswalk = pd.DataFrame(
        {"municipality": ["1", "2", "3"], "region": ["a", "a", "b"]}
    )
    source = pd.DataFrame({"municipality": ["1", "3"], "population": [100, 50]})
    assert aggregate_population(source, crosswalk, {"2": "1"}) == {"a": 100, "b": 50}
    crosswalk.loc[1, "region"] = "b"
    with pytest.raises(ValueError, match="region"):
        aggregate_population(source, crosswalk, {"2": "1"})


def test_graphml_roundtrip(tmp_path):
    a = np.array([[0, 1, 0], [1, 0, 1], [0, 1, 0]])
    w = np.array([[0.0, 1.0, 0.0], [0.5, 0.0, 0.5], [0.0, 1.0, 0.0]])
    regions = [("1", "A"), ("2", "B"), ("3", "C")]
    out = tmp_path / "graph.graphml"
    export_graph(a, w, regions, {"1": 10, "2": 20, "3": 30}, out)
    graph = nx.read_graphml(out)
    assert len(graph) == 3 and graph.number_of_edges() == 4
    assert graph.nodes["1"]["population"] == 10
    assert graph["1"]["2"]["weight"] == 1.0
    assert graph["2"]["1"]["weight"] == 0.5
    assert graph["1"]["2"]["type"] == "queen"


def test_export_rejects_bad_binding(tmp_path):
    with pytest.raises(ValueError):
        export_graph(
            np.ones((2, 2)),
            np.ones((2, 2)),
            [("1", "A"), ("2", "B")],
            {"1": 1, "2": 1},
            tmp_path / "g",
        )


def test_publish_atomic_no_replace(tmp_path, monkeypatch):
    a = np.array([[0, 1], [1, 0]])
    w = a.astype(float)
    output = tmp_path / "graph.graphml"

    def fail(graph, handle):
        handle.write(b"partial")
        raise OSError("interrupted")

    monkeypatch.setattr(nx, "write_graphml", fail)
    with pytest.raises(OSError, match="interrupted"):
        export_graph(a, w, [("1", "A"), ("2", "B")], {"1": 10, "2": 20}, output)
    assert not output.exists()
    output.write_text("preserve")
    with pytest.raises(FileExistsError):
        export_graph(a, w, [("1", "A"), ("2", "B")], {"1": 10, "2": 20}, output)
    assert output.read_text() == "preserve"


def test_rejects_inexact_weights(tmp_path):
    a = np.array([[0, 1], [1, 0]])
    w = np.array([[0.0, 1.00000001], [1.0, 0.0]])
    with pytest.raises(ValueError, match="invalid"):
        export_graph(a, w, [("1", "A"), ("2", "B")], {"1": 1, "2": 1}, tmp_path / "g")


def test_export_rejects_disconnected_graph(tmp_path):
    a = np.zeros((4, 4), dtype=int)
    a[0, 1] = a[1, 0] = a[2, 3] = a[3, 2] = 1
    with pytest.raises(ValueError, match="invalid"):
        export_graph(
            a,
            a.astype(float),
            [("1", "A"), ("2", "B"), ("3", "C"), ("4", "D")],
            {"1": 1, "2": 1, "3": 1, "4": 1},
            tmp_path / "g",
        )


def test_graph_export_without_population_marks_absence(tmp_path):
    a = np.array([[0, 1], [1, 0]])
    output = tmp_path / "g.graphml"
    export_graph(a, a.astype(float), [("1", "A"), ("2", "B")], None, output)
    graph = nx.read_graphml(output)
    assert all("population" not in node for _, node in graph.nodes(data=True))


def test_candidate_export_is_bound_and_partial(tmp_path, monkeypatch):
    import json

    from headd_l0 import delivery_graph

    candidate = nx.cycle_graph(13)
    a = nx.to_numpy_array(candidate, dtype=np.uint8)
    w = a / 2
    placebo = np.repeat(a[None], 30, axis=0)
    monkeypatch.setattr(delivery_graph, "load_graphs", lambda _: (a, w, a, placebo))
    manifest = tmp_path / "candidate.json"
    manifest.write_text("{}")
    output = tmp_path / "package"
    delivery_graph.export_candidate_without_population(manifest, output)
    record = json.loads((output / "manifest.json").read_text())
    graph = nx.read_graphml(output / "candidate.graphml")
    assert record["status"] == "partial_population_pending"
    assert record["interpretation_allowed"] is False
    assert len(graph) == 13 and graph.number_of_edges() == 26
    assert all("population" not in x for _, x in graph.nodes(data=True))
    with pytest.raises(FileExistsError):
        delivery_graph.export_candidate_without_population(manifest, output)


def test_candidate_manifest_change_fails_before_publication(tmp_path, monkeypatch):
    from headd_l0 import delivery_graph

    a = nx.to_numpy_array(nx.cycle_graph(13), dtype=np.uint8)
    manifest = tmp_path / "candidate.json"
    manifest.write_text("original")

    def changed(_):
        manifest.write_text("changed")
        return a, a / 2, a, np.repeat(a[None], 30, axis=0)

    monkeypatch.setattr(delivery_graph, "load_graphs", changed)
    output = tmp_path / "package"
    with pytest.raises(ValueError, match="changed"):
        delivery_graph.export_candidate_without_population(manifest, output)
    assert not output.exists()


def test_sidra_rejects_urban_and_preserves_total(tmp_path):
    import csv

    from headd_l0.delivery_graph import read_sidra_2010

    path = tmp_path / "sidra.csv"
    rows = [
        ["Tabela 1378"],
        ["Variável - População residente"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "coluna"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "2010"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "Total"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "Total"],
        ["UF", "15", "Pará", "Total", "Total", "143", "Pessoas"],
    ]
    rows += [
        ["MU", f"15{i:04d}0", str(i), "Total", "Total", "1", "Pessoas"]
        for i in range(143)
    ]
    rows += [
        ["Notas"],
        ["1 - Dados do Universo."],
        [
            "2 - A categoria Pessoa responsável inclui as pessoas Sem declaração de compartilhamento de responsabilidade pelo domicílio."
        ],
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)
    result = read_sidra_2010(path)
    assert len(result) == 143 and result.population.sum() == 143
    rows[4][5] = "Urbana"
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)
    with pytest.raises(ValueError, match="Total"):
        read_sidra_2010(path)


def test_candidate_export_uses_verified_census_and_unique_ancestor(
    tmp_path, monkeypatch
):
    import hashlib
    import json

    from headd_l0 import delivery_graph
    from headd_l0.graph_io import PA_HEALTH_REGIONS_2013

    a = nx.to_numpy_array(nx.cycle_graph(13), dtype=np.uint8)
    monkeypatch.setattr(
        delivery_graph,
        "load_graphs",
        lambda _: (a, a / 2, a, np.repeat(a[None], 30, axis=0)),
    )
    codes = [str(c) for c in PA_HEALTH_REGIONS_2013]
    crosswalk = [
        {"municipality": f"15{i:04d}", "region": codes[i % 13]} for i in range(142)
    ]
    crosswalk.extend(
        [
            {"municipality": "150680", "region": "15002"},
            {"municipality": "150475", "region": "15002"},
        ]
    )
    source = pd.DataFrame(
        [
            {"municipality": r["municipality"], "population": 1}
            for r in crosswalk
            if r["municipality"] != "150475"
        ]
    )
    monkeypatch.setattr(delivery_graph, "read_sidra_2010", lambda _: source)
    manifest = tmp_path / "candidate.json"
    manifest.write_text(json.dumps({"municipality_region": crosswalk}))
    census = tmp_path / "census.csv"
    census.write_text("verified-by-test")
    out = tmp_path / "package"
    delivery_graph.export_candidate_with_population(manifest, census, out)
    graph = nx.read_graphml(out / "candidate.graphml")
    record = json.loads((out / "manifest.json").read_text())
    assert record["status"] == "candidate_graph_population_complete"
    assert record["interpretation_allowed"] is False
    assert (
        record["population_source_sha256"]
        == hashlib.sha256(census.read_bytes()).hexdigest()
    )
    assert sum(attrs["population"] for _, attrs in graph.nodes(data=True)) == 143
    assert graph.number_of_edges() == 26


def test_sidra_requires_universe_notes(tmp_path):
    import csv

    from headd_l0.delivery_graph import read_sidra_2010

    path = tmp_path / "census.csv"
    rows = [
        ["Tabela 1378"],
        ["População residente"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "coluna"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "2010"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "Total"],
        ["Nível", "Cód.", "Nome", "Idade", "Condição", "Total"],
        ["UF", "15", "Pará", "Total", "Total", "143", "Pessoas"],
    ]
    rows += [
        ["MU", f"15{i:04d}0", str(i), "Total", "Total", "1", "Pessoas"]
        for i in range(143)
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerows(rows)
    with pytest.raises(ValueError, match="notes"):
        read_sidra_2010(path)
