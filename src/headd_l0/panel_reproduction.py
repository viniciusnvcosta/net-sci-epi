"""Reproduce the regional count panel from the supplied integrated dataset."""

import argparse
import hashlib
import json
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0._sim_validation_io import _publish, _sha256
from headd_l0.data import MONTHS, hierarchy, load_sivep

INTEGRATED_SHA256 = "0a82aaecb02c5854149e22235a9e460abd82780d824c54ae5bd0fbd17902d05e"


def canonical_panel(groups: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Build canonical positive and total counts, rejecting missing cells."""
    frame = groups.copy()
    if frame[["region", "month", "species", "count"]].isna().any().any():
        raise ValueError("missing values")
    frame["month"] = pd.to_datetime(frame["month"])
    if (
        not frame.region.isin(hierarchy().leaves).all()
        or not frame.month.isin(MONTHS).all()
    ):
        raise ValueError("unknown region or month")
    if (frame["count"] < 0).any() or not (frame["count"] % 1 == 0).all():
        raise ValueError("invalid counts")
    grid = pd.MultiIndex.from_product(
        [hierarchy().leaves, MONTHS], names=["region", "month"]
    )
    total = frame.groupby(["region", "month"])["count"].sum().reindex(grid)
    if total.isna().any():
        raise ValueError("missing region-month")
    positive = (
        frame[frame.species != "negative"]
        .groupby(["region", "month"])["count"]
        .sum()
        .reindex(grid, fill_value=0)
    )
    return tuple(
        np.ascontiguousarray(x.to_numpy(dtype="<i8").reshape(13, 132))
        for x in (positive, total)
    )


def panel_hash(panel: tuple[np.ndarray, np.ndarray]) -> str:
    """Hash canonical labels, months and two little-endian count arrays."""
    digest = hashlib.sha256(
        json.dumps(
            {
                "shape": [13, 132],
                "names": hierarchy().leaves,
                "months": [str(x.date()) for x in MONTHS],
            },
            sort_keys=True,
        ).encode()
    )
    for value in panel:
        if value.shape != (13, 132):
            raise ValueError("invalid panel shape")
        digest.update(np.ascontiguousarray(value, dtype="<i8").tobytes())
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    """Aggregate verified data and publish the panel comparison without replacement."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("integrated", type=Path)
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        raise FileExistsError(args.output)
    if _sha256(args.integrated) != INTEGRATED_SHA256:
        raise ValueError("integrated source hash mismatch")
    before = args.integrated.stat()
    cols = [
        "notification.year",
        "notification.month",
        "notification.hr",
        "exam.result",
        "notification.state",
    ]
    counts = Counter()
    for chunk in pd.read_csv(
        args.integrated, sep="\t", usecols=cols, dtype=str, chunksize=200000
    ):
        frame = chunk[chunk["notification.state"] == "PA"]
        if frame[cols].isna().any().any():
            raise ValueError("missing PA values")
        counts.update(frame.groupby(cols[:-1], dropna=False).size().to_dict())
    after = args.integrated.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ValueError("integrated source changed during read")
    rows = []
    for (year, month, region, species), count in counts.items():
        rows.append(
            {
                "region": region,
                "month": pd.Timestamp(int(year), int(month), 1),
                "species": species,
                "count": count,
            }
        )
    result = canonical_panel(pd.DataFrame(rows))
    original = load_sivep(args.raw_dir)
    reference = (original.counts, original.tests)
    report = {
        "status": "comparison",
        "interpretation_allowed": False,
        "integrated_sha256": INTEGRATED_SHA256,
        "reference_sha256": {
            name: _sha256(args.raw_dir / name)
            for name in ("PA.csv", "PASIVEPDailyPerHr.csv")
        },
        "canonical_hash_integrated": panel_hash(result),
        "canonical_hash_reference": panel_hash(reference),
        "positive_equal": bool(np.array_equal(result[0], reference[0])),
        "tests_equal": bool(np.array_equal(result[1], reference[1])),
        "positive_differing_cells": int(np.count_nonzero(result[0] != reference[0])),
        "tests_differing_cells": int(np.count_nonzero(result[1] != reference[1])),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(
        tempfile.mkdtemp(prefix=f".{args.output.name}-", dir=args.output.parent)
    )
    (stage / "manifest.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    _publish(stage, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
