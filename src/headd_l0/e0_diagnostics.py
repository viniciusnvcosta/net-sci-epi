"""Read-only descriptive audit of the preserved E0* artifact contract."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from headd_l0.data import hierarchy
from headd_l0.threshold import check_far

_PINNED = {
    "manifest.json",
    "metrics.parquet",
    "far.parquet",
    "detector_fits.parquet",
    "pa_diagnostics.json",
}
_ARMS = ["B1*", "zscore"]


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _rows(frame, tasks, arms=None):
    keys = ["task"] if arms is None else ["task", "arm"]
    expected = set(tasks) if arms is None else {(t, a) for t in tasks for a in arms}
    actual = set(frame.task) if arms is None else set(zip(frame.task, frame.arm))
    _require(
        actual == expected and not frame.duplicated(keys).any(),
        f"missing, duplicate or unknown {'/'.join(keys)} rows",
    )


def _arrays(path):
    with np.load(path, allow_pickle=False) as saved:
        return {key: saved[key] for key in saved.files}


def _scores(source, partition, tasks):
    saved = _arrays(source / f"scores_{partition}.npz")
    shape = (2, 14, 72) if partition == "injected" else (200, 2, 14, 72)
    _require(
        saved["tasks"].tolist() == tasks and saved["arms"].tolist() == _ARMS,
        f"invalid {partition} task/arm axes",
    )
    scores = saved["scores"]
    _require(
        scores.shape == shape and np.isfinite(scores).all(),
        f"invalid/nonfinite {partition} scores",
    )
    return scores


def _metrics(frame, tasks):
    _rows(frame, tasks, _ARMS)
    _require(
        ((frame.window_start == 60) & (frame.window_end == 131)).all(),
        "invalid metric window",
    )
    counts = frame[["n_positive", "n_negative"]].to_numpy()
    _require(
        np.isfinite(counts).all()
        and (counts >= 0).all()
        and (counts == np.floor(counts)).all()
        and (counts.sum(axis=1) == 72).all(),
        "invalid metric class counts",
    )
    _require(
        np.allclose(frame.prevalence, frame.n_positive / 72, rtol=0, atol=1e-12),
        "invalid metric prevalence",
    )
    regional = frame[frame.task != "PA"]
    _require(
        (regional.n_positive > 0).all()
        and (regional.n_negative > 0).all()
        and np.isfinite(regional.auc_pr).all()
        and regional.auc_pr.between(0, 1).all()
        and (regional.ap_status == "defined").all(),
        "invalid regional AP",
    )
    result = []
    for task in tasks:
        pair = frame[frame.task == task].set_index("arm")
        _require(
            pair.n_positive.nunique() == pair.n_negative.nunique() == 1,
            f"inconsistent paired labels for {task}",
        )
        if task != "PA":
            b1, zscore = (
                float(pair.loc["B1*", "auc_pr"]),
                float(pair.loc["zscore", "auc_pr"]),
            )
            result.append(
                {
                    "task": task,
                    "b1_ap": b1,
                    "zscore_ap": zscore,
                    "delta_ap": b1 - zscore,
                    "n_positive": int(pair.iloc[0].n_positive),
                    "n_negative": int(pair.iloc[0].n_negative),
                    "denominator": 72,
                    "prevalence": float(pair.iloc[0].prevalence),
                }
            )
    return result


def diagnose_e0(source: Path, evidence: Path) -> dict:
    """Audit saved E0* artifacts without fitting, rewriting, or authorizing inference.

    Args:
        source: Existing historical run directory.
        evidence: JSON evidence pinning identity and five historical artifact hashes.

    Returns:
        A strict-JSON-compatible descriptive report. Completion is not a gate pass.

    Raises:
        ValueError: Evidence or artifact structure does not match the contract.
    """
    pinned = json.loads(evidence.read_text())
    _require(pinned.get("schema_version") == 1, "unsupported evidence schema")
    hashes = pinned.get("artifact_sha256", {})
    _require(set(hashes) == _PINNED, "invalid pinned artifact set")
    observed = {}
    for name in sorted(_PINNED):
        path = source / name
        _require(path.is_file(), f"missing pinned artifact: {name}")
        observed[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        _require(observed[name] == hashes[name], f"changed pinned artifact: {name}")
    manifest = json.loads((source / "manifest.json").read_text())
    identity = {
        "run_id": manifest["config"]["run_id"],
        "git_sha": manifest["git_sha"],
        "reference_sha": manifest["reference_sha"],
        "root_seed": manifest["config"]["root_seed"],
    }
    _require(
        all(identity[key] == pinned[key] for key in identity),
        "run/code/reference/seed identity mismatch",
    )
    _require(manifest["baseline_id"] == "B1*", "unexpected baseline identity")
    tasks = ["PA", *hierarchy().leaves]
    metrics = pd.read_parquet(source / "metrics.parquet")
    regional = _metrics(metrics, tasks)
    injected = _scores(source, "injected", tasks)
    calibration = _scores(source, "calibration", tasks)
    evaluation = _scores(source, "evaluation", tasks)
    injection = _arrays(source / "injection.npz")
    _require(
        injection["mask"].shape == (14, 132)
        and injection["mask"].dtype == np.dtype(bool),
        "invalid injection mask",
    )
    labels = injection["mask"][:, 60:132]
    ap_checks = []
    for j, task in enumerate(tasks):
        for a, arm in enumerate(_ARMS):
            row = metrics[(metrics.task == task) & (metrics.arm == arm)].iloc[0]
            _require(
                int(labels[j].sum()) == row.n_positive,
                f"saved labels differ for {task}/{arm}",
            )
            ap = (
                float(average_precision_score(labels[j], injected[a, j]))
                if labels[j].any() and not labels[j].all()
                else None
            )
            stored = float(row.auc_pr) if np.isfinite(row.auc_pr) else None
            ap_checks.append(
                {
                    "task": task,
                    "arm": arm,
                    "stored_ap": stored,
                    "recomputed_ap": ap,
                    "matches": stored is ap
                    if stored is None or ap is None
                    else bool(np.isclose(stored, ap, rtol=0, atol=1e-12)),
                }
            )
    far_table = pd.read_parquet(source / "far.parquet")
    _rows(far_table, tasks[1:], _ARMS)
    _require(
        np.isfinite(far_table.threshold).all()
        and (far_table.target_far == 1 / 60).all()
        and (far_table.tolerance == 1 / 300).all()
        and (far_table.n == 14400).all(),
        "invalid FAR thresholds, band or denominator",
    )
    far = []
    for task in tasks[1:]:
        for a, arm in enumerate(_ARMS):
            row = far_table[(far_table.task == task) & (far_table.arm == arm)].iloc[0]
            j = tasks.index(task)
            check = check_far(
                (evaluation[:, a, j] > row.threshold).ravel(), 1 / 60, 1 / 300
            )
            achieved = float(np.mean(calibration[:, a, j] > row.threshold))
            far.append(
                {
                    "task": task,
                    "arm": arm,
                    "threshold": float(row.threshold),
                    "target_far": 1 / 60,
                    "tolerance": 1 / 300,
                    "denominator": check.n,
                    "stored_observed_far": float(row.observed_far),
                    "recomputed_far": check.observed_far,
                    "observed_matches": bool(
                        np.isclose(
                            row.observed_far, check.observed_far, rtol=0, atol=1e-12
                        )
                    ),
                    "stored_passed": bool(row.passed),
                    "recomputed_passed": check.passed,
                    "passed_matches": bool(row.passed == check.passed),
                    "stored_achieved_far": float(row.achieved_far),
                    "recomputed_achieved_far": achieved,
                    "achieved_matches": bool(
                        np.isclose(row.achieved_far, achieved, rtol=0, atol=1e-12)
                    ),
                }
            )
    fits = pd.read_parquet(source / "fits.parquet")
    _rows(fits, tasks)
    forecast = _arrays(source / "forecast.npz")
    _require(
        forecast["means"].shape == (14, 132)
        and forecast["coefficients"].shape == (14, 6)
        and forecast["alpha"].shape == forecast["converged"].shape == (14,),
        "invalid forecast axes",
    )
    partitions = pd.read_parquet(source / "null_partitions.parquet")
    _require(
        len(partitions) == 400
        and partitions.panel_id.nunique() == 400
        and partitions.partition.value_counts().to_dict()
        == {"calibration": 200, "evaluation": 200},
        "invalid null partition identities/counts",
    )
    _require(
        (partitions.entropy == identity["root_seed"]).all(),
        "null partition entropy differs from root seed",
    )
    spawn_keys = [tuple(key) for key in partitions.spawn_key]
    _require(len(set(spawn_keys)) == 400, "overlapping null partition spawn keys")
    for partition, stream in (("calibration", 0), ("evaluation", 1)):
        _require(
            all(
                seed[0] == stream
                for seed in partitions.loc[
                    partitions.partition == partition, "spawn_key"
                ]
            ),
            f"invalid {partition} spawn stream",
        )
    auxiliary = [
        "fits.parquet",
        "null_partitions.parquet",
        "forecast.npz",
        "injection.npz",
        "scores_injected.npz",
        "scores_calibration.npz",
        "scores_evaluation.npz",
    ]
    observed.update(
        {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in auxiliary
        }
    )
    report = {
        "schema_version": 1,
        "source": {"path": str(source.resolve()), **identity, "baseline_id": "B1*"},
        "pinned_sha256": hashes,
        "observed_sha256": observed,
        "unpinned_diagnostic_artifacts": auxiliary,
        "regional_ap": regional,
        "mean_delta_ap": float(np.mean([row["delta_ap"] for row in regional])),
        "n_regions_b1_lower": sum(row["delta_ap"] < 0 for row in regional),
        "far": far,
        "fits": {
            "n_rows": len(fits),
            "n_converged": int(fits.converged.sum()),
            "n_valid": int(fits.valid.sum()),
            "n_fallback_used": int(fits.fallback_used.sum()),
        },
        "partitions": {
            "calibration": 200,
            "evaluation": 200,
            "disjoint_ids": True,
            "disjoint_spawn_keys": True,
        },
        "forecast": {
            "means_positive_finite": bool(
                np.isfinite(forecast["means"]).all() and (forecast["means"] > 0).all()
            ),
            "n_converged": int(forecast["converged"].sum()),
            "coefficients_finite": bool(np.isfinite(forecast["coefficients"]).all()),
            "alpha_positive_finite": bool(
                np.isfinite(forecast["alpha"]).all() and (forecast["alpha"] > 0).all()
            ),
        },
        "score_checks": {
            "finite": True,
            "regional_ap": [row for row in ap_checks if row["task"] != "PA"],
            "pa_ap": [row for row in ap_checks if row["task"] == "PA"],
            "ap_disagreements": [row for row in ap_checks if not row["matches"]],
        },
        "historical_gates": manifest["gates"],
        "interpretation_allowed": False,
    }
    # This also rejects nonfinite stored descriptive values not covered above.
    json.dumps(report, allow_nan=False)
    return report


def main() -> int:
    """Print strict JSON on diagnostic completion, or a reason on stderr."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = diagnose_e0(args.source, args.evidence)
        output = json.dumps(report, allow_nan=False, indent=2)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        print(f"E0 diagnostic failed: {error}", file=sys.stderr)
        return 1
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
