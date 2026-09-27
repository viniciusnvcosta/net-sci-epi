# ABOUTME: Legacy-interpreter worker that runs pinned CDADE code from a git-archive snapshot.
# ABOUTME: Writes component fixtures and a JSON log of outputs, exceptions and runtime evidence.
"""Invoked only by ``scripts/export_cdade_reference.py`` with the original interpreter.

Stages named ``pipeline_*`` call the original stage functions in the order of
``dvc.yaml``; the remaining stages characterise reachable primitives on fixed
inputs. Every stage is isolated: its exception is recorded verbatim and no
output is fabricated for it. All writes stay inside the snapshot and ``--out``.
"""

import argparse
import json
import os
import platform
import sys
from importlib import metadata
from pathlib import Path

from _reference_primitives import LOG, POOL, PRIMITIVES, SEED, save, stage


def import_reference(snapshot):
    import cdade

    origin = Path(cdade.__file__).resolve()
    LOG["environment"]["cdade_file"] = str(origin)
    LOG["environment"]["imported_from_snapshot"] = snapshot in origin.parents
    return True


def environment():
    import numpy as np

    names = (
        "numpy",
        "pandas",
        "scipy",
        "scikit-learn",
        "pyod",
        "river",
        "hydra-core",
        "pyarrow",
    )
    LOG["environment"].update(
        python=platform.python_version(),
        executable=sys.executable,
        packages={n: metadata.version(n) for n in names},
        numpy_blas=np.show_config(mode="dicts")["Build Dependencies"]["blas"],
    )


def data_stage(raw_dir, out):
    import numpy as np
    from cdade.data import sivep

    state_df, hr_df = sivep.load_raw(raw_dir)
    counts = sivep.prepare_counts(hr_df)
    state = sivep.prepare_state_counts(state_df)
    arrays = {
        "counts": counts.to_numpy(),
        "state": state.to_numpy(),
        "state_total_tests": state_df["totalTests"].to_numpy(),
        "state_negatives": state_df["negatives"].to_numpy(),
        "leaves": np.array(sivep.build_hierarchy_spec()["leaves"]),
        "dates": np.array(counts.index.strftime("%Y-%m-%d"), dtype=str),
        "summing_matrix": sivep.build_summing_matrix(),
    }
    callers = ["cdade.data.sivep.load_raw", "prepare_counts", "prepare_state_counts"]
    save(
        out,
        "data",
        arrays,
        seed=None,
        params={"raw_dir": str(raw_dir)},
        callers=callers,
    )
    mismatch = counts.sum(axis=1).to_numpy() != state.to_numpy()
    LOG["evidence"]["data"] = {
        "leaf_sum_equals_state": not bool(mismatch.any()),
        "mismatched_months": int(mismatch.sum()),
        "index_equal": bool(counts.index.equals(state.index)),
        "first": str(arrays["dates"][0]),
        "last": str(arrays["dates"][-1]),
    }


def compose(snapshot, *overrides):
    from hydra import compose as hydra_compose
    from hydra import initialize_config_dir

    with initialize_config_dir(config_dir=str(snapshot / "configs"), version_base=None):
        return hydra_compose(config_name="config", overrides=list(overrides))


def pipeline_prepare_inject(snapshot, out):
    import cdade.data.loaders  # noqa: F401  (registers dataset plugins)
    import pandas as pd
    import yaml
    from cdade.data import inject, prepare

    params = yaml.safe_load((snapshot / "params.yaml").read_text())["inject"]
    processed, injected = snapshot / "data/processed", snapshot / "data/injected"
    prepare.run(["sivep"], processed, project_root=snapshot)
    kwargs = {k: params[k] for k in inject._DEFAULTS}
    inject.run(["sivep"], processed, injected, **kwargs)
    names = ("counts_injected", "counts_mask", "state_injected", "state_mask")
    read = {
        k: pd.read_parquet(injected / f"sivep_{k}.parquet").to_numpy() for k in names
    }
    read["processed_counts"] = pd.read_parquet(
        processed / "sivep_counts.parquet"
    ).to_numpy()
    callers = ["cdade.data.prepare.run", "cdade.data.inject.run"]
    save(out, "inject", read, seed=params["seed"], params=kwargs, callers=callers)
    LOG["evidence"]["inject"] = {
        "rng_order": "sivep counts then sivep state; sivep is first in datasets.active",
        "negative_injected_cells": int((read["counts_injected"] < 0).sum()),
        "anomalous_cells": int(read["counts_mask"].sum()),
    }


def pipeline_detect(snapshot, name):
    from cdade.detectors.run_detect import run_detect

    return run_detect(compose(snapshot, f"detector={name}"), "sivep")["scores"]


def pipeline_reconcile(snapshot, method):
    from cdade.reconciliation.run_reconcile import run_reconcile

    result = run_reconcile(compose(snapshot, f"reconciliation={method}"), "sivep")
    return list(result["coherent_scores"].shape)


def pipeline_select(snapshot):
    from cdade.selection.run_select import run_select

    return run_select(compose(snapshot), "sivep")


