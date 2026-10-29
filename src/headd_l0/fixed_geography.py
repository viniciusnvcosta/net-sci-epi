"""Fixed-series regional geography, separate from the historical P4 graph."""

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
import unicodedata
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

from headd_l0._sim_validation_io import _publish, _sha256
from headd_l0.data import hierarchy
from headd_l0.graph import (
    SWAP_BUDGET,
    _draw_placebos,
    _validate,
    build_adjacency,
    row_normalize,
)
from headd_l0.graph_io import PA_HEALTH_REGIONS_2013


def _code(value: object, width: int) -> str:
    if isinstance(value, str):
        if len(value) != width or not value.isascii() or not value.isdigit():
            raise ValueError("invalid code format")
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("invalid numeric code")  # noqa: TRY004 - invalid source value
    if not pd.notna(value) or int(value) != value:
        raise ValueError("invalid numeric code")
    result = str(int(value))
    if len(result) != width:
        raise ValueError("invalid code length")
    return result


def _name(value: object) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", str(value))
        .encode("ascii", "ignore")
        .decode()
        .upper()
        .split()
    )


def select_pa_crosswalk(relation: pd.DataFrame) -> pd.DataFrame:
    """Select PA municipalities, removing the explicit state aggregate."""
    result = relation[["municipality", "region"]].copy()
    result = result[result.municipality.astype(str).str.startswith("15")].copy()
    result["municipality"] = result.municipality.map(lambda x: _code(x, 6))
    result["region"] = result.region.map(lambda x: _code(x, 5))
    aggregate = result[result.municipality == "150000"]
    if len(aggregate) != 1 or aggregate.region.iloc[0] != "15000":
        raise ValueError("invalid PA aggregate")
    return result[result.municipality != "150000"].reset_index(drop=True)


def join_municipalities(
    municipalities: gpd.GeoDataFrame, relation: pd.DataFrame, names: pd.DataFrame
) -> gpd.GeoDataFrame:
    """Join 144 PA municipalities to their validated fixed regions."""
    m = municipalities.copy()
    r = relation[["municipality", "region"]].copy()
    if "abbrev_state" not in m or not m.abbrev_state.eq("PA").all():
        raise ValueError("municipalities must be PA")
    m["municipality"] = m.code_muni6.map(lambda x: _code(x, 6))
    r["municipality"] = r.municipality.map(lambda x: _code(x, 6))
    r["region"] = r.region.map(lambda x: _code(x, 5))
    if (
        len(m) != 144
        or len(r) != 144
        or m.municipality.duplicated().any()
        or r.municipality.duplicated().any()
        or not r.municipality.str.startswith("15").all()
        or set(m.municipality) != set(r.municipality)
    ):
        raise ValueError("municipality crosswalk is incomplete or duplicated")
    mapping = {str(k): v for k, v in PA_HEALTH_REGIONS_2013.items()}
    if (
        set(r.region) != set(mapping)
        or r.loc[r.municipality == "150795", "region"].item() != "15004"
    ):
        raise ValueError("invalid regional composition")
    n = names.copy()
    n = n[n.region.astype(str).isin(mapping)].copy()
    n["region"] = n.region.map(lambda x: _code(x, 5))
    n["name"] = n.name.map(_name)
    if (
        len(n) != 13
        or n.region.duplicated().any()
        or not n.status.eq("ATIVO").all()
        or not n.name.eq(n.region.map(mapping)).all()
    ):
        raise ValueError("invalid region names")
    joined = m.merge(r, on="municipality", validate="one_to_one")
    joined["name"] = joined.region.map(mapping)
    return joined


