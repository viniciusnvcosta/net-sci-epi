"""E1 artifact reduction: independent-null FAR and censored paired timing."""

import hashlib
import json
import subprocess
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
from pyarrow.parquet import ParquetWriter

from headd_l0.data import hierarchy
from headd_l0.e1 import _seed_record
from headd_l0.evaluate import detection_outcome
from headd_l0.select import SelectionConfig
from headd_l0.simulate import _MONTHLY, SimConfig
from headd_l0.threshold import calibration_report, check_far


def _write_scores(path, records, scores, arms):
    names = hierarchy().leaves
    with ParquetWriter(
        path / "scores.parquet",
        pa.schema(
            [
                ("replicate_id", pa.string()),
                ("noise", pa.string()),
                ("epsilon", pa.float64()),
                ("partition", pa.string()),
                ("label", pa.string()),
                ("arm", pa.string()),
                ("task", pa.string()),
                ("month", pa.int64()),
                ("score", pa.float64()),
            ]
        ),
    ) as writer:
        for record, values in zip(records, scores, strict=True):
            frame = pd.DataFrame(
                {
                    **{
                        key: record[key]
                        for key in (
                            "replicate_id",
                            "noise",
                            "epsilon",
                            "partition",
                            "label",
                        )
                    },
                    "arm": np.repeat([arm.name for arm in arms], 13 * 72),
                    "task": np.tile(np.repeat(names, 72), len(arms)),
                    "month": np.tile(np.arange(60, 132), len(arms) * 13),
                    "score": values.ravel(),
                }
            )
            writer.write_table(
                pa.Table.from_pandas(frame, schema=writer.schema, preserve_index=False)
            )


def _far(cfg, records, scores, arms):
    rows = []
    for (noise, epsilon), group in records.groupby(["noise", "epsilon"], sort=True):
        calibration = group.index[group.partition == "calibration"]
        evaluation = group.index[
            (group.partition == "evaluation") & (group.label == "N")
        ]
        for a, arm in enumerate(arms):
            for j, task in enumerate(hierarchy().leaves):
                cal = np.asarray([scores[i][a, j] for i in calibration]).ravel()
                ev = np.asarray([scores[i][a, j] for i in evaluation]).ravel()
                complete = bool(np.isfinite(cal).all() and np.isfinite(ev).all())
                cal, ev = cal[np.isfinite(cal)], ev[np.isfinite(ev)]
                row = {
                    "noise": noise,
                    "epsilon": epsilon,
                    "arm": arm.name,
                    "task": task,
                    "target_far": cfg.target_far,
                    "tolerance": cfg.far_tolerance,
                    "calibration_n": len(cal),
                    "n": len(ev),
                    "complete": complete,
                    "calibration_expected_n": cfg.n_calibration * 72,
                    "evaluation_expected_n": cfg.n_null * 72,
                    "threshold": None,
                    "achieved_far": None,
                    "observed_far": None,
                    "method": "unavailable_forecast",
                    "passed": False,
                    "alarms": None,
                }
                if len(cal):
                    fit = calibration_report(cal, cfg.target_far)
                    row.update({k: v for k, v in asdict(fit).items() if k != "n"})
                    if len(ev):
                        row.update(
                            asdict(
                                check_far(
                                    ev > fit.threshold,
                                    cfg.target_far,
                                    cfg.far_tolerance,
                                )
                            )
                        )
                        row["passed"] &= complete
                rows.append(row)
    return pd.DataFrame(rows)


