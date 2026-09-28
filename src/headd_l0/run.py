"""E0* sanity gate and local experiment entry point."""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from headd_l0.data import hierarchy
from headd_l0.stats import task_bootstrap


@dataclass(frozen=True)
class E0StarResult:
    """Outcome of the pre-registered component, task and trivial-baseline gates."""

    passed: bool
    conditions: dict[str, bool]
    lower_bound: float | None
    reasons: tuple[str, ...]


def check_e0_star(
    components_ok: bool, auc_pr: pd.DataFrame, rng: np.random.Generator
) -> E0StarResult:
    """Check all 14 tasks, then bootstrap paired AP differences over 13 regions.

    Args:
        components_ok: Outcome of the component behavior suite for this code.
        auc_pr: Columns task, arm, auc_pr, n_positive, n_negative. Both B1* and
            zscore must have finite AP and both classes on every canonical task.
        rng: Independent bootstrap stream; never used for data generation.
    """
    names = ("PA", *hierarchy().leaves)
    required = {"task", "arm", "auc_pr", "n_positive", "n_negative"}
    valid = required.issubset(auc_pr.columns)
    if valid:
        keys = list(zip(auc_pr.task, auc_pr.arm, strict=True))
        expected = {(name, arm) for name in names for arm in ("B1*", "zscore")}
        valid = len(keys) == len(expected) and set(keys) == expected
        numeric = auc_pr[["auc_pr", "n_positive", "n_negative"]].to_numpy(float)
        valid = bool(
            valid
            and np.isfinite(numeric).all()
            and auc_pr.auc_pr.between(0, 1).all()
            and (numeric[:, 1:] > 0).all()
        )
    if valid:
        sizes = auc_pr.groupby("task")[["n_positive", "n_negative"]].nunique()
        valid = bool(
            (sizes == 1).all().all()
            and (numeric[:, 1:] == np.floor(numeric[:, 1:])).all()
        )
    lower = None
    if valid:
        table = auc_pr.pivot(index="task", columns="arm", values="auc_pr")
        delta = (table["B1*"] - table["zscore"]).loc[list(names[1:])].to_numpy()
        lower = float(task_bootstrap(delta, rng, n_boot=10000).low)
    conditions = {
        "components": bool(components_ok),
        "fourteen_tasks": valid,
        "trivial_baseline": lower is not None and lower > 0,
    }
    return E0StarResult(
        all(conditions.values()),
        conditions,
        lower,
        tuple(name for name, passed in conditions.items() if not passed),
    )
