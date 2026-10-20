"""Training-only endemic calibration under the fixed P5 technical profile."""

import argparse
import json
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Literal

import numpy as np

from headd_l0.data import LEAVES, RAW_FILES, load_sivep
from headd_l0.simulate import (
    _MONTH_EDGES,
    _MONTHLY,
    _PROFILE_ID,
    SimConfig,
    _calendar,
    _integrate,
    _observe,
)

_TRAIN_MONTHS = 60
_REPLICATES = 128
_BRACKET = (0.0, 1 / 7)
_MAX_ITERATIONS = 30


@dataclass(frozen=True)
class CalibrationConfig:
    """Select input/output paths and noise; numerical fitting rules are fixed."""

    raw_dir: Path
    processed_dir: Path
    output_dir: Path
    run_id: str
    root_seed: int
    noise: Literal["white", "env", "dem"] = "white"
    profile_id: str = _PROFILE_ID

    def __post_init__(self) -> None:
        SimConfig(profile_id=self.profile_id, noise=self.noise)
        if type(self.root_seed) is not int or self.root_seed < 0:
            raise ValueError("root_seed must be a nonnegative integer")
        if (
            not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or Path(self.run_id).name != self.run_id
            or self.run_id in {".", ".."}
        ):
            raise ValueError("run_id must be a directory name")
        for key in ("raw_dir", "processed_dir", "output_dir"):
            value = getattr(self, key)
            if not isinstance(value, (str, Path)) or not str(value).strip():
                raise ValueError(f"{key} must be a nonempty path")
            object.__setattr__(self, key, Path(value).expanduser())


@dataclass(frozen=True)
class CalibrationResult:
    """Canonical regional hazards, training targets, residuals and fit cost."""

    names: tuple[str, ...]
    hazards: np.ndarray
    target_medians: np.ndarray
    simulated_medians: np.ndarray
    errors: np.ndarray
    iterations: np.ndarray


