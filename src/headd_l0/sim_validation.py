"""Fixed single-region P5 diagnostics; scientific eligibility stays blocked."""

import importlib.metadata
import json
import platform
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0._sim_validation_io import _publish, _sha256, _write_json
from headd_l0.features import rolling_ews
from headd_l0.gao_sources import verify_sources
from headd_l0.simulate import SimConfig, simulate

CELLS = tuple(
    (noise, label) for noise in ("white", "env", "dem") for label in ("T", "N")
)
_MANIFEST = Path("tests/reference/gao_manifest.json")
_FROZEN = {
    "simulation": {
        "profile_id": "P5-IMPL-2026-10-19-v1",
        "noise": "white",
        "label": "T",
        "testing_rate": 0.5,
    },
    "validation": {"root_seed": 42, "replicates_per_noise_label": 64},
}


@dataclass(frozen=True)
class G4Config:
    """Identity and local input/output paths; the scientific design is fixed."""

    run_id: str
    output_dir: Path
    simulation_config: Path
    archive_path: Path
    supplement_path: Path


def _load_config(path: Path) -> G4Config:
    raw = tomllib.loads(path.read_text())
    if set(raw) != set(G4Config.__dataclass_fields__) or not all(
        isinstance(value, str) and value for value in raw.values()
    ):
        raise ValueError("invalid G4 configuration: require exactly five string fields")
    if raw["run_id"] in (".", "..") or Path(raw["run_id"]).name != raw["run_id"]:
        raise ValueError("invalid G4 configuration: run_id must be one path component")
    cfg = G4Config(
        raw["run_id"],
        **{key: Path(value).resolve() for key, value in raw.items() if key != "run_id"},
    )
    if tomllib.loads(cfg.simulation_config.read_text()) != _FROZEN:
        raise ValueError("referenced simulation configuration violates frozen design")
    return cfg


def _monthly_seeds():
    _, monthly, _ = np.random.SeedSequence(42).spawn(3)
    for (noise, label), cell in zip(CELLS, monthly.spawn(6), strict=True):
        for replicate, seed in enumerate(cell.spawn(64)):
            yield noise, label, replicate, seed


def _month_edges(manifest: dict) -> np.ndarray:
    profile = manifest["monthly_profile"]
    start = np.datetime64(profile["start"], "M")
    return np.arange(start, start + np.timedelta64(profile["months"] + 1, "M")).astype(
        "datetime64[D]"
    )


def _design_month(manifest: dict) -> int:
    p = manifest["monthly_profile"]
    crossing = (
        p["ramp_start_week"] * 7
        + (1 - p["R0_start"])
        / (p["R0_end_T"] - p["R0_start"])
        * (p["ramp_end_week"] - p["ramp_start_week"])
        * 7
    )
    edges = (_month_edges(manifest) - np.datetime64(p["start"], "D")).astype(int)
    month = int(np.searchsorted(edges, crossing, side="right") - 1)
    if month != 75 or p["months"] != 132 or p["regions_initial_validation"] != 1:
        raise ValueError("manifest violates frozen monthly design")
    return month


def _window_statistics(counts: np.ndarray, month: int) -> dict:
    if month < 12 or len(counts) < month:
        raise ValueError("incomplete prespecified diagnostic window")
    values, masks = rolling_ews(counts[month - 12 : month], 12)
    return {
        "window_start": month - 12,
        "window_end_exclusive": month,
        "CV": float(values[-1, 1]),
        "CV_valid": bool(masks[-1, 1]),
        "AR1": float(values[-1, 2]),
        "AR1_valid": bool(masks[-1, 2]),
    }


def _summaries(frame: pd.DataFrame) -> pd.DataFrame:
    expected = {(noise, label, i) for noise, label in CELLS for i in range(64)}
    actual = list(
        frame[["noise", "label", "replicate"]].itertuples(index=False, name=None)
    )
    if len(actual) != len(expected) or set(actual) != expected:
        raise ValueError(
            "monthly coverage must contain every requested address exactly once"
        )
    rows = []
    for noise, label in CELLS:
        cell = frame[(frame.noise == noise) & (frame.label == label)]
        row = {
            "noise": noise,
            "label": label,
            "requested": 64,
            "completed": len(cell),
            "replicate_ids": sorted(cell.replicate.tolist()),
        }
        for statistic in ("CV", "AR1"):
            valid = cell[f"{statistic}_valid"].astype(bool)
            values = cell.loc[valid, statistic]
            row.update(
                {
                    f"{statistic}_valid_count": int(valid.sum()),
                    f"{statistic}_invalid_count": int((~valid).sum()),
                    f"{statistic}_median": float(values.median())
                    if len(values)
                    else None,
                }
            )
        rows.append(row)
    return pd.DataFrame(rows)


