"""Explicit DataSUS/geobr acquisition, audit artifacts and graph CLI."""

import argparse
import inspect
import json
import resource
import shutil
import subprocess
import time
import tomllib
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import geobr
import geopandas as gpd
import networkx as nx
import numpy as np
import pandas as pd
from geobr._cache import cache_dir
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from headd_l0.data import hierarchy
from headd_l0.graph import (
    SWAP_BUDGET,
    _draw_placebos,
    _sha,
    build_adjacency,
    centralities,
    export_graph,
    row_normalize,
)
from headd_l0.reconcile import summing_matrix

GEOBR_SOURCE = Path(inspect.getfile(geobr.read_health_region))


@dataclass(frozen=True)
class GraphConfig:
    """Explicit scientific source and local artifact destinations."""

    run_id: str
    root_seed: int
    year: int
    simplified: bool
    n_placebos: int
    processed_dir: Path
    output_dir: Path

    def __post_init__(self) -> None:
        """Validate the approved source and normalize artifact paths."""
        if (
            type(self.year) is not int
            or self.year != 2013
            or self.simplified is not False
            or type(self.n_placebos) is not int
            or self.n_placebos != 30
        ):
            raise ValueError("P4 requires year=2013, simplified=false and 30 placebos")
        if type(self.root_seed) is not int or self.root_seed < 0:
            raise ValueError("root_seed must be a nonnegative integer")
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or Path(self.run_id).name != self.run_id
            or self.run_id in {".", ".."}
        ):
            raise ValueError("run_id must be a directory name")
        for name in ("processed_dir", "output_dir"):
            value = getattr(self, name)
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{name} must be a nonempty path")
            object.__setattr__(self, name, Path(value).expanduser())


def _canonical_regions(regions: gpd.GeoDataFrame, manifest: dict) -> gpd.GeoDataFrame:
    code, name = "code_health_region", "name_health_region"
    if not {code, name}.issubset(regions.columns):
        raise ValueError("source lacks health-region codes/names")
    mapping = regions[[code, name]].drop_duplicates().copy()
    mapping["name"] = mapping[name].map(
        lambda s: " ".join(
            unicodedata.normalize("NFKD", str(s))
            .encode("ascii", "ignore")
            .decode()
            .upper()
            .split()
        )
    )
    manifest["name_mapping"] = json.loads(mapping.to_json(orient="records"))
    if (
        len(mapping) != 13
        or mapping[code].duplicated().any()
        or mapping["name"].duplicated().any()
        or set(mapping["name"]) != set(hierarchy().leaves)
        or not mapping[code].astype(str).str.startswith("15").all()
        or not (pd.to_numeric(mapping[code]) % 1 == 0).all()
    ):
        raise ValueError(
            f"source must contain exactly 13 PA regional codes and canonical names; observed {len(mapping)}"
        )
    if "abbrev_state" in regions and not (regions.abbrev_state == "PA").all():
        raise ValueError("source includes non-PA regions")
    regions = regions.merge(mapping[[code, "name"]], on=code, validate="many_to_one")
    if (
        regions.geometry.isna().any()
        or regions.geometry.is_empty.any()
        or not regions.geometry.is_valid.all()
    ):
        raise ValueError("empty or invalid source geometries; no local repairs")
    manifest["local_dissolve"] = bool(regions[code].duplicated().any())
    if manifest["local_dissolve"]:
        regions = regions[["name", "geometry"]].dissolve(by="name").reset_index()
    return regions.set_index("name").loc[list(hierarchy().leaves)].reset_index()


def _map(regions: gpd.GeoDataFrame, path: Path) -> None:
    figure = Figure(figsize=(10, 8))
    FigureCanvasAgg(figure)
    axis = figure.subplots()
    regions.plot(ax=axis, facecolor="#e5edf4", edgecolor="#283a4c", linewidth=0.5)
    for _, row in regions.iterrows():
        point = row.geometry.representative_point()
        axis.annotate(row["name"], (point.x, point.y), fontsize=6)
    axis.set_title("DataSUS 2013 / geobr original resolution — Queen diagnostic")
    figure.savefig(path, dpi=160, bbox_inches="tight")


def _artifacts(regions: gpd.GeoDataFrame, cfg: GraphConfig, manifest: dict) -> None:
    path, names = cfg.processed_dir, hierarchy().leaves
    regions.to_parquet(path / "regions.parquet", index=False)
    _map(regions, path / "map.png")
    A = build_adjacency(regions, names)
    manifest["degrees"] = A.sum(axis=1).tolist()
    draws, manifest["placebos"] = _draw_placebos(
        A, cfg.n_placebos, np.random.default_rng(cfg.root_seed)
    )
    np.save(path / "adjacency.npy", A)
    np.save(path / "W.npy", row_normalize(A))
    np.save(path / "placebos.npy", np.stack(draws))
    S = summing_matrix(hierarchy())
    np.save(path / "S.npy", S)
    tree = nx.DiGraph()
    tree.add_edges_from((hierarchy().state, name) for name in names)
    nx.write_gexf(tree, path / "S.gexf")
    export_graph(A, names, path / "A.gexf")
    for i, B in enumerate(draws):
        export_graph(B, names, path / f"placebo_{i:02d}.gexf")
    centralities(A, names).to_parquet(path / "centralities.parquet", index=False)


