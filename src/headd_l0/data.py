# ABOUTME: Loads the SIVEP-Malária Pará CSVs into region × month count arrays and a long table.
# ABOUTME: Fixes the PA → 13 health-region hierarchy and writes derived data with provenance.
"""SIVEP-PA loader, ported from CDADE ``cdade/data/sivep.py`` at fbfa609 (Apache-2.0).

``counts`` sums every ``exam.result`` other than ``negative``, as the original
``prepare_counts`` does; ``tests`` also include negatives. A species absent from
an observed region-month contributes zero, but a missing region-month, region
or month is an error: structural gaps are never filled with zeros.
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

STATE = "PA"
LEAVES: tuple[str, ...] = (
    "ARAGUAIA",
    "BAIXO AMAZONAS",
    "CARAJAS",
    "LAGO DE TUCURUI",
    "MARAJO I",
    "MARAJO II",
    "METROPOLITANA I",
    "METROPOLITANA II",
    "METROPOLITANA III",
    "RIO CAETES",
    "TAPAJOS",
    "TOCANTINS",
    "XINGU",
)
MONTHS = pd.date_range("2009-01-01", "2019-12-01", freq="MS")
NEGATIVE = "negative"
RAW_FILES = ("PA.csv", "PASIVEPDailyPerHr.csv")


@dataclass(frozen=True)
class Hierarchy:
    """Aggregate state over its leaf regions, leaves in canonical order."""

    state: str
    leaves: tuple[str, ...]


@dataclass(frozen=True)
class DataBundle:
    """Loaded SIVEP data; arrays are read-only and indexed ``[region, month]``."""

    long: pd.DataFrame
    counts: np.ndarray
    state_counts: np.ndarray
    tests: np.ndarray
    months: pd.DatetimeIndex
    hierarchy: Hierarchy


@dataclass(frozen=True)
class DataConfig:
    """Paths read from ``configs/data.toml``."""

    raw_dir: Path
    processed_dir: Path
    results_dir: Path


def hierarchy() -> Hierarchy:
    """Return the fixed PA hierarchy."""
    return Hierarchy(STATE, LEAVES)


def _months(frame: pd.DataFrame) -> pd.Series:
    parts = {"year": frame["notification.year"], "month": frame["notification.month"]}
    return pd.to_datetime(pd.DataFrame({**parts, "day": 1}))


def _read_long(raw_dir: Path) -> pd.DataFrame:
    hr = pd.read_csv(raw_dir / "PASIVEPDailyPerHr.csv")
    long = pd.DataFrame(
        {
            "region": hr["notification.hr"],
            "month": _months(hr),
            "species": hr["exam.result"],
            "count": hr["testperhr"].astype(np.int64),
        }
    )
    unknown = sorted(set(long["region"]) - set(LEAVES))
    if unknown:
        raise ValueError(f"unknown regions in PASIVEPDailyPerHr.csv: {unknown}")
    if (long["count"] < 0).any():
        raise ValueError("negative testperhr values in PASIVEPDailyPerHr.csv")
    if not long["month"].isin(MONTHS).all():
        raise ValueError("months outside 2009-01..2019-12 in PASIVEPDailyPerHr.csv")
    return long


def _grid(long: pd.DataFrame) -> np.ndarray:
    """Sum ``count`` into a ``[region, month]`` array over the full observed grid."""
    table = long.groupby(["region", "month"])["count"].sum().unstack("month")
    table = table.reindex(index=list(LEAVES), columns=MONTHS)
    return table.fillna(0).to_numpy(np.int64)


def _read_only(array: np.ndarray) -> np.ndarray:
    array.setflags(write=False)
    return array


def load_sivep(raw_dir: Path) -> DataBundle:
    """Load both SIVEP-PA CSVs from ``raw_dir`` without modifying them.

    Args:
        raw_dir: Directory holding ``PA.csv`` and ``PASIVEPDailyPerHr.csv``.

    Returns:
        The long table, ``counts``/``tests`` ``[13, 132]`` and ``state_counts`` ``[132]``.

    Raises:
        ValueError: On unknown regions, negative counts, a missing region-month,
            region or month, or PA totals that differ from the regional sums.
    """
    raw_dir = Path(raw_dir)
    long = _read_long(raw_dir)
    cells = long.groupby(["region", "month"]).size().unstack("month")
    cells = pd.DataFrame(cells).reindex(index=list(LEAVES), columns=MONTHS)
    gaps = cells.isna().stack(future_stack=True)
    missing = [
        (r, m.strftime("%Y-%m")) for r, m in gaps[gaps.to_numpy(dtype=bool)].index
    ]
    if missing:
        raise ValueError(f"missing region-months ({len(missing)}): {missing[:5]}")
    counts = _grid(long[long["species"] != NEGATIVE])
    tests = _grid(long)
    state = pd.read_csv(raw_dir / "PA.csv")
    if not pd.DatetimeIndex(_months(state)).equals(MONTHS):
        raise ValueError(
            "PA.csv months are missing or out of order for 2009-01..2019-12"
        )
    state_counts = state["positives"].to_numpy(np.int64)
    for label, regional, total in (
        ("positives", counts, state_counts),
        ("totalTests", tests, state["totalTests"].to_numpy(np.int64)),
    ):
        differ = int((regional.sum(axis=0) != total).sum())
        if differ:
            raise ValueError(
                f"PA {label} differ from the regional sum in {differ} months"
            )
    return DataBundle(
        long=long,
        counts=_read_only(counts),
        state_counts=_read_only(state_counts),
        tests=_read_only(tests),
        months=MONTHS,
        hierarchy=hierarchy(),
    )


def prepare(raw_dir: Path, output_dir: Path) -> DataBundle:
    """Load the raw data and write the long table, arrays and provenance.

    Args:
        raw_dir: Raw CSV directory; only read.
        output_dir: Destination for ``long.parquet``, ``*.npy`` and ``provenance.json``.

    Returns:
        The loaded bundle.
    """
    raw_dir, output_dir = Path(raw_dir), Path(output_dir)
    bundle = load_sivep(raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    bundle.long.to_parquet(output_dir / "long.parquet", index=False)
    for name in ("counts", "state_counts", "tests"):
        np.save(output_dir / f"{name}.npy", getattr(bundle, name))
    provenance = {
        "source": "cdade/data/sivep.py at fbfa609bba6cb0b0f2a9e8d73be18022aec319b7",
        "raw_sha256": {
            n: hashlib.sha256((raw_dir / n).read_bytes()).hexdigest() for n in RAW_FILES
        },
        "months": [
            MONTHS[0].strftime("%Y-%m"),
            MONTHS[-1].strftime("%Y-%m"),
            len(MONTHS),
        ],
        "hierarchy": asdict(bundle.hierarchy),
    }
    (output_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return bundle


def load_config(path: Path) -> DataConfig:
    """Read a data TOML file into a :class:`DataConfig`."""
    values = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    return DataConfig(**{key: Path(value) for key, value in values.items()})


def main(argv: list[str] | None = None) -> int:
    """Regenerate processed data and write a run manifest from a TOML config."""
    parser = argparse.ArgumentParser(description="Prepare SIVEP-PA counts.")
    parser.add_argument("config", type=Path)
    cfg = load_config(parser.parse_args(argv).config)
    if not cfg.raw_dir.is_dir():
        raise FileNotFoundError(f"raw_dir does not exist: {cfg.raw_dir}")
    prepare(cfg.raw_dir, cfg.processed_dir)
    provenance = json.loads((cfg.processed_dir / "provenance.json").read_text())
    git = ["git", "-C", str(Path(__file__).parent), "rev-parse", "HEAD"]
    manifest = {
        "config": {key: str(value) for key, value in asdict(cfg).items()},
        "provenance": provenance,
        "git_sha": subprocess.check_output(git, text=True).strip(),
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }
    cfg.results_dir.mkdir(parents=True, exist_ok=True)
    (cfg.results_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