def _technical_checks(primary, zero, one, month: int, ramp_month: int) -> dict:
    arrays = [
        getattr(result, name)
        for result in (primary, zero, one)
        for name in ("counts", "twin_counts")
    ]
    counts_valid = all(
        array.shape == (1, 132)
        and np.isfinite(array).all()
        and (array >= 0).all()
        and np.equal(array, np.floor(array)).all()
        for array in arrays
    )
    checks = {
        "finite_nonnegative_integer_counts_132": bool(counts_valid),
        "theta_zero": bool(not zero.counts.any() and not zero.twin_counts.any()),
        "theta_half_bounded_by_trials": bool(
            (primary.counts <= one.counts).all()
            and (primary.twin_counts <= one.twin_counts).all()
        ),
        "onset_matches_design": primary.onset.tolist()
        == [month if primary.label == "T" else -1],
    }
    checks["null_or_preramp_twin_equality"] = all(
        np.array_equal(
            result.counts[:, :ramp_month] if primary.label == "T" else result.counts,
            result.twin_counts[:, :ramp_month]
            if primary.label == "T"
            else result.twin_counts,
        )
        for result in (primary, zero, one)
    )
    return checks


def _generate(manifest: dict) -> tuple[dict, pd.DataFrame, dict]:
    month = _design_month(manifest)
    p = manifest["monthly_profile"]
    ramp_day = np.datetime64(p["start"], "D") + np.timedelta64(
        p["ramp_start_week"] * 7, "D"
    )
    ramp_month = int(
        np.searchsorted(_month_edges(manifest), ramp_day, side="right") - 1
    )
    names = (
        "counts",
        "twin_counts",
        "theta_zero_counts",
        "theta_zero_twin_counts",
        "theta_one_counts",
        "theta_one_twin_counts",
    )
    arrays = {name: np.empty((3, 2, 64, 132), dtype=np.int64) for name in names}
    rows, checks = [], {}
    for noise, label, replicate, seed in _monthly_seeds():
        results = [
            simulate(
                SimConfig(noise=noise, label=label, testing_rate=theta),
                np.zeros((1, 1)),
                np.random.default_rng(seed),
            )
            for theta in (0.5, 0.0, 1.0)
        ]
        if any(result.label != label for result in results):
            raise ValueError(
                f"{noise}:{label}:{replicate}: unexpected realization label"
            )
        primary, zero, one = results
        realization_checks = _technical_checks(primary, zero, one, month, ramp_month)
        if not realization_checks["finite_nonnegative_integer_counts_132"]:
            raise ValueError(f"{noise}:{label}:{replicate}: invalid 132 integer counts")
        for name, passed in realization_checks.items():
            checks[name] = checks.get(name, True) and passed
        index = (
            ("white", "env", "dem").index(noise),
            ("T", "N").index(label),
            replicate,
        )
        for name, array in zip(
            names,
            (
                getattr(result, field)
                for result in results
                for field in ("counts", "twin_counts")
            ),
            strict=True,
        ):
            arrays[name][index] = array[0]
        row = {
            "noise": noise,
            "label": label,
            "replicate": replicate,
            "onset": int(primary.onset[0]),
            "onset_expected": month if label == "T" else -1,
            "onset_coverage": "design_crossing" if label == "T" else "absence_expected",
            "entropy": seed.entropy,
            "spawn_key": list(seed.spawn_key),
            **_window_statistics(primary.counts[0], month),
            **realization_checks,
        }
        for result, prefix in zip(
            results, ("primary", "theta_zero", "theta_one"), strict=True
        ):
            row[f"{prefix}_status"] = json.dumps(
                {
                    key: result.params[key]
                    for key in (
                        "scientific_ratification",
                        "G4",
                        "interpretation_allowed",
                    )
                },
                sort_keys=True,
            )
            for phase, projection in result.params["projection"].items():
                steps = projection["steps"]
                clipped = np.asarray(projection["clipped_coordinates"])[0]
                row.update(
                    {
                        f"{prefix}_{phase}_steps": steps,
                        f"{prefix}_{phase}_coordinate_steps": steps * 2,
                        f"{prefix}_{phase}_fraction": projection["fraction"],
                    }
                )
                for coordinate, count in zip(("S", "I"), clipped, strict=True):
                    row[f"{prefix}_{phase}_clipped_{coordinate}"] = int(count)
                    row[f"{prefix}_{phase}_fraction_{coordinate}"] = float(
                        count / steps
                    )
        rows.append(row)
    frame = pd.DataFrame(rows)
    # Refuse partial/duplicate generation before writing any artifacts.
    _summaries(frame)
    arrays.update(noise=np.array(["white", "env", "dem"]), label=np.array(["T", "N"]))
    return arrays, frame, checks