def pipeline_evaluate(snapshot, blended, out):
    import numpy as np
    import pandas as pd
    from cdade.baselines import run_baselines as rb
    from cdade.evaluation.run_evaluate import evaluate_all_methods

    cfg = compose(snapshot)
    injected = snapshot / "data/injected"
    counts = pd.read_parquet(injected / "sivep_counts_injected.parquet")
    mask = pd.read_parquet(injected / "sivep_counts_mask.parquet")
    y_true = mask.to_numpy().astype(int).max(axis=1)
    n_test = int(len(y_true) * cfg.evaluation.test_frac)
    x_train, x_val, x_test, _, y_val, _ = rb._train_test_split(counts, mask)
    np.random.seed(int(cfg.experiment.seed))
    runners = {
        "b1": lambda: rb._run_b1(counts, cfg),
        "b2": lambda: rb._run_b2(x_train, x_val, y_val, x_test, cfg),
        "b3": lambda: rb._run_b3(x_train, x_test, cfg),
        "b4": lambda: rb._run_b4(x_train, x_val, y_val, x_test, cfg),
        "b5": lambda: rb._run_b5(x_train, x_test, cfg),
    }
    baselines = {}
    for key, run in runners.items():
        scores = stage(f"pipeline_baseline_{key}", lambda run=run: run()[0])
        if scores is not None:
            baselines[key] = np.asarray(scores, dtype=float)
    metrics = evaluate_all_methods(
        y_true[-n_test:], blended[-n_test:], dict(baselines), 4
    )
    rows = [{"task": "sivep", "method": m, **v} for m, v in metrics.items()]
    (out / "pipeline_metrics.json").write_text(json.dumps(rows, indent=2) + "\n")
    LOG["outputs"]["pipeline_metrics"] = {
        "path": "fixtures/pipeline_metrics.json",
        "seed": int(cfg.experiment.seed),
        "params": {"test_frac": cfg.evaluation.test_frac, "nab_window": 4},
        "callers": [
            "cdade.baselines.run_baselines._run_b1.._run_b5",
            "cdade.evaluation.run_evaluate.evaluate_all_methods",
        ],
        "not_run": {"b6-b8": "recurrent baselines, excluded from the port"},
    }
    arrays = {"y_true": y_true, "cdade_test": blended[-n_test:], **baselines}
    save(
        out,
        "evaluate",
        arrays,
        seed=int(cfg.experiment.seed),
        params={"n_test": n_test},
        callers=["cdade.evaluation.run_evaluate (label reduction)"],
    )
    LOG["task_names"] = sorted({row["task"] for row in rows})
    LOG["evidence"]["evaluate"] = {
        "label_shape": list(y_true.shape),
        "n_test_evaluate": n_test,
        "n_test_baselines": len(x_test),
        "test_positive_rate": float(y_true[-n_test:].mean()),
        "auc_pr": {m: v["auc_pr"] for m, v in metrics.items()},
    }


def select_lookahead_probe(snapshot):
    """Perturb scores from t=90 on and report which earlier outputs change."""
    import numpy as np
    import pandas as pd
    from cdade.selection.run_select import _run_single_dataset

    cfg = compose(snapshot)
    scores = np.random.default_rng(SEED).normal(size=(132, 6))
    blended = []
    for label, shift in (("base", 0.0), ("changed", 1000.0)):
        values = scores.copy()
        values[90:] += shift
        recon = snapshot / f"results/probe/{label}/recon"
        out = snapshot / f"results/probe/{label}/out"
        recon.mkdir(parents=True)
        out.mkdir(parents=True)
        pd.DataFrame(values).to_csv(recon / "leaf_forecasts_reconciled.csv")
        blended.append(_run_single_dataset(cfg, "probe", recon, out)["blended_scores"])
    changed = np.flatnonzero(np.abs(blended[0][:90] - blended[1][:90]) > 0)
    return {
        "cut": 90,
        "input": "Generator(42).normal((132, 6))",
        "prefix_indices_changed": changed.tolist(),
    }


def run_all(snapshot, out):
    import numpy as np

    stage("pipeline_prepare_inject", pipeline_prepare_inject, snapshot, out)
    scores = {
        n: stage(f"pipeline_detect_{n}", pipeline_detect, snapshot, n) for n in POOL
    }
    kept = {n: np.asarray(s, dtype=float) for n, s in scores.items() if s is not None}
    if kept:
        save(
            out,
            "detect",
            kept,
            seed=None,
            params={"input": "injected counts, fit=score"},
            callers=["cdade.detectors.run_detect.run_detect"],
        )
    methods = ("min_t", "bottom_up")  # config default (bottom_up) runs last
    shapes = {
        m: stage(f"pipeline_reconcile_{m}", pipeline_reconcile, snapshot, m)
        for m in methods
    }
    LOG["evidence"]["reconcile"] = {
        "output_shape": shapes,
        "input_columns": _columns(snapshot),
    }
    selected = stage("pipeline_select", pipeline_select, snapshot)
    if selected is not None:
        stage(
            "pipeline_evaluate",
            pipeline_evaluate,
            snapshot,
            selected["blended_scores"],
            out,
        )
    probe = stage("select_lookahead", select_lookahead_probe, snapshot)
    LOG["evidence"]["select_lookahead"] = probe
    for name, fn in PRIMITIVES:
        stage(name, fn, out)


def _columns(snapshot):
    path = snapshot / "results/detectors/sivep/leaf_forecasts.csv"
    return path.read_text().splitlines()[0].split(",") if path.exists() else None


def main():
    parser = argparse.ArgumentParser()
    for flag in ("--snapshot", "--raw-dir", "--out", "--log"):
        parser.add_argument(flag, type=Path, required=True)
    args = parser.parse_args()
    snapshot, out = args.snapshot.resolve(), args.out
    out.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(snapshot))
    os.chdir(snapshot)
    try:
        if stage("import_reference", import_reference, snapshot):
            stage("environment", environment)
            stage("data", data_stage, args.raw_dir, out)
            run_all(snapshot, out)
    finally:
        args.log.write_text(json.dumps(LOG, indent=2, default=str) + "\n")


if __name__ == "__main__":
    main()
