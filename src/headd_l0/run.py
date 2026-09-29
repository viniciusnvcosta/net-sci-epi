"""E0* sanity gate and local experiment entry point."""

import argparse
import hashlib
import json
import subprocess
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from numbers import Real
from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0.data import hierarchy, load_sivep
from headd_l0.inject import InjectionConfig, inject_original_bounded
from headd_l0.stats import task_bootstrap

BASELINE_ID = "B1*"
REFERENCE_SHA = "fbfa609bba6cb0b0f2a9e8d73be18022aec319b7"


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
    """Validate paired regional evidence and bootstrap AP gains over 13 regions.

    PA rows are optional descriptive evidence. Their AP and class balance do not
    enter the gate, though duplicate or unknown task/arm keys are rejected.

    Args:
        components_ok: Outcome of the component behavior suite for this code.
        auc_pr: Columns task, arm, auc_pr, n_positive, n_negative. Regional
            rows require finite AP and both classes in the 72-month test window.
        rng: Independent bootstrap stream; never used for data generation.
    """
    names = hierarchy().leaves
    required = {"task", "arm", "auc_pr", "n_positive", "n_negative"}
    valid = required.issubset(auc_pr.columns)
    if valid:
        keys = list(zip(auc_pr.task, auc_pr.arm, strict=True))
        expected = {(name, arm) for name in names for arm in ("B1*", "zscore")}
        permitted = expected | {("PA", arm) for arm in ("B1*", "zscore")}
        valid = (
            len(keys) == len(set(keys))
            and set(keys).issubset(permitted)
            and expected.issubset(keys)
        )
    if valid:
        regional = auc_pr.loc[auc_pr.task != "PA"]
        columns = ("auc_pr", "n_positive", "n_negative")
        valid = all(
            regional[column]
            .map(lambda value: isinstance(value, Real) and not isinstance(value, bool))
            .all()
            for column in columns
        )
    if valid:
        numeric = regional[list(columns)].to_numpy(float)
        counts = numeric[:, 1:]
        valid = bool(
            np.isfinite(numeric).all()
            and ((numeric[:, 0] >= 0) & (numeric[:, 0] <= 1)).all()
            and (counts > 0).all()
            and (counts == np.floor(counts)).all()
            and (counts.sum(axis=1) == 72).all()
        )
    if valid:
        sizes = regional.groupby("task")[["n_positive", "n_negative"]].nunique()
        valid = bool((sizes == 1).all().all())
    lower = None
    if valid:
        table = regional.pivot(index="task", columns="arm", values="auc_pr")
        delta = (table["B1*"] - table["zscore"]).loc[list(names)].to_numpy()
        lower = float(task_bootstrap(delta, rng, n_boot=10000).low)
    conditions = {
        "components": bool(components_ok),
        "thirteen_regional_tasks": valid,
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

    run_id: str
    root_seed: int
    raw_dir: Path
    output_dir: Path
    baseline_id: str = BASELINE_ID
    reference_sha: str = REFERENCE_SHA

    def __post_init__(self) -> None:
        """Validate every construction path and normalize strings to Paths.

        Relative paths remain relative to the execution directory; ``~`` expands
        to the current user's home. No filesystem writes occur during validation.
        """
        if self.baseline_id != BASELINE_ID or self.reference_sha != REFERENCE_SHA:
            raise ValueError("E0* requires the approved baseline and pinned reference")
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or Path(self.run_id).name != self.run_id
            or self.run_id in {".", ".."}
            or "\\" in self.run_id
        ):
            raise ValueError("run_id must be a directory name")
        if type(self.root_seed) is not int or self.root_seed < 0:
            raise ValueError("root_seed must be a nonnegative integer")
        for name in ("raw_dir", "output_dir"):
            value = getattr(self, name)
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{name} must be a nonempty path")
            object.__setattr__(self, name, Path(value).expanduser())


def load_config(path: Path) -> E0Config:
    """Read TOML; execution fields are required and validated by E0Config."""
    with Path(path).open("rb") as handle:
        values = tomllib.load(handle)
    try:
        return E0Config(**values)
    except TypeError as exc:
        raise ValueError(f"invalid E0 configuration: {exc}") from exc


def run_preflight(cfg: E0Config, counts: np.ndarray) -> Path:
    """Persist coherent injection and class diagnostics before detector execution.

    No component/performance gate is inferred from preparation. A single-class
    regional task fails E0*; otherwise the performance gate remains pending
    until Experiments Task 0 calls check_e0_star with evaluated model outputs.
    """

    seed = np.random.SeedSequence(cfg.root_seed)
    # Layer 0 uses the configured root stream; later calibration/evaluation
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
    tasks["denominator"] = 72
    tasks["window_start"] = 60
    tasks["window_end"] = 131
    tasks["positive_prevalence"] = tasks.n_positive / tasks.denominator
    tasks["role"] = ["descriptive", *(["regional"] * 13)]
    tasks["in_gate"] = [False, *([True] * 13)]
    tasks.to_parquet(path / "tasks.parquet", index=False)
    pa_diagnostics = {
        "positive_prevalence": float(tasks.loc[0, "positive_prevalence"]),
        "union_coverage_months": int(result.mask[0, 60:].sum()),
        "denominator": 72,
        "counts_coherent": bool(
            np.array_equal(result.counts[0], result.counts[1:].sum(axis=0))
        ),
        "labels_union_coherent": bool(
            np.array_equal(result.mask[0], result.mask[1:].any(axis=0))
        ),
    }
    (path / "pa_diagnostics.json").write_text(
        json.dumps(pa_diagnostics, indent=2) + "\n"
    )
    pd.DataFrame([asdict(event) for event in result.events]).to_parquet(
        path / "events.parquet", index=False
    )
    invalid = tasks.loc[
        tasks.in_gate & ((tasks.n_positive == 0) | (tasks.n_negative == 0)), "task"
    ]
    git = ["git", "-C", str(Path(__file__).resolve().parent)]
    manifest = {
        "config": {
            k: str(v) if isinstance(v, Path) else v for k, v in asdict(cfg).items()
        },
        "baseline_id": cfg.baseline_id,
        "e0_star_revision": "D-E0*-R1",
        "e0_star_decision_commit": "50f8b3f29bacc4747329addf80cee6719fe3c7fc",
        "e0_star_gate_version": "regional-13-v1",
        "reference_sha": cfg.reference_sha,
        "git_sha": subprocess.check_output(
            [*git, "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()
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
