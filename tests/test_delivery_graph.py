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