def _preserve_sources(path: Path, manifest: dict) -> None:
    downloaded = []
    for source in sorted(cache_dir().glob("*.parquet")):
        if source.name.startswith(("healthregions_2013", "metadata_geobr_v2")):
            shutil.copy2(source, path / source.name)
            if source.name.startswith("healthregions_2013"):
                downloaded.append({"file": source.name, "sha256": _sha(source)})
    metadata = path / "metadata_geobr_v2.parquet"
    if metadata.exists():
        catalog = pd.read_parquet(metadata).set_index("file_name")
        for item in downloaded:
            item["catalog_url"] = str(catalog.loc[item["file"], "download_url"])
    manifest["source"]["downloads"] = downloaded
    manifest["source"]["download_endpoint_observed"] = False
    manifest["source"]["mirror_note"] = (
        "geobr may use its IPEA mirror for the same asset; endpoint is not exposed"
    )


def main(argv: list[str] | None = None) -> int:
    """Acquire one explicit source; preserve diagnostics and exit 2 on failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    values = tomllib.loads(parser.parse_args(argv).config.read_text())
    cfg = GraphConfig(**values)
    run_path = cfg.output_dir / cfg.run_id
    if run_path.exists() or cfg.processed_dir.exists():
        raise FileExistsError(
            "run or processed directory already exists; choose new paths"
        )
    run_path.mkdir(parents=True)
    cfg.processed_dir.mkdir(parents=True)
    start, usage = time.perf_counter(), resource.getrusage(resource.RUSAGE_SELF)
    git = ["git", "-C", str(Path(__file__).resolve().parent)]
    manifest = {
        "config": {
            k: str(v) if isinstance(v, Path) else v for k, v in asdict(cfg).items()
        },
        "contiguity": "queen",
        "placebo_budget": SWAP_BUDGET,
        "code_sha256": {
            p.name: _sha(p)
            for p in (Path(__file__), Path(__file__).with_name("graph.py"))
        },
        "dependencies": {
            name: version(name)
            for name in (
                "geobr",
                "geopandas",
                "libpysal",
                "shapely",
                "networkx",
                "duckdb",
            )
        },
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "git_sha": subprocess.check_output(
            [*git, "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()
        ),
        "seed": {"entropy": cfg.root_seed, "spawn_key": []},
        "names": list(hierarchy().leaves),
        "status": "blocked",
        "interpretation_allowed": False,
        "source": {
            "provider": "DataSUS via geobr",
            "url": "https://github.com/ipea/geobr",
            "year": cfg.year,
            "simplified": cfg.simplified,
            "geometry_level": "micro",
            "code_state": "PA",
            "geobr_version": version("geobr"),
            "reader_sha256": _sha(GEOBR_SOURCE),
            "upstream_processing": "municipality union; exterior rings only; union again (holes removed)",
            "local_geometry_repairs": [],
        },
    }
    try:
        regions = geobr.read_health_region(
            year=cfg.year,
            code_state="PA",
            geometry_level="micro",
            simplified=cfg.simplified,
            show_progress=False,
        )
        regions.to_parquet(cfg.processed_dir / "source_regions.parquet", index=False)
        manifest["source"]["returned_rows"] = len(regions)
        manifest["source"]["crs"] = str(regions.crs)
        manifest["source"]["invalid_geometries"] = int(
            (~regions.geometry.is_valid).sum()
        )
        manifest["source"]["empty_geometries"] = int(regions.geometry.is_empty.sum())
        if (
            "name_health_region" in regions
            and not regions.geometry.isna().any()
            and not regions.geometry.is_empty.any()
            and regions.geometry.is_valid.all()
        ):
            _map(
                regions.rename(columns={"name_health_region": "name"}),
                cfg.processed_dir / "source_map.png",
            )
        regions = _canonical_regions(regions, manifest)
        _artifacts(regions, cfg, manifest)
        manifest["status"] = "ready"
    except Exception as exc:  # noqa: BLE001 - CLI must preserve acquisition diagnostics.
        manifest["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            _preserve_sources(cfg.processed_dir, manifest)
        except Exception as exc:  # noqa: BLE001 - retain the primary failure as well.
            manifest["status"] = "blocked"
            manifest["source_cache_error"] = f"{type(exc).__name__}: {exc}"
        manifest["artifact_sha256"] = {
            str(p.relative_to(cfg.processed_dir)): _sha(p)
            for p in sorted(cfg.processed_dir.iterdir())
            if p.is_file()
        }
        now = resource.getrusage(resource.RUSAGE_SELF)
        manifest["cost"] = {
            "elapsed_seconds": time.perf_counter() - start,
            "user_cpu_seconds": now.ru_utime - usage.ru_utime,
            "system_cpu_seconds": now.ru_stime - usage.ru_stime,
            "peak_rss_kib": now.ru_maxrss,
            "artifact_bytes": sum(
                p.stat().st_size for p in cfg.processed_dir.iterdir() if p.is_file()
            ),
        }
        text = json.dumps(manifest, indent=2, allow_nan=False) + "\n"
        (cfg.processed_dir / "manifest.json").write_text(text)
        (run_path / "manifest.json").write_text(text)
    print(
        f"P4 {manifest['status']}: {run_path}; scientific interpretation remains gated."
    )
    return 0 if manifest["status"] == "ready" else 2
