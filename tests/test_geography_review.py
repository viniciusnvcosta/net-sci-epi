import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

from headd_l0._sim_validation_io import _sha256
from headd_l0.data import hierarchy
from headd_l0.geography_review import main, review_layers, verify_binding


@pytest.fixture
def binding_fixture(tmp_path, monkeypatch):
    import headd_l0.geography_review as review

    monkeypatch.chdir(tmp_path)
    config = tmp_path / "config.toml"
    config.write_text("test = true\n")
    source = tmp_path / "input"
    source.write_bytes(b"input")
    code = tmp_path / "code.py"
    code.write_bytes(b"code")
    output = tmp_path / "adjacency.npy"
    output.write_bytes(b"output")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "config_sha256": _sha256(config),
                "inputs": {"x": {"path": str(source), "sha256": _sha256(source)}},
                "outputs": {"adjacency.npy": _sha256(output)},
                "source_sha256": {str(code): _sha256(code)},
            }
        )
    )
    monkeypatch.setattr(review, "MANIFEST_SHA256", _sha256(manifest))
    return config, manifest, source, output


def test_binding_rejects_manifest(binding_fixture):
    config, manifest, _, _ = binding_fixture
    manifest.write_text("{}")
    with pytest.raises(ValueError, match="manifest"):
        verify_binding(config, manifest)


@pytest.mark.parametrize("which", ["source", "output", "config", "code"])
def test_binding_rejects_input_or_output(binding_fixture, which):
    config, manifest, source, output = binding_fixture
    target = {
        "source": source,
        "output": output,
        "config": config,
        "code": Path("code.py"),
    }[which]
    target.write_bytes(target.read_bytes() + b"X")
    with pytest.raises(ValueError, match="hash"):
        verify_binding(config, manifest)


@pytest.fixture
def municipal_fixture():
    names = tuple(hierarchy().leaves)
    return gpd.GeoDataFrame(
        {
            "name": names,
            "municipality": [
                "150795" if n == "LAGO DE TUCURUI" else str(150001 + i)
                for i, n in enumerate(names)
            ],
            "region": ["15004" if n == "LAGO DE TUCURUI" else "15001" for n in names],
        },
        geometry=[box(i, 0, i + 1, 1) for i in range(13)],
        crs="EPSG:4326",
    )


@pytest.fixture
def adjacency(municipal_fixture):
    from headd_l0.fixed_geography import candidate_graph

    return candidate_graph(municipal_fixture)[0]


def test_review_layers_require_tailandia(municipal_fixture, adjacency):
    municipal_fixture.loc[municipal_fixture.municipality == "150795", "name"] = (
        "TOCANTINS"
    )
    with pytest.raises(ValueError, match="Tailândia"):
        review_layers(municipal_fixture, adjacency, tuple(hierarchy().leaves))


def test_review_layers_reject_graph_or_names(municipal_fixture, adjacency):
    bad = adjacency.copy()
    bad[0, 1] = 1 - bad[0, 1]
    with pytest.raises(ValueError):
        review_layers(municipal_fixture, bad, tuple(hierarchy().leaves))
    with pytest.raises(ValueError):
        review_layers(municipal_fixture, adjacency, tuple(reversed(hierarchy().leaves)))


def test_review_layers_success(municipal_fixture, adjacency):
    regions, thailand = review_layers(
        municipal_fixture, adjacency, tuple(hierarchy().leaves)
    )
    assert len(regions) == 13
    assert thailand.municipality.iloc[0] == "150795"


def test_publish_no_replace(tmp_path):
    output = tmp_path / "output"
    output.mkdir()
    (output / "keep").write_text("preservar")
    with pytest.raises(FileExistsError):
        main(["missing.toml", "missing.json", str(output)])
    assert (output / "keep").read_text() == "preservar"
    assert not (output / "manifest.json").exists()


@pytest.fixture
def review_cli_fixture(tmp_path, monkeypatch, municipal_fixture, adjacency):
    import headd_l0.geography_review as review

    config = tmp_path / "config.toml"
    config.write_text(
        'relation = "unused"\nnames = "unused"\ngeometry = "unused"\np4_adjacency = "unused"\n'
    )
    manifest = tmp_path / "manifest.json"
    manifest.write_text("{}")
    output = tmp_path / "package"
    candidate = {"region_names": list(hierarchy().leaves), "inputs": {}, "outputs": {}}
    monkeypatch.setattr(review, "verify_binding", lambda *_: candidate)
    monkeypatch.setattr(review.pd, "read_csv", lambda *a, **kw: None)
    monkeypatch.setattr(
        review.gpd,
        "read_parquet",
        lambda *_: municipal_fixture.assign(abbrev_state="PA"),
    )
    monkeypatch.setattr(review, "select_pa_crosswalk", lambda x: x)
    monkeypatch.setattr(review, "join_municipalities", lambda *a: municipal_fixture)
    monkeypatch.setattr(review.np, "load", lambda *a, **kw: adjacency)
    return config, manifest, output


def test_render_failure_does_not_publish(review_cli_fixture, monkeypatch):
    import headd_l0.geography_review as review

    def fail(*args):
        raise RuntimeError("render failed")

    monkeypatch.setattr(review, "_render", fail)
    config, manifest, output = review_cli_fixture
    with pytest.raises(RuntimeError, match="render failed"):
        main([str(config), str(manifest), str(output)])
    assert not output.exists()


def test_publish_success_has_image_hashes(review_cli_fixture):
    config, manifest, output = review_cli_fixture
    assert main([str(config), str(manifest), str(output)]) == 0
    result = json.loads((output / "manifest.json").read_text())
    assert result["interpretation_allowed"] is False
    assert set(result["outputs"]) == {"mapa-regioes.png", "comparacao-arestas.png"}
    for name, digest in result["outputs"].items():
        assert (output / name).stat().st_size > 0
        assert _sha256(output / name) == digest