def candidate_graph(municipalities: gpd.GeoDataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Dissolve valid municipalities and build Queen adjacency and weights."""
    if (
        municipalities.geometry.isna().any()
        or municipalities.geometry.is_empty.any()
        or not municipalities.geometry.is_valid.all()
        or not municipalities.geom_type.isin(["Polygon", "MultiPolygon"]).all()
    ):
        raise ValueError("invalid municipal geometry")
    regions = municipalities[["name", "geometry"]].dissolve(by="name").reset_index()
    a = build_adjacency(regions, tuple(hierarchy().leaves))
    return a, row_normalize(a)


def _edges(a: np.ndarray, names: tuple[str, ...]) -> list[list[str]]:
    return [
        [names[i], names[j]]
        for i in range(len(names))
        for j in range(i + 1, len(names))
        if a[i, j]
    ]


def main(argv: list[str] | None = None) -> int:
    """Build a separately identified candidate from verified local sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args(argv)
    config = tomllib.loads(args.config.read_text())
    if (
        type(config["root_seed"]) is not int
        or config["root_seed"] != 42
        or type(config["n_placebos"]) is not int
        or config["n_placebos"] != 30
    ):
        raise ValueError("candidate requires seed 42 and 30 placebos")
    output = Path(config["output_dir"])
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    inputs = {}
    for key in ("relation", "names", "geometry", "p4_adjacency"):
        path = Path(config[key])
        digest = _sha256(path)
        if digest != config[f"{key}_sha256"]:
            raise ValueError(f"source hash mismatch: {key}")
        inputs[key] = {"path": str(path), "sha256": digest}
    relation = pd.read_csv(
        config["relation"],
        sep=";",
        header=None,
        names=["municipality", "region"],
        dtype=str,
    )
    names = pd.read_csv(
        config["names"],
        sep=";",
        header=None,
        names=["region", "status", "name", "level"],
        dtype=str,
        encoding="latin1",
    )
    geometry = gpd.read_parquet(config["geometry"])
    geometry = geometry[geometry.abbrev_state == "PA"].copy()
    municipalities = join_municipalities(geometry, select_pa_crosswalk(relation), names)
    a, w = candidate_graph(municipalities)
    p4 = np.load(config["p4_adjacency"], allow_pickle=False)
    _validate(p4)
    if p4.shape != a.shape:
        raise ValueError("P4 shape mismatch")
    draws, diagnostics = _draw_placebos(a, 30, np.random.default_rng(42))
    if len(draws) != 30:
        raise ValueError("incomplete placebo set")
    seen = {a.tobytes()}
    for draw in draws:
        _validate(draw)
        if (
            draw.shape != a.shape
            or not np.array_equal(draw.sum(axis=1), a.sum(axis=1))
            or draw.tobytes() in seen
        ):
            raise ValueError("invalid placebo")
        seen.add(draw.tobytes())
    labels = tuple(hierarchy().leaves)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    np.save(stage / "adjacency.npy", a)
    np.save(stage / "W.npy", w)
    np.save(stage / "placebos.npy", np.stack(draws))
    outputs = {p.name: _sha256(p) for p in sorted(stage.glob("*.npy"))}
    root = Path(__file__).resolve().parents[2]
    commit = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    source_status = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", "src/headd_l0"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    source_hashes = {
        str(p.relative_to(root)): _sha256(p)
        for p in sorted((root / "src/headd_l0").glob("*.py"))
    }
    manifest = {
        "status": "candidate_only",
        "interpretation_allowed": False,
        "rule": "fixed-series-pa-v1",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "source_sha256": source_hashes,
        "source_git_status": source_status,
        "config_sha256": _sha256(args.config),
        "inputs": inputs,
        "outputs": outputs,
        "versions": {
            name: version(name)
            for name in ("numpy", "pandas", "geopandas", "libpysal", "shapely")
        },
        "python_version": sys.version,
        "geos_version": shapely.geos_version_string,
        "root_seed": 42,
        "n_placebos": 30,
        "placebo_budget": SWAP_BUDGET,
        "placebo_diagnostics": diagnostics,
        "region_names": labels,
        "municipality_region": municipalities[["municipality", "region"]]
        .sort_values("municipality")
        .to_dict(orient="records"),
        "edges": _edges(a, labels),
        "degrees": a.sum(axis=1).tolist(),
        "p4_edges": _edges(p4, labels),
        "p4_degrees": p4.sum(axis=1).tolist(),
        "added_edges": _edges(a & (1 - p4), labels),
        "removed_edges": _edges(p4 & (1 - a), labels),
        "topology_check": "expected"
        if len(_edges(a, labels)) == 26
        and len(_edges(p4, labels)) == 25
        and _edges(a & (1 - p4), labels) == [["LAGO DE TUCURUI", "METROPOLITANA II"]]
        and not _edges(p4 & (1 - a), labels)
        else "unexpected",
        "p4_W": row_normalize(p4).tolist(),
        "W": w.tolist(),
    }
    (stage / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    _publish(stage, output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