def _outcomes(cfg, records, scores, onsets, arms, far):
    rows, comparisons = [], []
    lookup = far.set_index(["noise", "epsilon", "arm", "task"])
    for i, record in records.iterrows():
        if record.partition != "evaluation":
            continue
        common = {
            key: record[key] for key in ("replicate_id", "noise", "epsilon", "label")
        }
        for j, task in enumerate(hierarchy().leaves):
            paired = {}
            for a, arm in enumerate(arms):
                gate = lookup.loc[record.noise, record.epsilon, arm.name, task]
                eligible = bool(record.fit_valid and pd.notna(gate.threshold))
                alarms = np.zeros(132, dtype=bool)
                if eligible:
                    alarms[60:] = scores[i][a, j] > gate.threshold
                timing = asdict(
                    detection_outcome(alarms, int(onsets[i][j]), cfg.window, cfg.window)
                )
                if not eligible:
                    timing.update(
                        detected=False,
                        first_alarm=None,
                        delay=None,
                        lead=None,
                        restricted_lead=None,
                        censored=False,
                    )
                row = {
                    **common,
                    "task": task,
                    "arm": arm.name,
                    **timing,
                    "fit_valid": bool(record.fit_valid),
                    "score_available": bool(record.fit_valid),
                    "alarm_available": eligible,
                    "timing_denominator": int(onsets[i][j] >= 0),
                    "eligible_months": 72,
                    "far_passed": bool(gate.passed),
                    "interpretation_allowed": False,
                }
                rows.append(row)
                paired[arm.name] = row
            if record.label == "T":
                observed = paired["B2"]
                for arm in arms:
                    if arm.name == "B2":
                        continue
                    reference = paired[arm.name]
                    comparable = observed["far_passed"] and reference["far_passed"]
                    defined = all(
                        row["restricted_lead"] is not None
                        for row in (observed, reference)
                    )
                    comparisons.append(
                        {
                            **common,
                            "task": task,
                            "arm": "B2",
                            "reference": arm.name,
                            "onset": int(onsets[i][j]),
                            "paired_eligible": defined,
                            "restricted_lead_gain": observed["restricted_lead"]
                            - reference["restricted_lead"]
                            if defined
                            else None,
                            "far_comparable": comparable,
                            "interpretation_allowed": False,
                            "blocked_reason": "E0_star_failed;G4_pending"
                            + ("" if comparable else ";FAR")
                            + ("" if record.fit_valid else ";D5"),
                        }
                    )
    return pd.DataFrame(rows), pd.DataFrame(comparisons)


def _artifacts(path, cfg, records, scores, shared, arms, graphs):
    _write_scores(path, records, scores, arms)
    records = pd.DataFrame(records)
    records.to_parquet(path / "replicates.parquet", index=False)
    np.savez(
        path / "shared.npz", **{key: np.stack(values) for key, values in shared.items()}
    )
    np.savez(path / "graphs.npz", **graphs)
    far = _far(cfg, records, scores, arms)
    metrics, comparisons = _outcomes(cfg, records, scores, shared["onset"], arms, far)
    for name, table in (
        ("far", far),
        ("metrics", metrics),
        ("comparisons", comparisons),
    ):
        table.to_parquet(path / f"{name}.parquet", index=False)
    return metrics, far


def _manifest(cfg, streams, arms, reference_sha):
    config = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in asdict(cfg).items()
    }
    deterministic_config = {
        key: value
        for key, value in config.items()
        if key not in ("run_id", "output_dir")
    }
    root = Path(__file__).resolve().parents[2]
    git = ["git", "-C", str(root)]
    return {
        "config": config,
        "config_sha256": hashlib.sha256(
            json.dumps(deterministic_config, sort_keys=True).encode()
        ).hexdigest(),
        "git_sha": subprocess.check_output(
            [*git, "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()
        ),
        "timestamp": datetime.now(UTC).isoformat(),
        "reference_sha": reference_sha,
        "versions": {
            name: version(name)
            for name in (
                "numpy",
                "pandas",
                "scipy",
                "scikit-learn",
                "pyod",
                "river",
                "pyarrow",
                "statsmodels",
            )
        },
        "source_sha256": {
            str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((root / "src/headd_l0").glob("*.py"))
        },
        "seeds": {name: _seed_record(seed) for name, seed in streams.items()},
        "seed_addresses": "stream/canonical_noise_epsilon_cell/label/index; detector: stream/cell/partition/label/index/region/canonical_detector",
        "simulation_profile": {"config": asdict(SimConfig()), "monthly": _MONTHLY},
        "graph_source": cfg.graph_source,
        "endemic_source": cfg.endemic_source,
        "arms": [asdict(arm) for arm in arms],
        "settings": {
            "detectors": cfg.detectors,
            "selection": asdict(SelectionConfig(window=cfg.window, k=cfg.selection_k)),
            "reconciliation": cfg.reconciliation,
            "threshold": cfg.threshold,
            "training_months": [11, 59],
            "evaluation_months": [60, 131],
            "shared_forecast_and_mint": True,
            "selection_reset_each_replicate": True,
        },
        "nondeterministic_fields": [
            "timestamp",
            "config.run_id",
            "config.output_dir",
            "git_dirty",
        ],
        "gates": {
            "E0": {"status": "inconclusive"},
            "E0_star": {"status": "failed", "source": "e0-star-scoring-20260930"},
            "G4": {"status": "pending"},
            "scientific_ratification": {"status": "pending"},
        },
        "interpretation_allowed": False,
        "status": "running",
    }