def run_validation(config_path: Path) -> Path:
    """Publish complete fixed diagnostics, retaining blocked scientific status.

    Args:
        config_path: Five-field TOML, resolved from the execution directory.

    Returns:
        Immutable package path. This return does not imply scientific approval.
    """
    cfg = _load_config(config_path)
    profile = json.loads(_MANIFEST.read_text())
    sources = verify_sources(cfg.archive_path, cfg.supplement_path, _MANIFEST)
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{cfg.run_id}-", dir=cfg.output_dir))
    destination = cfg.output_dir / cfg.run_id
    try:
        arrays, replicates, technical = _generate(profile)
        np.savez_compressed(stage / "counts.npz", **arrays)
        replicates.to_parquet(stage / "replicates.parquet", index=False)
        _summaries(replicates).to_parquet(stage / "summary.parquet", index=False)
        _write_json(stage / "source_checks.json", sources)
        artifacts = {path.name: _sha256(path) for path in stage.iterdir()}
        input_paths = [
            config_path,
            cfg.simulation_config,
            _MANIFEST,
            Path(profile["fixture"]["path"]),
            Path("pyproject.toml"),
            Path("uv.lock"),
            *sorted(Path("src/headd_l0").glob("*.py")),
        ]
        provenance = {str(path.resolve()): _sha256(path) for path in input_paths}
        manifest = {
            "schema_version": 1,
            "created_at_utc": datetime.now(UTC).isoformat(),
            "run_id": cfg.run_id,
            "run_status": "completed",
            "G4": "failed"
            if sources["status"] == "failed" or not all(technical.values())
            else "pending",
            "scientific_review": "not_requested",
            "interpretation_allowed": False,
            "config": {key: str(value) for key, value in asdict(cfg).items()},
            "profile_manifest_status": profile["status"],
            "profile_id": profile["profile_id"],
            "source_checks": sources,
            "technical_checks": technical,
            "source_archive_verification": sources["source_archive_verification"],
            "deterministic_tests": "not_run_by_runner",
            "latent_flow_conservation": "not_exposed_by_SimResult; deterministic_tests_required",
            "simulation_parameters": asdict(SimConfig()),
            "simulator_calls": len(replicates) * 3,
            "design_month": _design_month(profile),
            "window": [63, 75],
            "seed_tree": profile["validation"]["seed_tree"],
            "root_seed": 42,
            "replicates_per_noise_label": 64,
            "reserved_root_branches": {"source": 0, "endemic_calibration": 2},
            "git_sha": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], text=True
            ).strip(),
            "versions": {
                "python": platform.python_version(),
                **{
                    name: importlib.metadata.version(name)
                    for name in ("numpy", "scipy", "pandas", "pyarrow")
                },
            },
            "input_sha256": provenance,
            "artifact_sha256": artifacts,
        }
        _write_json(stage / "manifest.json", manifest)
        if any(_sha256(stage / name) != digest for name, digest in artifacts.items()):
            raise ValueError("artifact hash verification failed")
        _summaries(pd.read_parquet(stage / "replicates.parquet"))
        _publish(stage, destination)
    except Exception as error:
        _write_json(
            stage / "failure.json",
            {
                "run_status": "failed",
                "reason": str(error),
                "interpretation_allowed": False,
                "G4": "failed",
            },
        )
        raise
    return destination


def main() -> int:
    """Run fixed diagnostics; exit nonzero while scientific review is outstanding."""
    if len(sys.argv) != 2:
        print("usage: python -m headd_l0.sim_validation CONFIG.toml", file=sys.stderr)
        return 2
    try:
        output = run_validation(Path(sys.argv[1]))
        manifest = json.loads((output / "manifest.json").read_text())
    except (OSError, ValueError, KeyError, RuntimeError) as error:
        print(f"G4 evidence error: {error}", file=sys.stderr)
        return 2
    print(
        f"Published {output}; G4={manifest['G4']}; scientific review not requested; interpretation_allowed=false",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
