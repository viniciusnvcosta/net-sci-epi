"""Tests for the fixed-series geography candidate."""

import hashlib
import json

import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
import pytest
from shapely.geometry import box

from headd_l0.graph_io import PA_HEALTH_REGIONS_2013


@pytest.fixture
def geography_inputs():
    codes = [f"15{i:04d}" for i in range(1, 144)] + ["150795"]
    regions = list(PA_HEALTH_REGIONS_2013)
    assigned = [str(regions[i % 13]) for i in range(143)] + ["15004"]
    relation = pd.DataFrame({"municipality": codes, "region": assigned})
    municipality = gpd.GeoDataFrame(
        {"code_muni6": [int(c) for c in codes], "abbrev_state": "PA"},
        geometry=[box(i, 0, i + 1, 1) for i in range(144)],
        crs="EPSG:4674",
    )
    names = pd.DataFrame(
        [(str(k), "ATIVO", v, "1") for k, v in PA_HEALTH_REGIONS_2013.items()],
        columns=["region", "status", "name", "level"],
    )
    return municipality, relation, names


def test_crosswalk_selects_pa_and_aggregate(geography_inputs):
    from headd_l0.fixed_geography import join_municipalities, select_pa_crosswalk

    municipalities, relation, names = geography_inputs
    relation = pd.concat(
        [
            relation,
            pd.DataFrame(
                {
                    "municipality": ["150000", "110001", "0"],
                    "region": ["15000", "11001", "0"],
                }
            ),
        ],
        ignore_index=True,
    )
    selected = select_pa_crosswalk(relation)
    assert len(selected) == 144
    result = join_municipalities(municipalities, selected, names)
    assert len(result) == 144
    assert result.loc[result.code_muni6 == 150795, "name"].item() == "LAGO DE TUCURUI"
    municipalities["code_muni6"] = municipalities.code_muni6.astype(str)
    assert len(join_municipalities(municipalities, selected, names)) == 144


@pytest.mark.parametrize(
    "failure",
    ["missing", "duplicate", "fraction", "external", "region", "name", "tailandia"],
)
def test_crosswalk_rejects_bad_input(geography_inputs, failure):
    from headd_l0.fixed_geography import join_municipalities

    municipalities, relation, names = geography_inputs
    if failure == "missing":
        relation = relation.iloc[:-1]
    elif failure == "duplicate":
        relation = pd.concat([relation, relation.iloc[[0]]], ignore_index=True)
    elif failure == "fraction":
        municipalities["code_muni6"] = municipalities.code_muni6.astype(float)
        municipalities.loc[0, "code_muni6"] = 150001.5
    elif failure == "external":
        relation.loc[0, "municipality"] = "110001"
    elif failure == "region":
        relation.loc[0, "region"] = "15999"
    elif failure == "name":
        names.loc[0, "name"] = "OUTRA"
    else:
        relation.loc[143, "region"] = "15011"
    with pytest.raises(ValueError):
        join_municipalities(municipalities, relation, names)


@pytest.fixture
def connected_regions():
    from headd_l0.data import hierarchy

    return gpd.GeoDataFrame(
        {"name": hierarchy().leaves},
        geometry=[box(i, 0, i + 1, 1) for i in range(13)],
        crs="EPSG:4674",
    )


def test_candidate_graph_queen_and_weights(connected_regions):
    from headd_l0.fixed_geography import candidate_graph

    a, w = candidate_graph(connected_regions)
    expected = np.diag(np.ones(12, dtype=np.uint8), 1)
    expected += expected.T
    np.testing.assert_array_equal(a, expected)
    np.testing.assert_allclose(w.sum(axis=1), 1)
    np.testing.assert_array_equal(np.diag(a), np.zeros(13))


