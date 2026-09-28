# ABOUTME: Shared stage log and fixture helpers for the pinned-CDADE reference worker.
# ABOUTME: Characterises reachable CDADE primitives on fixed seeded inputs, apart from the pipeline.
"""Imported only by ``scripts/_reference_worker.py`` under the original interpreter.

The characterisation stages call original primitives on fixed inputs. They are
evidence about those functions, never a claim that the original pipeline ran.
"""

import hashlib
import sys
import traceback

LOG = {
    "environment": {},
    "outputs": {},
    "exceptions": [],
    "evidence": {},
    "task_names": None,
}
POOL = (
    "pca",
    "lof",
    "knn",
    "hbos",
    "mcd",
    "iforest",
)  # config default (iforest) runs last
SEED = 42


def stage(name, fn, *args):
    """Run one stage, recording any exception instead of propagating it."""
    try:
        return fn(*args)
    except Exception as exc:  # noqa: BLE001 (any failure is audit evidence)
        LOG["exceptions"].append(
            {
                "stage": name,
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
        return None


def array_hash(value):
    import numpy as np

    arr = np.ascontiguousarray(value)
    head = f"{arr.dtype.str}|{arr.shape}|".encode()
    return hashlib.sha256(head + arr.tobytes()).hexdigest()


def save(out, component, arrays, *, seed, params, callers):
    """Write one fixture file and describe it; the exporter hashes the file."""
    import numpy as np

    np.savez(out / f"{component}.npz", **arrays)
    LOG["outputs"][component] = {
        "path": f"fixtures/{component}.npz",
        "seed": seed,
        "params": params,
        "callers": callers,
        "array_hashes": {k: array_hash(v) for k, v in arrays.items()},
        "shapes": {k: list(np.shape(v)) for k, v in arrays.items()},
    }


def evt_stage(out):
    from types import SimpleNamespace

    import numpy as np
    import pandas as pd
    from cdade.baselines.reconciliation_evt import _fit_gpd, _gpd_survival
    from cdade.reconciliation.evt import EVTReconciler

    residuals = np.random.default_rng(SEED).standard_t(4, size=1000)
    threshold, shape, scale = _fit_gpd(residuals, 0.05)
    grid = np.linspace(0.0, 10.0, 101)
    arrays = {
        "residuals": residuals,
        "gpd": np.array([threshold, shape, scale]),
        "grid": grid,
        "survival": _gpd_survival(grid, threshold, shape, scale),
    }
    save(
        out,
        "evt",
        arrays,
        seed=SEED,
        params={"contamination": 0.05, "t_df": 4},
        callers=["cdade.baselines.reconciliation_evt._fit_gpd", "_gpd_survival"],
    )
    EVTReconciler(SimpleNamespace(contamination=0.05)).fit(pd.Series(residuals))


def detector_stage(out):
    import numpy as np
    from cdade.registry import get_detector
    from sklearn.covariance import MinCovDet

    for name in POOL:
        __import__(f"cdade.detectors.{name}")
    rng = np.random.default_rng(SEED)
    x_train = rng.normal(size=(240, 3))
    inliers, outliers = rng.normal(size=(40, 3)), rng.normal(size=(10, 3)) + 10
    x_test = np.vstack([inliers, outliers])
    arrays, orientation = {"x_train": x_train, "x_test": x_test}, {}
    for name in POOL:
        cls = get_detector(name)
        cfg_cls = getattr(sys.modules[cls.__module__], f"{cls.__name__}Config")
        scores = stage(
            f"detector_{name}",
            lambda c=cls, f=cfg_cls: c(f()).fit(x_train).score(x_test),
        )
        if scores is not None:
            arrays[name] = np.asarray(scores, dtype=float)
            orientation[name] = bool(np.median(scores[40:]) > np.median(scores[:40]))
    arrays["sklearn_mcd_covariance"] = (
        MinCovDet(random_state=SEED).fit(x_train).covariance_
    )
    save(
        out,
        "detectors",
        arrays,
        seed=SEED,
        params={"train": [240, 3], "outlier_shift": 10},
        callers=[f"cdade.detectors.{n}" for n in POOL],
    )
    LOG["evidence"]["detectors"] = {"outliers_score_higher": orientation}


def selection_stage(out):
    from itertools import combinations

    import numpy as np
    from cdade.selection import DriftDetector, ensemble_q_diversity, meta_des_competence
    from cdade.selection.diversity import q_statistic_pair
    from cdade.selection.selector import MetaDESSelector

    rng = np.random.default_rng(SEED)
    preds = rng.integers(0, 2, size=(6, 12))
    labels = rng.integers(0, 2, size=12)
    pairs = combinations(range(6), 2)
    q = np.array([q_statistic_pair(preds[i], preds[j], labels) for i, j in pairs])
    competence = meta_des_competence(preds[None, :, :], labels[None, :])[0].mean(axis=1)
    signal = np.concatenate([np.full(60, 0.2), np.full(60, 0.8)]) + rng.normal(
        0, 0.01, 120
    )
    drift = DriftDetector("adwin")
    flags = np.array([drift.update(float(v)) for v in signal])
    arrays = {
        "predictions": preds,
        "labels": labels,
        "q_pairs": q,
        "diversity": np.array(ensemble_q_diversity(preds, labels)),
        "competence": competence,
        "selected": MetaDESSelector(k=5, alpha=0.5).select(competence, preds, labels),
        "drift_signal": signal,
        "drift_flags": flags,
    }
    save(
        out,
        "select",
        arrays,
        seed=SEED,
        params={"k": 5, "alpha": 0.5, "adwin_delta": 0.002},
        callers=[
            "cdade.selection.diversity",
            "competence",
            "selector",
            "drift_detector",
        ],
    )


def metrics_stage(out):
    import numpy as np
    from cdade.evaluation.metrics import compute_all_metrics

    rng = np.random.default_rng(SEED)
    labels = (rng.uniform(size=120) < 0.1).astype(int)
    scores = rng.normal(size=120) + 2 * labels
    values = compute_all_metrics(labels, scores, nab_window=4)
    arrays = {
        "labels": labels,
        "scores": scores,
        "metrics": np.array([values[k] for k in sorted(values)]),
    }
    save(
        out,
        "metrics",
        arrays,
        seed=SEED,
        params={"keys": sorted(values), "nab_window": 4},
        callers=["cdade.evaluation.metrics.compute_all_metrics"],
    )


def stats_stage(out):
    import numpy as np
    from cdade.evaluation import stats as st

    rng = np.random.default_rng(SEED)
    auc = rng.uniform(0.3, 0.9, size=(14, 6))
    y_true = (rng.uniform(size=60) < 0.2).astype(float)
    a, b = rng.uniform(size=60), rng.uniform(size=60)
    methods = {f"m{i}": {"auc_pr": 0.0} for i in range(6)}
    probe = st.run_stats_pipeline(
        methods,
        y_true=y_true,
        cdade_scores=a,
        baseline_scores={"b": b},
        auc_pr_matrix=auc,
    )
    delta, low, high = st.cliffs_delta_with_ci(a, b, n_bootstrap=200)
    dm = probe["diebold_mariano"]["b"]
    arrays = {
        "auc_pr": auc,
        "y_true": y_true,
        "a": a,
        "b": b,
        "cliffs": np.array([delta, low, high]),
        "dm": np.array([dm["stat"], dm["p_value"]]),
    }
    save(
        out,
        "stats",
        arrays,
        seed=SEED,
        params={"cliffs_bootstrap": 200, "rng": "RandomState"},
        callers=["cdade.evaluation.stats.run_stats_pipeline", "cliffs_delta_with_ci"],
    )
    LOG["evidence"]["stats"] = {
        "friedman": probe["friedman"],
        "followups_after_friedman": {
            k: bool(probe[k]) for k in ("wilcoxon", "diebold_mariano", "cliffs_delta")
        },
    }


PRIMITIVES = (
    ("evt", evt_stage),
    ("detectors", detector_stage),
    ("select", selection_stage),
    ("metrics", metrics_stage),
    ("stats", stats_stage),
)
