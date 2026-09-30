"""Approved E0* scoring and NB2 null artifacts; no substitute D5 forecaster."""

import hashlib
import json
import subprocess
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0.data import hierarchy
from headd_l0.detectors import DETECTORS, DetectorConfig, rolling_zscore
from headd_l0.evaluate import auc_pr
from headd_l0.features import local_features
from headd_l0.forecast import NB2Fit, fit_nb2, forecast_mean, sample_nb2
from headd_l0.reconcile import (
    fit_mint,
    reconciled_residuals,
    standardize,
    summing_matrix,
)
from headd_l0.run import check_e0_star, run_preflight
from headd_l0.select import SelectionConfig, select_stream
from headd_l0.threshold import calibration_report

DECISION_SHA = "50f8b3f29bacc4747329addf80cee6719fe3c7fc"


def _null_panels(fit, counts, seed, n):
    leaves_fit = NB2Fit(fit.coefficients[1:], fit.alpha[1:], fit.converged[1:], 60)
    panels = np.broadcast_to(counts, (n, *counts.shape)).astype(np.int64).copy()
    panels[:, 1:, 60:] = sample_nb2(
        leaves_fit, np.arange(60, 132), n, np.random.default_rng(seed)
    )
    panels[:, 0] = panels[:, 1:].sum(axis=1)
    return panels


def _source_identity():
    root = Path(__file__).resolve().parents[2]
    sources = [
        *sorted((root / "src/headd_l0").glob("*.py")),
        *sorted((root / "tests").glob("test_*.py")),
        root / "pyproject.toml",
        root / "uv.lock",
    ]
    return hashlib.sha256(
        b"".join(
            p.relative_to(root).as_posix().encode() + p.read_bytes() for p in sources
        )
    ).hexdigest()


def _component_evidence(path):
    root = Path(__file__).resolve().parents[2]
    before = _source_identity()
    command = [
        sys.executable,
        "-m",
        "pytest",
        "-o",
        "addopts=",
        "-q",
        *[
            f"tests/test_{name}.py"
            for name in (
                "forecast",
                "reconcile",
                "features",
                "detectors",
                "select",
                "threshold",
                "evaluate",
                "stats",
            )
        ],
    ]
    with (path / "components.log").open("w") as log:
        result = subprocess.run(
            command, cwd=root, stdout=log, stderr=subprocess.STDOUT, check=False
        )
    return {
        "command": command,
        "cwd": str(root),
        "exit_code": result.returncode,
        "timestamp": datetime.now(UTC).isoformat(),
        "git_sha": subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
        ).strip(),
        "source_sha256": before,
        "passed": result.returncode == 0 and before == _source_identity(),
    }


def _score_panels(panels, fitted, mint, pools):
    scores = np.empty((len(panels), 2, 14, 72))
    S = summing_matrix(hierarchy())
    for i, panel in enumerate(panels):
        features = local_features(
            standardize(reconciled_residuals(panel, fitted, S, mint))
        ).values
        for j, pool in enumerate(pools):
            raw = np.column_stack(
                [detector.score(features[j, 1:]) for detector in pool]
            )
            scores[i, 0, j] = select_stream(raw, 59, SelectionConfig()).scores[59:]
        scores[i, 1] = rolling_zscore(panel, window=12)[:, 60:]
        if (i + 1) % 10 == 0:
            print(f"Scored {i + 1}/{len(panels)} null panels", flush=True)
    return scores


def _calibrate_scores(calibration, evaluation, names):
    rows = []
    for arm_index, arm in enumerate(("B1*", "zscore")):
        for j, name in enumerate(names):
            report = calibration_report(calibration[:, arm_index, j].ravel(), 1 / 60)
            far = float(np.mean(evaluation[:, arm_index, j] > report.threshold))
            rows.append(
                {
                    "task": name,
                    "arm": arm,
                    **asdict(report),
                    "observed_far": far,
                    "tolerance": 1 / 300,
                    "passed": abs(far - 1 / 60) <= 1 / 300,
                    "null_model": "nb2",
                    "fit_valid": True,
                    "fallback_used": False,
                }
            )
    return pd.DataFrame(rows)


