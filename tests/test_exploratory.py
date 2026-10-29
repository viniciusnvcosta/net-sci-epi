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


def test_calibration_binding_rejects_changed_bytes(tmp_path, monkeypatch):
    from headd_l0 import exploratory

    artifact = tmp_path / "endemic_calibration.npz"
    np.savez(artifact, names=np.array(hierarchy().leaves), hazards=np.full(13, 0.1))
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "status": "ready",
                "config": {"noise": "white", "profile_id": "P5-IMPL-2026-10-19-v1"},
                "artifact_sha256": {artifact.name: digest(artifact)},
            }
        )
    )
    monkeypatch.setattr(exploratory, "ENDEMIC_MANIFEST_SHA256", digest(manifest))
    monkeypatch.setattr(exploratory, "ENDEMIC_ARTIFACT_SHA256", digest(artifact))
    assert exploratory.load_hazards(tmp_path) == (0.1,) * 13
    artifact.write_bytes(artifact.read_bytes() + b"X")
    with pytest.raises(ValueError, match="hash"):
        exploratory.load_hazards(tmp_path)


def test_far_requires_disjoint_complete_nulls():
    from headd_l0.exploratory import evaluate_far

    calibration = np.zeros((2, 7, 13, 72))
    evaluation = np.zeros((2, 7, 13, 72))
    with pytest.raises(ValueError, match="200"):
        evaluate_far(
            calibration,
            evaluation,
            range(len(calibration)),
            range(1000, 1000 + len(evaluation)),
        )
    calibration = np.zeros((200, 7, 13, 72))
    evaluation = np.zeros((200, 7, 13, 72))
    evaluation[0, 0, 0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        evaluate_far(
            calibration,
            evaluation,
            range(len(calibration)),
            range(1000, 1000 + len(evaluation)),
        )


def test_far_rejects_overlapping_streams():
    from headd_l0.exploratory import evaluate_far

    scores = np.zeros((200, 7, 13, 72))
    with pytest.raises(ValueError, match="overlap"):
        evaluate_far(scores, scores, range(200), range(200))


def test_far_reports_per_arm_counts():
    from headd_l0.exploratory import evaluate_far

    calibration = np.zeros((200, 7, 13, 72))
    evaluation = np.zeros_like(calibration)
    evaluation[:3, 0, 0, :] = 1
    evaluation[3, 0, 0, :24] = 1
    rows = evaluate_far(calibration, evaluation, range(200), range(1000, 1200))
    assert len(rows) == 91
    assert rows[0]["alarms"] == 240 and rows[0]["n"] == 14400 and rows[0]["passed"]
    assert not rows[1]["passed"]


def test_pilot_uses_candidate_weights_and_discards_scores(monkeypatch):
    from types import SimpleNamespace

    from headd_l0 import exploratory

    a = np.eye(13)
    calls = []

    def fake_sim(weights, epsilon, label, partition, index, hazards):
        calls.append((weights.copy(), epsilon, label, partition, index))
        return SimpleNamespace(counts=np.zeros((13, 132)))

    monkeypatch.setattr(exploratory, "simulate_replicate", fake_sim)
    monkeypatch.setattr(
        exploratory, "score_replicate", lambda *args: np.zeros((7, 13, 72))
    )
    monkeypatch.setattr(exploratory, "measure_arm_costs", lambda *args: {})
    records = exploratory.measure_pilot(a, {}, (1e-6,) * 13)
    assert len(records) == 4
    assert {(x[1], x[2]) for x in calls} == {
        (0.0, "T"),
        (0.0, "N"),
        (0.2, "T"),
        (0.2, "N"),
    }
    assert all(np.array_equal(x[0], a) and x[3] == "pilot" for x in calls)
    assert all(
        "scores" not in record and record["simulation_seconds"] >= 0
        for record in records
    )


def test_timing_requires_both_far_checks():
    from headd_l0.exploratory import evaluate_timings

    scores = np.zeros((1, 7, 13, 72))
    scores[0, 1, 0, 10] = 2
    onsets = np.full((1, 13), -1)
    onsets[0, 0] = 70
    far = [
        {"arm": a, "region": r, "threshold": 1.0, "passed": True}
        for a in range(7)
        for r in range(13)
    ]
    far[0]["passed"] = False
    rows = evaluate_timings(scores, onsets, far)
    row = next(x for x in rows if x["region"] == 0 and x["reference_arm"] == 0)
    assert row["b2_restricted_lead"] == 0
    assert row["comparable"] is False and row["gain"] is None


def test_budget_can_use_one_placebo(monkeypatch):
    from headd_l0 import exploratory

    monkeypatch.setattr(
        exploratory,
        "_score",
        lambda counts, cfg, arms, graphs, seed: (
            np.zeros((len(arms), 13, 72)),
            {},
            {"fit_valid": True},
        ),
    )
    values = exploratory.score_replicate(
        np.ones((13, 132)), {}, np.random.SeedSequence(3), 1
    )
    assert values.shape == (5, 13, 72)
    cal = np.zeros((200, 5, 13, 72))
    far = exploratory.evaluate_far(cal, cal.copy(), range(200), range(1000, 1200))
    assert len(far) == 65


def test_arm_costs_measure_all_predeclared_arms(monkeypatch):
    from headd_l0 import exploratory

    monkeypatch.setattr(
        exploratory,
        "_score",
        lambda counts, cfg, arms, graphs, seed: (
            np.zeros((len(arms), 13, 72)),
            {},
            {"fit_valid": True},
        ),
    )
    times = exploratory.measure_arm_costs(
        np.ones((13, 132)), {}, np.random.SeedSequence(3)
    )
    assert set(times) == {
        "B1*",
        "B2",
        "B2-P4",
        "B2-placebo-00",
        "B2-placebo-01",
        "B2-placebo-02",
        "zscore",
    }
    assert all(value >= 0 for value in times.values())


def test_candidate_rejects_changed_source_code(graph_package, monkeypatch):
    from headd_l0 import exploratory

    source = graph_package.parent / "code.py"
    source.write_text("original")
    manifest = json.loads(graph_package.read_text())
    manifest["source_sha256"] = {
        str(source): hashlib.sha256(source.read_bytes()).hexdigest()
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
