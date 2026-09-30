"""Acquisition diagnostics, provenance, canonicalization and verified caches."""

import hashlib
import json
from pathlib import Path

import geopandas as gpd
import networkx as nx
import numpy as np
import pytest
from shapely.geometry import Polygon, box

from headd_l0 import graph, graph_io
from headd_l0.data import hierarchy


def acquisition_fixture():
    names = hierarchy().leaves
    return (
        gpd.GeoDataFrame(
            {
                "code_health_region": [
                    15001,
                    15002,
                    15003,
                    15004,
                    15013,
                    15014,
                    15006,
                    15007,
                    15008,
                    15009,
                    15010,
                    15011,
                    15012,
                ],
                "name_health_region": names,
                "abbrev_state": "PA",
            },
            geometry=[box(i % 4, i // 4, i % 4 + 1, i // 4 + 1) for i in range(13)],
            crs="EPSG:4674",
        )
        .iloc[::-1]
        .reset_index(drop=True)
    )


def config_file(tmp_path):
    path = tmp_path / "graph.toml"
    path.write_text(
        f'run_id = "test-graph"\nroot_seed = 42\nyear = 2013\nsimplified = false\nn_placebos = 30\nprocessed_dir = "{tmp_path / "processed"}"\noutput_dir = "{tmp_path / "results"}"\n'
    )
    return path


def fake_download(**kwargs):
    assert kwargs["year"] == 2013 and kwargs["simplified"] is False
    assert kwargs["code_state"] == "PA" and kwargs["geometry_level"] == "micro"
    return acquisition_fixture()


def test_acquisition_exports_and_verified_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(graph_io.geobr, "read_health_region", fake_download)
    monkeypatch.setattr(graph, "CACHE_DIR", tmp_path / "processed")
    assert graph_io.main([str(config_file(tmp_path))]) == 0
    A, names = graph.adjacency()
    assert A.shape == (13, 13) and names == hierarchy().leaves
    root = tmp_path / "processed"
    manifest = json.loads((tmp_path / "results/test-graph/manifest.json").read_text())
    assert manifest["status"] == "ready"
    assert manifest["interpretation_allowed"] is False
    assert manifest["source"]["year"] == 2013
    assert manifest["source"]["simplified"] is False
    assert manifest["seed"]["entropy"] == 42
    assert manifest["cost"]["elapsed_seconds"] > 0
    assert (
        len(manifest["placebos"]["sha256"])
        == len(set(manifest["placebos"]["sha256"]))
        == 30
    )
    assert len(manifest["placebos"]["pairwise_edge_distance"]) == 435
    assert len(manifest["name_mapping"]) == 13
    for rel, sha in manifest["artifact_sha256"].items():
        assert hashlib.sha256((root / rel).read_bytes()).hexdigest() == sha
    S = nx.read_gexf(root / "S.gexf")
    assert S.number_of_nodes() == 14 and S.number_of_edges() == 13
    assert (root / "map.png").stat().st_size > 0
    assert len(list(root.glob("placebo_*.gexf"))) == 30
    np.testing.assert_array_equal(np.load(root / "S.npy")[0], 1)
    with pytest.raises(FileExistsError):
        graph_io.main([str(config_file(tmp_path))])
    np.save(root / "adjacency.npy", np.zeros((13, 13)))
    with pytest.raises(ValueError, match="hash|checksum"):
        graph.adjacency()


@pytest.mark.parametrize(
    "failure", ["cardinality", "disconnected", "network", "empty", "code"]
)
def test_acquisition_failure_preserves_diagnostics(tmp_path, monkeypatch, failure):
    def download(**kwargs):
        result = fake_download(**kwargs)
        if failure == "network":
            raise OSError("source unavailable")
        if failure == "cardinality":
            return result.iloc[:-1]
        if failure == "disconnected":
            result.loc[0, "geometry"] = box(100, 100, 101, 101)
        if failure == "code":
            result["code_health_region"] = result.code_health_region.astype(float)
            result.loc[0, "code_health_region"] = 15001.5
        if failure == "empty":
            result.loc[0, "geometry"] = Polygon()
        return result

    monkeypatch.setattr(graph_io.geobr, "read_health_region", download)
    monkeypatch.setattr(graph, "CACHE_DIR", tmp_path / "processed")
    assert graph_io.main([str(config_file(tmp_path))]) == 2
    manifest = json.loads((tmp_path / "results/test-graph/manifest.json").read_text())
    assert manifest["status"] == "blocked"
    assert manifest["error"] and manifest["cost"]["elapsed_seconds"] > 0
    assert manifest["placebo_budget"]["accepted_per_edge"] == 10
    if failure == "cardinality":
        assert (tmp_path / "processed/source_map.png").stat().st_size > 0
    assert not (tmp_path / "processed/adjacency.npy").exists()
    if failure != "network":
        assert (tmp_path / "processed/source_regions.parquet").exists()
    with pytest.raises(ValueError, match="ready"):
        graph.adjacency()


@pytest.mark.parametrize(
    "field,value",
    [
        ("year", 2013.0),
        ("n_placebos", 30.0),
        ("root_seed", True),
        ("run_id", ".."),
        ("processed_dir", ""),
    ],
)
def test_invalid_config_cannot_start_acquisition(tmp_path, field, value):
    values = {
        "run_id": "test",
        "year": 2013,
        "simplified": False,
        "root_seed": 42,
        "n_placebos": 30,
        "processed_dir": tmp_path / "processed",
        "output_dir": tmp_path / "results",
    }
    values[field] = value
    with pytest.raises(ValueError):
        graph_io.GraphConfig(**values)


def test_download_provenance_and_municipality_dissolve(tmp_path, monkeypatch):
    import pandas as pd

    cached = tmp_path / "geobr-cache"
    cached.mkdir()
    source = acquisition_fixture()
    source.loc[source.name_health_region == "MARAJO I", "name_health_region"] = (
        "Marajó I"
    )
    last = source.iloc[-1:].copy()
    source.loc[source.index[-1], "geometry"] = box(0, 0, 0.5, 1)
    last.loc[last.index[0], "geometry"] = box(0.5, 0, 1, 1)
    municipalities = gpd.GeoDataFrame(
        pd.concat([source, last], ignore_index=True), crs=source.crs
    )
    asset = "healthregions_2013.parquet"
    municipalities.to_parquet(cached / asset)
    url = f"https://github.com/ipea/geobr_prep_data/releases/download/v2.0.0/{asset}"
    pd.DataFrame([{"file_name": asset, "download_url": url}]).to_parquet(
        cached / "metadata_geobr_v2.parquet"
    )
    monkeypatch.setattr(graph_io, "cache_dir", lambda: cached)
    monkeypatch.setattr(
        graph_io.geobr, "read_health_region", lambda **kwargs: municipalities
    )
    assert graph_io.main([str(config_file(tmp_path))]) == 0
    manifest = json.loads((tmp_path / "results/test-graph/manifest.json").read_text())
    assert manifest["local_dissolve"] is True
    assert manifest["source"]["downloads"] == [
        {
            "file": asset,
            "sha256": hashlib.sha256((cached / asset).read_bytes()).hexdigest(),
            "catalog_url": url,
        }
    ]
    assert manifest["contiguity"] == "queen"
    assert (
        manifest["code_sha256"]["graph.py"]
        == hashlib.sha256(Path(graph.__file__).read_bytes()).hexdigest()
    )
    canonical = gpd.read_parquet(tmp_path / "processed/regions.parquet")
    assert canonical.name.tolist() == list(hierarchy().leaves)
    assert canonical.loc[0, "geometry"].equals(box(0, 0, 1, 1))


@pytest.mark.parametrize(
    "field,value", [("geometry_level", "municipality"), ("code_state", "SP")]
)
def test_incompatible_cache_source_is_rejected(tmp_path, monkeypatch, field, value):
    monkeypatch.setattr(graph_io.geobr, "read_health_region", fake_download)
    monkeypatch.setattr(graph, "CACHE_DIR", tmp_path / "processed")
    assert graph_io.main([str(config_file(tmp_path))]) == 0
    path = tmp_path / "processed/manifest.json"
    manifest = json.loads(path.read_text())
    manifest["source"][field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="source"):
        graph.adjacency()


@pytest.mark.parametrize("corruption", ["unknown_codes", "swapped_names"])
def test_source_region_identity_mismatch_is_blocked(tmp_path, monkeypatch, corruption):
    source = acquisition_fixture()
    if corruption == "unknown_codes":
        source["code_health_region"] = list(range(15901, 15914))
    else:
        source.loc[[0, 1], "name_health_region"] = source.loc[
            [1, 0], "name_health_region"
        ].to_numpy()
    monkeypatch.setattr(graph_io.geobr, "read_health_region", lambda **kwargs: source)
    assert graph_io.main([str(config_file(tmp_path))]) == 2
    manifest = json.loads((tmp_path / "results/test-graph/manifest.json").read_text())
    assert manifest["status"] == "blocked"
    assert "codes" in manifest["error"]
    assert manifest["name_mapping_version"] == "datasus-pa-2013-v1"
    assert manifest["name_mapping"] == [
        {
            "code_health_region": int(row.code_health_region),
            "name_health_region": row.name_health_region,
            "name": row.name_health_region,
        }
        for row in source.itertuples()
    ]
    assert not (tmp_path / "processed/adjacency.npy").exists()