def _score_e0(cfg, leaves, n=200):
    git = ["git", "-C", str(Path(__file__).resolve().parent)]
    decision = subprocess.run(
        [*git, "merge-base", "--is-ancestor", DECISION_SHA, "HEAD"],
        capture_output=True,
        check=False,
    )
    if decision.returncode:
        raise ValueError("regional E0* decision must precede scoring")
    path = run_preflight(cfg, leaves)
    manifest = json.loads((path / "manifest.json").read_text())
    manifest.update(
        status="running",
        fallback_status="pending_specification_not_used",
        task6_complete=False,
    )

    def save():
        (path / "manifest.json").write_text(
            json.dumps(manifest, indent=2, allow_nan=False) + "\n"
        )

    save()
    try:
        names = ("PA", *hierarchy().leaves)
        counts = np.vstack((leaves.sum(axis=0), leaves))
        fit = fit_nb2(counts)
        fitted = forecast_mean(fit, np.arange(132))
        valid = (
            fit.converged
            & np.isfinite(fit.coefficients).all(axis=1)
            & np.isfinite(fit.alpha)
            & (fit.alpha > 0)
            & np.isfinite(fitted).all(axis=1)
            & (fitted > 0).all(axis=1)
        )
        fits = pd.DataFrame(
            {
                "task": names,
                "converged": fit.converged,
                "valid": valid,
                "alpha": fit.alpha,
                "train_start": 0,
                "train_end": 59,
                "fallback_used": False,
                "fallback_status": np.where(
                    valid, "not_needed", "pending_specification"
                ),
            }
        )
        fits.to_parquet(path / "fits.parquet", index=False)
        np.savez_compressed(
            path / "forecast.npz",
            coefficients=fit.coefficients,
            alpha=fit.alpha,
            converged=fit.converged,
            means=fitted,
        )
        manifest["fits"] = fits.drop(columns="alpha").to_dict("records")
        if not valid.all():
            manifest.update(
                status="failed",
                failure_reason="D5_forecast_unavailable",
                failed_fits=[
                    name for name, ok in zip(names, valid, strict=True) if not ok
                ],
                fallback_status="pending_specification",
            )
            manifest["gates"]["E0_star"] = {
                "status": "failed",
                "reasons": ["D5_forecast_unavailable"],
                "components": "not_evaluated",
                "trivial_baseline": "not_evaluated",
            }
            save()
            return path
        streams = dict(
            zip(
                ("calibration", "evaluation", "detectors", "bootstrap"),
                np.random.SeedSequence(cfg.root_seed).spawn(4),
                strict=True,
            )
        )
        manifest["streams"] = {
            name: {"entropy": seed.entropy, "spawn_key": list(seed.spawn_key)}
            for name, seed in streams.items()
        }
        manifest["settings"] = {
            "detector": {
                "contamination": DetectorConfig(seed=0).contamination,
                "seeds_artifact": "detector_fits.parquet",
            },
            "selector": asdict(SelectionConfig()),
            "detector_names": list(DETECTORS),
            "features": "local",
            "reconciler": "mint_shrink",
            "threshold": "evt_gpd",
            "training_months": [1, 59],
            "evaluation_months": [60, 131],
            "zscore_window": 12,
            "null_panels_per_partition": n,
            "shared_training": True,
            "selection_reset_each_panel": True,
        }
        partitions = {}
        ids = []
        for partition in ("calibration", "evaluation"):
            seeds = streams[partition].spawn(n)
            partitions[partition] = np.concatenate(
                [_null_panels(fit, counts, seed, 1) for seed in seeds]
            )
            for i, seed in enumerate(seeds):
                ids.append(
                    {
                        "panel_id": f"{partition}:{i:03d}",
                        "partition": partition,
                        "entropy": seed.entropy,
                        "spawn_key": list(seed.spawn_key),
                        "model": "nb2",
                        "all_fits_valid": True,
                        "fallback_used": False,
                    }
                )
            np.savez_compressed(
                path / f"null_{partition}.npz",
                counts=partitions[partition][:, 1:],
                aggregate=partitions[partition][:, 0],
                all_fits_valid=True,
                fallback_used=False,
            )
        pd.DataFrame(ids).to_parquet(path / "null_partitions.parquet", index=False)
        print("NB2 converged; null partitions saved; checking components", flush=True)
        evidence = _component_evidence(path)
        manifest["component_evidence"] = evidence
        save()
        if (
            not evidence["passed"]
            or evidence.get("source_sha256") != _source_identity()
        ):
            raise ValueError("component evidence failed or changed during verification")
        mint = fit_mint(counts, fitted)
        features = local_features(
            standardize(
                reconciled_residuals(counts, fitted, summing_matrix(hierarchy()), mint)
            )
        ).values
        pools, detector_records = [], []
        for j, seed in enumerate(streams["detectors"].spawn(14)):
            pool = []
            for (name, factory), child in zip(
                DETECTORS.items(), seed.spawn(len(DETECTORS)), strict=True
            ):
                config = DetectorConfig(seed=int(child.generate_state(1)[0]))
                pool.append(factory(config).fit(features[j, 1:60]))
                detector_records.append(
                    {
                        "task": names[j],
                        "detector": name,
                        **asdict(config),
                        "entropy": child.entropy,
                        "spawn_key": list(child.spawn_key),
                    }
                )
            pools.append(pool)
        pd.DataFrame(detector_records).to_parquet(
            path / "detector_fits.parquet", index=False
        )
        np.savez_compressed(
            path / "mint.npz", covariance=mint.covariance, shrinkage=mint.shrinkage
        )
        null_scores = {}
        for partition, panels in partitions.items():
            print(f"Scoring {partition} partition", flush=True)
            null_scores[partition] = _score_panels(panels, fitted, mint, pools)
            np.savez_compressed(
                path / f"scores_{partition}.npz",
                scores=null_scores[partition],
                arms=np.array(["B1*", "zscore"]),
                tasks=np.array(names),
                all_fits_valid=True,
                fallback_used=False,
            )
        far = _calibrate_scores(
            null_scores["calibration"][:, :, 1:],
            null_scores["evaluation"][:, :, 1:],
            names[1:],
        )
        far.to_parquet(path / "far.parquet", index=False)
        injection = np.load(path / "injection.npz")
        scores = _score_panels(injection["counts"][None], fitted, mint, pools)[0]
        np.savez_compressed(
            path / "scores_injected.npz",
            scores=scores,
            arms=np.array(["B1*", "zscore"]),
            tasks=np.array(names),
            all_fits_valid=True,
            fallback_used=False,
        )
        rows = []
        for a, arm in enumerate(("B1*", "zscore")):
            for j, name in enumerate(names):
                labels = injection["mask"][j, 60:]
                both = labels.any() and not labels.all()
                rows.append(
                    {
                        "task": name,
                        "arm": arm,
                        "auc_pr": auc_pr(labels, scores[a, j]) if both else None,
                        "ap_status": "defined" if both else "single_class",
                        "n_positive": int(labels.sum()),
                        "n_negative": int((~labels).sum()),
                        "prevalence": float(labels.mean()),
                        "window_start": 60,
                        "window_end": 131,
                        "in_gate": j > 0,
                        "fit_valid": True,
                        "fallback_used": False,
                        "null_model": "nb2",
                    }
                )
        metrics = pd.DataFrame(rows)
        metrics.to_parquet(path / "metrics.parquet", index=False)
        if evidence.get("source_sha256") != _source_identity():
            raise ValueError("component evidence became stale during scoring")
        gate = check_e0_star(
            evidence["passed"], metrics, np.random.default_rng(streams["bootstrap"])
        )
        manifest["gates"]["E0_star"] = {
            "status": "passed" if gate.passed else "failed",
            **asdict(gate),
        }
        manifest["gates"]["FAR"] = {
            "status": "passed" if far.passed.all() else "failed",
            "failed_pairs": far.loc[~far.passed, ["task", "arm"]].to_dict("records"),
            "target": 1 / 60,
            "tolerance": 1 / 300,
        }
        manifest["status"] = "completed"
        save()
    except Exception as exc:
        manifest.update(status="failed", failure_reason=f"{type(exc).__name__}: {exc}")
        manifest["gates"]["E0_star"]["status"] = "failed"
        save()
        raise
    return path