@pytest.mark.parametrize("failure", ["empty", "invalid", "island"])
def test_candidate_graph_rejects_bad_geometry(connected_regions, failure):
    from shapely.geometry import Polygon

    from headd_l0.fixed_geography import candidate_graph

    if failure == "empty":
        connected_regions.loc[0, "geometry"] = Polygon()
    elif failure == "invalid":
        connected_regions.loc[0, "geometry"] = Polygon(
            [(0, 0), (1, 1), (1, 0), (0, 1), (0, 0)]
        )
    else:
        connected_regions.loc[0, "geometry"] = box(50, 0, 51, 1)
    with pytest.raises(ValueError):
        candidate_graph(connected_regions)


@pytest.fixture
def publication_inputs(tmp_path, geography_inputs, monkeypatch):
    from headd_l0 import fixed_geography as fixed

    municipalities, relation, names = geography_inputs
    relation = pd.concat(
        [relation, pd.DataFrame({"municipality": ["150000"], "region": ["15000"]})],
        ignore_index=True,
    )
    paths = {
        key: tmp_path / key for key in ("relation", "names", "geometry", "p4_adjacency")
    }
    relation.to_csv(paths["relation"], sep=";", header=False, index=False)
    names.to_csv(paths["names"], sep=";", header=False, index=False)
    municipalities.to_parquet(paths["geometry"])
    original = nx.to_numpy_array(nx.cycle_graph(13), dtype=np.uint8)
    with paths["p4_adjacency"].open("wb") as f:
        np.save(f, original)
    rng = np.random.default_rng(42)
    draws = []
    seen = {original.tobytes()}
    while len(draws) < 30:
        order = rng.permutation(13)
        graph = nx.Graph()
        graph.add_nodes_from(range(13))
        graph.add_edges_from(zip(order, np.roll(order, -1)))
        candidate = nx.to_numpy_array(graph, nodelist=range(13), dtype=np.uint8)
        if candidate.tobytes() not in seen:
            draws.append(candidate)
            seen.add(candidate.tobytes())
    monkeypatch.setattr(fixed, "candidate_graph", lambda _: (original, original / 2))
    monkeypatch.setattr(fixed, "_draw_placebos", lambda *_: (draws, {"budget": {}}))
    hashes = {
        key: hashlib.sha256(path.read_bytes()).hexdigest()
        for key, path in paths.items()
    }
    config = tmp_path / "run.toml"
    output = tmp_path / "output"
    config.write_text(
        "\n".join(
            [
                f'{key} = "{path}"\n{key}_sha256 = "{hashes[key]}"'
                for key, path in paths.items()
            ]
        )
        + f'\noutput_dir = "{output}"\nroot_seed = 42\nn_placebos = 30\n'
    )
    return config, output, paths, original, draws


def test_publication_succeeds_with_manifest(publication_inputs):
    from headd_l0.fixed_geography import main

    config, output, _, _, _ = publication_inputs
    assert main([str(config)]) == 0
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["root_seed"] == 42
    assert manifest["interpretation_allowed"] is False
    for name, digest in manifest["outputs"].items():
        assert hashlib.sha256((output / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize(
    "failure", ["hash", "exists", "generator", "duplicate", "disconnected", "degree"]
)
def test_publication_rejects_failure(publication_inputs, monkeypatch, failure):
    from headd_l0 import fixed_geography as fixed

    config, output, paths, original, draws = publication_inputs
    if failure == "hash":
        paths["relation"].write_text("changed")
    elif failure == "exists":
        output.mkdir()
        (output / "keep").write_text("unchanged")
    elif failure == "generator":

        def fail(*args):
            raise RuntimeError("no candidates")

        monkeypatch.setattr(fixed, "_draw_placebos", fail)
    else:
        if failure == "duplicate":
            draws[-1] = draws[0]
        elif failure == "disconnected":
            draws[-1] = np.zeros_like(original)
        else:
            draws[-1] = np.ones_like(original) - np.eye(13, dtype=np.uint8)
    with pytest.raises((ValueError, FileExistsError, RuntimeError)):
        fixed.main([str(config)])
    assert not (output / "manifest.json").exists()
    if failure == "exists":
        assert (output / "keep").read_text() == "unchanged"
