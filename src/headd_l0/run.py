"""E0* sanity gate and local experiment entry point."""

from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

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


@dataclass(frozen=True)
class E0Config:
    """Layer-0 preparation; the experiment runner later supplies scored tasks."""

    run_id: str = "e0-star-preflight"
    root_seed: int = 42
    raw_dir: str = "/home/vinvs/projects/hybrid-theory/data/raw"
    output_dir: str = "results"
    baseline_id: str = "B1*"
    reference_sha: str = "fbfa609bba6cb0b0f2a9e8d73be18022aec319b7"


def load_config(path: "Path") -> E0Config:
    """Read the E0 preparation TOML; reject changed baseline identity or SHA."""
    import tomllib
    from pathlib import Path

    with Path(path).open("rb") as handle:
        cfg = E0Config(**tomllib.load(handle))
    if cfg.baseline_id != "B1*" or cfg.reference_sha != E0Config.reference_sha:
        raise ValueError("E0* requires the approved baseline and pinned reference")
    if (
        not cfg.run_id
        or Path(cfg.run_id).name != cfg.run_id
        or cfg.run_id in {".", ".."}
    ):
        raise ValueError("run_id must be a directory name")
    return cfg


def run_preflight(cfg: E0Config, counts: np.ndarray) -> "Path":
    """Persist coherent injection and class diagnostics before detector execution.

    No component/performance gate is inferred from preparation. A single-class
    task fails E0* immediately; otherwise the performance gate remains pending
    until Experiments Task 4 calls check_e0_star with evaluated model outputs.
    """
    import hashlib
    import json
    import subprocess
    from dataclasses import asdict
    from datetime import datetime
    from pathlib import Path

    from headd_l0.inject import InjectionConfig, inject_original_bounded

    seed = np.random.SeedSequence(cfg.root_seed)
    # Layer 0 retains the explicit seed42 stream; later calibration/evaluation
    # must spawn disjoint streams under the experiment runner's contract.
    result = inject_original_bounded(
        counts, np.random.default_rng(seed), InjectionConfig()
    )
    path = Path(cfg.output_dir) / cfg.run_id
    path.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(
        path / "injection.npz",
        counts=result.counts,
        mask=result.mask,
        onset=result.onset,
    )
    names = ("PA", *hierarchy().leaves)
    tasks = pd.DataFrame(
        {
            "task": names,
            "n_positive": result.mask[:, 60:].sum(axis=1),
            "n_negative": (~result.mask[:, 60:]).sum(axis=1),
        }
    )
    tasks.to_parquet(path / "tasks.parquet", index=False)
    pd.DataFrame([asdict(event) for event in result.events]).to_parquet(
        path / "events.parquet", index=False
    )
    invalid = tasks.loc[(tasks.n_positive == 0) | (tasks.n_negative == 0), "task"]
    manifest = {
        "config": {
            k: str(v) if isinstance(v, Path) else v for k, v in asdict(cfg).items()
        },
        "baseline_id": cfg.baseline_id,
        "reference_sha": cfg.reference_sha,
        "git_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output(["git", "status", "--porcelain"], text=True).strip()
        ),
        "timestamp": datetime.now(UTC).isoformat(),
        "seed": {"entropy": seed.entropy, "spawn_key": list(seed.spawn_key)},
        "input_sha256": hashlib.sha256(
            np.ascontiguousarray(counts).tobytes()
        ).hexdigest(),
        "injection_config": asdict(InjectionConfig()),
        "negative_injected_cells": int((result.counts < 0).sum()),
        "adjusted_onsets": sum(e.proposed_onset != e.onset for e in result.events),
        "interpretation_allowed": False,
        "gates": {
            "E0": {"status": "inconclusive"},
            "E0_star": {
                "status": "failed" if len(invalid) else "pending",
                "reasons": [f"single_class:{name}" for name in invalid],
                "components": "not_evaluated",
                "trivial_baseline": "not_evaluated",
            },
        },
    }
    (path / "manifest.json").write_text(
        json.dumps(manifest, indent=2, allow_nan=False) + "\n"
    )
    return path


def main() -> int:
    """Prepare layer 0; exit 2 while E0* cannot authorize E1 interpretation."""
    import argparse
    from pathlib import Path

    from headd_l0.data import load_sivep

    parser = argparse.ArgumentParser(
        description="Prepare E0* injection and class diagnostics"
    )
    parser.add_argument("config", type=Path)
    cfg = load_config(parser.parse_args().config)
    result = run_preflight(cfg, load_sivep(Path(cfg.raw_dir)).counts)
    print(
        f"Artifacts: {result}; E0 inconclusive; E0* does not authorize interpretation."
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
