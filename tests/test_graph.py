"""Queen geometry, labeled rewiring and graph export contracts."""

import geopandas as gpd
import networkx as nx
import numpy as np
import pytest
from shapely.geometry import Polygon, box

from headd_l0 import graph
from headd_l0.data import hierarchy


@pytest.fixture
def regions():
    return gpd.GeoDataFrame(
        {"name": ["C", "A", "D", "B"]},
        geometry=[box(1, 1, 2, 2), box(0, 0, 1, 1), box(2, 1, 3, 2), box(1, 0, 2, 1)],
        crs="EPSG:4674",
    )


def test_queen_edges_and_canonical_names(regions):
    # A-C and B-D share only a vertex; source row order must not define identity.
    expected = [[0, 1, 1, 0], [1, 0, 1, 1], [1, 1, 0, 1], [0, 1, 1, 0]]
    np.testing.assert_array_equal(
        graph.build_adjacency(regions, tuple("ABCD")), expected
    )


def test_wrong_geography_level_rejected(regions):
    with pytest.raises(ValueError, match="names|regions"):
        graph.build_adjacency(regions, hierarchy().leaves)
    regions.loc[0, "name"] = "A"
    with pytest.raises(ValueError, match="names|regions"):
        graph.build_adjacency(regions, tuple("ABCD"))


def test_islands_rejected(regions):
    regions.loc[2, "geometry"] = box(10, 10, 11, 11)
    with pytest.raises(ValueError, match="disconnected"):
        graph.build_adjacency(regions, tuple("ABCD"))
    with pytest.raises(ValueError, match="disconnected|island"):
        graph.row_normalize(np.zeros((13, 13)))


@pytest.mark.parametrize(
    "geometry", [None, Polygon(), Polygon([(0, 0), (1, 1), (0, 1), (1, 0)])]
)
def test_invalid_geometries_are_not_silently_repaired(regions, geometry):
    regions.loc[0, "geometry"] = geometry
    with pytest.raises(ValueError, match="geometr"):
        graph.build_adjacency(regions, tuple("ABCD"))


def test_placebos_preserve_labeled_degrees():
    A = nx.to_numpy_array(nx.circulant_graph(13, [1, 2]), dtype=np.uint8)
    before = A.copy()
    draws = graph.placebos(A, 30, np.random.default_rng(42))
    again = graph.placebos(A, 30, np.random.default_rng(42))
    assert len(draws) == len({B.tobytes() for B in draws}) == 30
    for B, repeated in zip(draws, again, strict=True):
        np.testing.assert_array_equal(B.sum(axis=1), A.sum(axis=1))
        np.testing.assert_array_equal(B, repeated)
        assert np.array_equal(B, B.T) and not np.diag(B).any()
        assert nx.is_connected(nx.from_numpy_array(B))
        assert not np.array_equal(B, A)
    np.testing.assert_array_equal(A, before)


def test_placebo_degrees_keep_nonuniform_node_identity():
    A = nx.to_numpy_array(nx.barabasi_albert_graph(13, 2, seed=1), dtype=np.uint8)
    for B in graph.placebos(A, 3, np.random.default_rng(3)):
        np.testing.assert_array_equal(B.sum(axis=1), A.sum(axis=1))


@pytest.mark.parametrize("network", [nx.complete_graph(13), nx.star_graph(12)])
def test_unrewirable_graph_fails(network):
    with pytest.raises(RuntimeError, match="budget"):
        graph.placebos(nx.to_numpy_array(network), 1, np.random.default_rng(42))


def test_normalization_and_exports(tmp_path):
    A = nx.to_numpy_array(nx.cycle_graph(13), dtype=np.uint8)
    names = hierarchy().leaves
    np.testing.assert_allclose(graph.row_normalize(A).sum(axis=1), 1)
    path = tmp_path / "adjacency.gexf"
    graph.export_graph(A, names, path)
    network = nx.read_gexf(path)
    assert set(network) == set(names)
    assert network.number_of_edges() == 13
    assert set(network.edges()) == {
        (names[i], names[j]) for i, j in zip(*np.where(np.triu(A)), strict=True)
    }
    table = graph.centralities(A, names)
    assert table.name.tolist() == list(names)
    np.testing.assert_array_equal(table.degree, 2)
    np.testing.assert_allclose(table.eigenvector, 1 / np.sqrt(13))


@pytest.mark.parametrize(
    "A",
    [
        np.ones((2, 3)),
        np.eye(3),
        [[0, 1], [0, 0]],
        [[0, 2], [2, 0]],
        [[0, np.nan], [np.nan, 0]],
    ],
)
def test_invalid_adjacency_rejected(A):
    with pytest.raises(ValueError):
        graph.row_normalize(np.asarray(A))


def test_small_unrewirable_graph_fails_with_budget_error():
    with pytest.raises(RuntimeError, match="budget"):
        graph.placebos(np.array([[0, 1], [1, 0]]), 1, np.random.default_rng(42))
