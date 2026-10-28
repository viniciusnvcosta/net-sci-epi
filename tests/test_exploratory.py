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


def test_candidate_rejects_changed_source(graph_package, monkeypatch):
    from headd_l0 import exploratory

    source = graph_package.parent / "relation.csv"
    source.write_text("original")
    manifest = json.loads(graph_package.read_text())
    manifest["inputs"]["relation"] = {
        "path": str(source),
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    }
    graph_package.write_text(json.dumps(manifest))
    monkeypatch.setattr(
        exploratory,
        "CANDIDATE_MANIFEST_SHA256",
        hashlib.sha256(graph_package.read_bytes()).hexdigest(),
    )
    source.write_text("changed")
    with pytest.raises(ValueError, match="hash"):
        load_graphs(graph_package)


def test_score_replicate_reuses_counts_and_zscore_is_causal(monkeypatch):
    from headd_l0 import exploratory

    counts = np.ones((13, 132))
    counts[:, 80] = 5
    observed = []

    def fake_score(values, cfg, arms, graphs, seed):
        observed.append(values.copy())
        return np.ones((len(arms), 13, 72)), {}, {"fit_valid": True}

    monkeypatch.setattr(exploratory, "_score", fake_score)
    graphs = {
        "observed": np.eye(13),
        "p4": np.eye(13),
        **{f"placebo-{i:02d}": np.eye(13) for i in range(3)},
    }
    a = exploratory.score_replicate(counts, graphs, np.random.SeedSequence(3))
    altered = counts.copy()
    altered[:, 100:] = 100
    b = exploratory.score_replicate(altered, graphs, np.random.SeedSequence(3))
    assert len(observed) == 2
    assert np.array_equal(observed[0], counts)
    assert a.shape == (7, 13, 72)
    assert np.array_equal(a[-1, :, :40], b[-1, :, :40])


def test_score_fails_closed_on_invalid_nb2(monkeypatch):
    from headd_l0 import exploratory

    def invalid(*args):
        return np.full((6, 13, 72), np.nan), {}, {"fit_valid": False}

    monkeypatch.setattr(exploratory, "_score", invalid)
    with pytest.raises(ValueError, match="invalid NB2"):
        exploratory.score_replicate(np.ones((13, 132)), {}, np.random.SeedSequence(1))


def test_simulation_seed_addresses_and_generator(monkeypatch):
    from headd_l0 import exploratory

    seen = []

    def fake_simulate(config, weights, rng):
        seen.append((config, weights.copy(), rng.integers(100000)))
        return "result"

    monkeypatch.setattr(exploratory, "simulate", fake_simulate)
    w = np.eye(13)
    assert (
        exploratory.simulate_replicate(w, 0.2, "T", "pilot", 0, (1e-6,) * 13)
        == "result"
    )
    exploratory.simulate_replicate(w, 0.2, "T", "pilot", 0, (1e-6,) * 13)
    exploratory.simulate_replicate(w, 0.2, "T", "evaluation", 0, (1e-6,) * 13)
    assert np.array_equal(seen[0][1], w)
    assert seen[0][2] == seen[1][2]
    assert seen[0][2] != seen[2][2]
    assert seen[0][0].epsilon == 0.2
