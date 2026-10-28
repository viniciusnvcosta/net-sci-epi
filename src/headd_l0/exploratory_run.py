"""Run an independently identified, strictly exploratory SIR demonstration."""

import json
import resource
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0._sim_validation_io import _publish, _sha256
from headd_l0.data import hierarchy
from headd_l0.exploratory import (
    evaluate_far,
    evaluate_timings,
    load_graphs,
    load_hazards,
    measure_pilot,
    score_replicate,
    simulate_replicate,
)


def _source_identity() -> dict[str, str]:
    return {p.name: _sha256(p) for p in sorted(Path(__file__).parent.glob("*.py"))}


def _verify_budget(path: Path) -> dict:
    """Require a committed cost-based budget with a verified pilot manifest."""
    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    relative = path.resolve().relative_to(root)
    saved = subprocess.run(
        ["git", "show", f"HEAD:{relative.as_posix()}"], check=True, capture_output=True
    ).stdout
    if saved != path.read_bytes():
        raise ValueError("budget must match committed bytes")
    budget = json.loads(saved)
    pilot = Path(budget["pilot_manifest"])
    if _sha256(pilot) != budget["pilot_manifest_sha256"]:
        raise ValueError("pilot manifest hash mismatch")
    if json.loads(pilot.read_text()).get("status") != "pilot_complete":
        raise ValueError("pilot not complete")
    if (
        type(budget["n_transition"]) is not int
        or budget["n_transition"] < 1
        or budget["placebo_ids"] not in ([0], [0, 1], [0, 1, 2])
    ):
        raise ValueError("unsupported exploratory budget")
    return budget


def run_experiment(
    manifest_path: Path, calibration_dir: Path, budget_path: Path, output: Path
) -> None:
    """Run paired T/N cells and publish descriptive results without replacement."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    source_identity = _source_identity()
    budget = _verify_budget(budget_path)
    a, w, p4, placebo = load_graphs(manifest_path)
    hazards = load_hazards(calibration_dir)
    graphs = {
        "observed": a,
        "p4": p4,
        **{f"placebo-{i:02d}": placebo[i] for i in range(3)},
    }
    results, far_rows, timing_rows = {}, [], []
    for cell, epsilon in enumerate((0.0, 0.2)):
        scores = {}
        onsets = []
        for partition, label, n in [
            ("calibration", "N", 200),
            ("evaluation", "N", 200),
            ("evaluation", "T", budget["n_transition"]),
        ]:
            values = []
            for index in range(n):
                simulation = simulate_replicate(
                    w, epsilon, label, partition, index, hazards
                )
                address = (
                    3,
                    ("pilot", "calibration", "evaluation").index(partition),
                    cell,
                    ("T", "N").index(label),
                    index,
                )
                seed = np.random.SeedSequence(20261028, spawn_key=address)
                values.append(
                    score_replicate(
                        simulation.counts, graphs, seed, len(budget["placebo_ids"])
                    )
                )
                if label == "T":
                    onsets.append(simulation.onset)
            scores[f"{partition}_{label}"] = np.stack(values)
        far = evaluate_far(
            scores["calibration_N"],
            scores["evaluation_N"],
            range(200),
            range(1000, 1200),
        )
        timing = evaluate_timings(scores["evaluation_T"], np.stack(onsets), far)
        far_rows.extend({"epsilon": epsilon, **row} for row in far)
        timing_rows.extend({"epsilon": epsilon, **row} for row in timing)
        for key, value in scores.items():
            results[f"epsilon_{cell}_{key}"] = value
        results[f"epsilon_{cell}_onsets"] = np.stack(onsets)
    if _source_identity() != source_identity:
        raise ValueError("source changed during experiment")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    pd.DataFrame(far_rows).to_csv(stage / "far.csv", index=False)
    pd.DataFrame(timing_rows).to_csv(stage / "timings.csv", index=False)
    np.savez_compressed(stage / "scores.npz", **results)
    record = {
        "status": "exploratory",
        "interpretation_allowed": False,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "root_seed": 20261028,
        "region_names": list(hierarchy().leaves),
        "arm_names": [
            "B1*",
            "B2",
            "B2-P4",
            *[f"B2-placebo-{i:02d}" for i in budget["placebo_ids"]],
            "zscore",
        ],
        "seed_addresses": "simulation=(partition,epsilon,label,index); detector=(3,partition,epsilon,label,index); children 0=region,1=simulation",
        "source_sha256": {
            p.name: _sha256(p) for p in Path(__file__).parent.glob("*.py")
        },
        "candidate_manifest_sha256": _sha256(manifest_path),
        "endemic_manifest_sha256": _sha256(calibration_dir / "manifest.json"),
        "budget_sha256": _sha256(budget_path),
        "n_calibration": 200,
        "n_null_evaluation": 200,
        "n_transition": budget["n_transition"],
        "placebo_ids": budget["placebo_ids"],
        "outputs": {p.name: _sha256(p) for p in stage.iterdir()},
    }
    (stage / "manifest.json").write_text(
        json.dumps(record, indent=2, sort_keys=True) + "\n"
    )
    _publish(stage, output)


def run_pilot(manifest_path: Path, calibration_dir: Path, output: Path) -> None:
    """Publish pilot timing or a failure while retaining blocked interpretation."""
    if output.exists() or output.is_symlink():
        raise FileExistsError(output)
    source_identity = _source_identity()
    a, w, p4, placebo = load_graphs(manifest_path)
    hazards = load_hazards(calibration_dir)
    graphs = {
        "observed": a,
        "p4": p4,
        **{f"placebo-{i:02d}": placebo[i] for i in range(3)},
    }
    try:
        records = measure_pilot(w, graphs, hazards)
        status, error = "pilot_complete", None
    except (ValueError, RuntimeError, ArithmeticError) as exc:
        records, status, error = [], "pilot_failed", str(exc)
    if _source_identity() != source_identity:
        raise ValueError("source changed during pilot")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    projection = None
    if status == "pilot_complete":
        simulation = max(row["simulation_seconds"] for row in records)
        b1 = max(row["arm_seconds"]["B1*"] for row in records)
        b2 = max(row["arm_seconds"]["B2"] for row in records)
        placebo_cost = max(
            row["arm_seconds"][f"B2-placebo-{i:02d}"]
            for row in records
            for i in range(3)
        )
        projection = {
            "seconds": 9 * (600 * (simulation + 2 * b1 + b2) + 500 * 30 * placebo_cost),
            "limitation": "extrapolacao de quatro paineis white; B0 aproximado por B1; outros ruidos e epsilon nao medidos; ajustes compartilhados repetidos",
        }
    result = {
        "cost_projection": projection,
        "status": status,
        "error": error,
        "interpretation_allowed": False,
        "records": records,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "candidate_manifest_sha256": _sha256(manifest_path),
        "endemic_manifest_sha256": _sha256(calibration_dir / "manifest.json"),
        "source_sha256": source_identity,
        "root_seed": 20261028,
        "per_arm_timings": "individual measurements include repeated shared fitting",
        "d_cost_status": "pending",
    }
    (stage / "manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    _publish(stage, output)
