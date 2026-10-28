"""Create a traceable visual review package for the fixed-series candidate."""

import argparse
import json
import subprocess
import tempfile
import tomllib
from datetime import UTC, datetime
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D

from headd_l0._sim_validation_io import _publish, _sha256
from headd_l0.data import hierarchy
from headd_l0.fixed_geography import (
    candidate_graph,
    join_municipalities,
    select_pa_crosswalk,
)

MANIFEST_SHA256 = "7a2050e059d037960fd0fce8839d66f57dd9d6cab5942441ea3ea54bee9d4fe0"


def verify_binding(config_path: Path, manifest_path: Path) -> dict:
    """Verify the candidate manifest and every file to which it binds."""
    if _sha256(manifest_path) != MANIFEST_SHA256:
        raise ValueError("manifest hash mismatch")
    manifest = json.loads(manifest_path.read_text())
    files = [(config_path, manifest["config_sha256"])]
    files += [(Path(v["path"]), v["sha256"]) for v in manifest["inputs"].values()]
    files += [(manifest_path.parent / k, v) for k, v in manifest["outputs"].items()]
    files += [(Path(k), v) for k, v in manifest["source_sha256"].items()]
    for path, expected in files:
        if _sha256(path) != expected:
            raise ValueError(f"hash mismatch: {path}")
    return manifest


def review_layers(
    municipalities: gpd.GeoDataFrame, a: np.ndarray, names: tuple[str, ...]
) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Validate the review geometry against the candidate adjacency and order."""
    if names != tuple(hierarchy().leaves):
        raise ValueError("region order mismatch")
    thailand = municipalities[municipalities.municipality == "150795"]
    if (
        len(thailand) != 1
        or thailand.iloc[0]["name"] != "LAGO DE TUCURUI"
        or thailand.iloc[0]["region"] != "15004"
    ):
        raise ValueError("Tailândia assignment mismatch")
    calculated, _ = candidate_graph(municipalities)
    if not np.array_equal(calculated, a):
        raise ValueError("adjacency mismatch")
    regions = (
        municipalities[["name", "geometry"]]
        .dissolve(by="name")
        .loc[list(names)]
        .reset_index()
    )
    return regions, thailand


def _render(
    regions: gpd.GeoDataFrame,
    thailand: gpd.GeoDataFrame,
    a: np.ndarray,
    p4: np.ndarray,
    stage: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(14, 11))
    regions.plot(
        column="name",
        categorical=True,
        cmap="tab20",
        ax=ax,
        edgecolor="black",
        linewidth=0.35,
    )
    thailand.boundary.plot(ax=ax, color="red", linewidth=2.2)
    points = regions.geometry.representative_point()
    for name, point in zip(regions["name"], points, strict=True):
        ax.annotate(
            name,
            (point.x, point.y),
            fontsize=7,
            ha="center",
            bbox={"facecolor": "white", "alpha": 0.7, "edgecolor": "none"},
        )
    ax.legend(
        handles=[Line2D([0], [0], color="red", lw=2, label="Tailândia")],
        loc="lower left",
    )
    ax.set_title("Regiões de saúde — composição fixa candidata")
    ax.set_axis_off()
    fig.savefig(stage / "mapa-regioes.png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(14, 11))
    regions.plot(ax=ax, color="#eeeeee", edgecolor="#888888", linewidth=0.4)
    for name, point in zip(regions["name"], points, strict=True):
        ax.annotate(
            name,
            (point.x, point.y),
            fontsize=7,
            ha="center",
            bbox={"facecolor": "white", "alpha": 0.8, "edgecolor": "none"},
        )
    for i in range(len(regions)):
        for j in range(i + 1, len(regions)):
            if a[i, j] != p4[i, j]:
                color = "green" if a[i, j] else "red"
                ax.plot(
                    [points.iloc[i].x, points.iloc[j].x],
                    [points.iloc[i].y, points.iloc[j].y],
                    color=color,
                    linewidth=2,
                )
    ax.legend(
        handles=[
            Line2D([0], [0], color="green", label="Adicionada"),
            Line2D([0], [0], color="red", label="Removida"),
        ],
        loc="lower left",
    )
    ax.set_title("Arestas alteradas frente a P4 — linhas esquemáticas")
    ax.set_axis_off()
    fig.savefig(stage / "comparacao-arestas.png", dpi=160, bbox_inches="tight")
    plt.close(fig)


def main(argv: list[str] | None = None) -> int:
    """Verify v2 and publish maps and provenance without replacing a package."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(args.output)
    manifest = verify_binding(args.config, args.manifest)
    config = tomllib.loads(args.config.read_text())
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
    geo = gpd.read_parquet(config["geometry"])
    municipalities = join_municipalities(
        geo[geo.abbrev_state == "PA"].copy(), select_pa_crosswalk(relation), names
    )
    a = np.load(args.manifest.parent / "adjacency.npy", allow_pickle=False)
    p4 = np.load(config["p4_adjacency"], allow_pickle=False)
    regions, thailand = review_layers(
        municipalities, a, tuple(manifest["region_names"])
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{args.output.name}-", dir=args.output.parent)
    )
    _render(regions, thailand, a, p4, stage)
    source = Path(__file__)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    result = {
        "status": "review_package",
        "interpretation_allowed": False,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "candidate_manifest_sha256": MANIFEST_SHA256,
        "config_sha256": _sha256(args.config),
        "inputs": manifest["inputs"],
        "candidate_outputs": manifest["outputs"],
        "region_names": manifest["region_names"],
        "review_code_sha256": _sha256(source),
        "outputs": {p.name: _sha256(p) for p in sorted(stage.glob("*.png"))},
    }
    (stage / "manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    _publish(stage, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
