import hashlib
import json

import networkx as nx
import numpy as np
import pytest

from headd_l0.data import hierarchy
from headd_l0.exploratory import load_graphs


@pytest.fixture
def graph_package(tmp_path, monkeypatch):
    from headd_l0 import exploratory

    candidate = nx.cycle_graph(13)
    a = nx.to_numpy_array(candidate, dtype=np.uint8)
    p4 = a.copy()
    p4[0, 1] = p4[1, 0] = 0
    w = a / a.sum(axis=1)[:, None]
    variants = []
    for seed in range(30):
        rng = np.random.default_rng(seed)
        order = rng.permutation(13)
        edges = list(zip(order, np.roll(order, -1), strict=True))
        graph = nx.Graph(edges)
        variants.append(nx.to_numpy_array(graph, nodelist=range(13), dtype=np.uint8))
    for name, array in [
        ("adjacency.npy", a),
        ("W.npy", w),
        ("placebos.npy", np.stack(variants)),
        ("p4.npy", p4),
    ]:
        np.save(tmp_path / name, array)
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    manifest = {
        "region_names": list(hierarchy().leaves),
        "outputs": {
            name: digest(tmp_path / name)
            for name in ["adjacency.npy", "W.npy", "placebos.npy"]
        },
        "inputs": {
            "p4_adjacency": {
                "path": str(tmp_path / "p4.npy"),
                "sha256": digest(tmp_path / "p4.npy"),
            }
        },
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest))
    monkeypatch.setattr(exploratory, "CANDIDATE_MANIFEST_SHA256", digest(path))
    return path


def test_candidate_binding_and_generator(graph_package):
    candidate, w, p4, placebos = load_graphs(graph_package)
    assert np.array_equal(w, candidate / candidate.sum(axis=1)[:, None])
    assert not np.array_equal(candidate, p4)
    assert placebos.shape == (30, 13, 13)
    target = graph_package.parent / "placebos.npy"
    target.write_bytes(target.read_bytes() + b"X")
    with pytest.raises(ValueError, match="hash"):
        load_graphs(graph_package)