def _draws(
    seeds: Sequence[np.random.SeedSequence],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Preallocate independent replicate streams, matching simulate draw order."""
    burn_steps = len(_calendar(-_MONTHLY["burn_in_days"], 0)) - 1
    steps = len(_calendar(0, int(_MONTH_EDGES[-1]))) - 1
    train_steps = len(_calendar(0, int(_MONTH_EDGES[_TRAIN_MONTHS]))) - 1
    burn = np.empty((burn_steps, len(seeds), 2))
    noise = np.empty((train_steps, len(seeds), 2))
    uniforms = np.empty((_TRAIN_MONTHS, len(seeds), 2))
    for i, seed in enumerate(seeds):
        rng = np.random.default_rng(seed)
        burn[:, i] = rng.standard_normal((burn_steps, 2))
        noise[:, i] = rng.standard_normal((steps, 2))[:train_steps]
        uniforms[:, i] = rng.random((_MONTHLY["months"], 2))[:_TRAIN_MONTHS]
    return burn, noise, uniforms


def _null_training_counts(
    hazard: float,
    noise: str,
    draws: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> np.ndarray:
    """Evaluate independent nulls in one vectorized integration, with no twin."""
    burn, innovations, uniforms = draws
    cfg = SimConfig(noise=noise, label="N", endemic_hazard=hazard)
    p = _MONTHLY
    state = np.tile(
        [p["population"] - p["initial_infected"], p["initial_infected"]],
        (burn.shape[1], 1),
    )
    _, state, _ = _integrate(cfg, _calendar(-p["burn_in_days"], 0), state, burn, "N")
    latent, _, _ = _integrate(
        cfg,
        _calendar(0, int(_MONTH_EDGES[_TRAIN_MONTHS])),
        state,
        innovations,
        "N",
    )
    return _observe(latent[:_TRAIN_MONTHS], uniforms, cfg.testing_rate).T


def _fit(target: float, noise: str, draws: tuple) -> tuple[float, float, int]:
    """Bisect the pre-registered bracket, reusing exactly the same innovations."""
    tolerance = max(1.0, 0.1 * target)
    low, high = _BRACKET
    lower = float(np.median(_null_training_counts(low, noise, draws)))
    if abs(lower - target) <= tolerance:
        return low, lower, 0
    upper = float(np.median(_null_training_counts(high, noise, draws)))
    if abs(upper - target) <= tolerance:
        return high, upper, 0
    if not lower < target < upper:
        raise ValueError(
            f"target {target} outside bracket summaries [{lower}, {upper}]"
        )
    for iteration in range(1, _MAX_ITERATIONS + 1):
        middle = (low + high) / 2
        summary = float(np.median(_null_training_counts(middle, noise, draws)))
        if abs(summary - target) <= tolerance:
            return middle, summary, iteration
        if summary < target:
            low = middle
        else:
            high = middle
    raise ValueError("calibration did not converge within 30 bisection iterations")


def calibrate(
    counts: np.ndarray,
    names: Sequence[str],
    seeds: Sequence[Sequence[np.random.SeedSequence]],
    *,
    noise: Literal["white", "env", "dem"] = "white",
) -> CalibrationResult:
    """Fit regional hazards from training counts without accessing evaluation.

    Args:
        counts: Observed nonnegative region-by-month counts; at least 60 months.
        names: Thirteen unique canonical names, aligned with the input rows.
        seeds: Caller-spawned 13 by 128 SeedSequences in canonical region order.
        noise: Fixed P5 noise profile, with theta=0.5 and epsilon=0.

    Returns:
        Frozen calibration result in canonical region order.

    Raises:
        ValueError: If inputs are invalid or any regional fit fails. The bracket
            is never expanded and no evaluation-month values enter the fit.
    """
    SimConfig(noise=noise)
    counts = np.asarray(counts)
    if (
        counts.ndim != 2
        or counts.shape[0] != len(LEAVES)
        or counts.shape[1] < _TRAIN_MONTHS
        or len(names) != len(LEAVES)
        or set(names) != set(LEAVES)
    ):
        raise ValueError("counts need 13 named regions and at least 60 months")
    training = counts[[list(names).index(name) for name in LEAVES], :_TRAIN_MONTHS]
    if not np.isfinite(training).all() or (training < 0).any():
        raise ValueError("training counts must be finite and nonnegative")
    if len(seeds) != 13 or any(
        len(region) != _REPLICATES
        or any(not isinstance(seed, np.random.SeedSequence) for seed in region)
        for region in seeds
    ):
        raise ValueError("calibration requires 13 by 128 caller-spawned seeds")
    targets = np.median(training, axis=1)
    fits = []
    for name, target, region_seeds in zip(LEAVES, targets, seeds, strict=True):
        try:
            fits.append(_fit(float(target), noise, _draws(region_seeds)))
        except ValueError as exc:
            raise ValueError(f"{name}: {exc}") from exc
    hazards, medians, iterations = np.asarray(fits).T
    return CalibrationResult(
        LEAVES, hazards, targets, medians, medians - targets, iterations.astype(int)
    )


def load_config(path: Path) -> CalibrationConfig:
    """Read a calibration TOML into the frozen, fixed-profile configuration."""
    return CalibrationConfig(**tomllib.loads(Path(path).read_text()))


def main(argv: list[str] | None = None) -> int:
    """Fit from SIVEP training counts and save derived artifacts and provenance.

    Args:
        argv: CLI arguments; one calibration TOML path.

    Returns:
        Zero for a completed technical fit, two for calibration failure.
        Scientific ratification and G4 remain pending in either case.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    config_path = parser.parse_args(argv).config
    cfg = load_config(config_path)
    run_path = cfg.output_dir / cfg.run_id
    if cfg.processed_dir.exists() or run_path.exists():
        raise FileExistsError("processed or run directory already exists")
    bundle = load_sivep(cfg.raw_dir)
    calibration_seed = np.random.SeedSequence(cfg.root_seed).spawn(3)[2]
    seeds = tuple(
        tuple(region.spawn(_REPLICATES)) for region in calibration_seed.spawn(13)
    )
    git = ["git", "-C", str(Path(__file__).resolve().parent)]
    manifest = {
        "config": {
            key: str(value) if isinstance(value, Path) else value
            for key, value in asdict(cfg).items()
        },
        "config_sha256": sha256(config_path.read_bytes()).hexdigest(),
        "input_sha256": {
            name: sha256((cfg.raw_dir / name).read_bytes()).hexdigest()
            for name in RAW_FILES
        },
        "code_sha256": {
            name: sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
            for name in ("calibrate.py", "simulate.py", "data.py")
        },
        "git_sha": subprocess.check_output(
            [*git, "rev-parse", "HEAD"], text=True
        ).strip(),
        "git_dirty": bool(
            subprocess.check_output([*git, "status", "--porcelain"], text=True).strip()
        ),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "names": list(LEAVES),
        "train_months": _TRAIN_MONTHS,
        "replicates_per_candidate": _REPLICATES,
        "nu_bracket_per_day": _BRACKET,
        "max_iterations": _MAX_ITERATIONS,
        "tolerance_counts": "max(1, 0.1*target_median)",
        "simulation": asdict(SimConfig(noise=cfg.noise, label="N")),
        "monthly_profile": _MONTHLY,
        "seeds": [
            [
                {"entropy": seed.entropy, "spawn_key": list(seed.spawn_key)}
                for seed in region
            ]
            for region in seeds
        ],
        "scientific_ratification": "pending",
        "G4": "pending",
        "interpretation_allowed": False,
        "status": "failed",
    }
    cfg.processed_dir.mkdir(parents=True)
    run_path.mkdir(parents=True)
    try:
        result = calibrate(
            bundle.counts, bundle.hierarchy.leaves, seeds, noise=cfg.noise
        )
        artifact = cfg.processed_dir / "endemic_calibration.npz"
        np.savez(artifact, **asdict(result))
        manifest["artifact_sha256"] = {
            artifact.name: sha256(artifact.read_bytes()).hexdigest()
        }
        manifest["status"] = "ready"
    except ValueError as exc:
        manifest["error"] = str(exc)
    for directory in (cfg.processed_dir, run_path):
        (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return 0 if manifest["status"] == "ready" else 2


if __name__ == "__main__":
    sys.exit(main())
