"""E1 configuration and shared per-replicate computation; run owns orchestration."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from headd_l0.data import hierarchy
from headd_l0.detectors import DETECTORS, DetectorConfig
from headd_l0.features import FEATURES
from headd_l0.forecast import fit_nb2, forecast_mean
from headd_l0.graph import adjacency, placebos, row_normalize
from headd_l0.reconcile import fit_mint, reconcile, standardize, summing_matrix
from headd_l0.select import SELECTORS, SelectionConfig
from headd_l0.simulate import SimConfig, simulate
from headd_l0.threshold import THRESHOLDS


@dataclass(frozen=True)
class ExperimentConfig:
    """Explicit synthetic design; loading never simulates or reads derived inputs."""

    name: str
    run_id: str
    root_seed: int
    output_dir: Path
    noise_types: tuple[str, ...]
    epsilon_levels: tuple[float, ...]
    n_transition: int
    n_null: int
    n_calibration: int
    n_placebos: int
    detectors: tuple[str, ...]
    selection_k: int
    graph_source: str
    endemic_source: str
    calibration_dirs: tuple[str, ...] = ()
    train_months: int = 60
    window: int = 12
    target_far: float = 1 / 60
    far_tolerance: float = 1 / 300
    reconciliation: str = "mint_shrink"
    selector: str = "meta_des"
    threshold: str = "evt_gpd"
    baseline_id: str = "B1*"
    n_placebo_transition_per_cell: int | None = None

    def __post_init__(self) -> None:
        for key in ("noise_types", "epsilon_levels", "detectors", "calibration_dirs"):
            object.__setattr__(self, key, tuple(getattr(self, key)))
        if (
            self.name not in ("e1_smoke", "e1_bench")
            or type(self.root_seed) is not int
            or self.root_seed < 0
            or not isinstance(self.run_id, str)
            or not self.run_id.strip()
            or Path(self.run_id).name != self.run_id
            or self.run_id in (".", "..")
            or "\\" in self.run_id
            or not isinstance(self.output_dir, (str, Path))
            or not str(self.output_dir).strip()
            or not self.noise_types
            or not set(self.noise_types) <= {"white", "env", "dem"}
            or not self.epsilon_levels
            or not set(self.epsilon_levels) <= {0, 0.05, 0.2}
            or len(set(self.noise_types)) != len(self.noise_types)
            or len(set(self.epsilon_levels)) != len(self.epsilon_levels)
            or any(
                type(n) is not int or n < 1
                for n in (
                    self.n_transition,
                    self.n_null,
                    self.n_calibration,
                    self.n_placebos,
                    self.selection_k,
                )
            )
            or self.n_placebos != 30
            or (
                self.n_placebo_transition_per_cell is not None
                and (
                    type(self.n_placebo_transition_per_cell) is not int
                    or not 1 <= self.n_placebo_transition_per_cell <= self.n_transition
                )
            )
            or not self.detectors
            or not set(self.detectors) <= DETECTORS.keys()
            or len(set(self.detectors)) != len(self.detectors)
            or self.selection_k > len(self.detectors)
            or self.reconciliation != "mint_shrink"
            or self.selector not in SELECTORS
            or self.threshold not in THRESHOLDS
            or self.baseline_id != "B1*"
            or (self.train_months, self.window) != (60, 12)
            or (self.target_far, self.far_tolerance) != (1 / 60, 1 / 300)
        ):
            raise ValueError("invalid E1 configuration")
        expected = (
            ("synthetic_cycle_smoke_only", "fixed_profile_smoke_only")
            if self.name == "e1_smoke"
            else ("queen_cache", "calibrated")
        )
        if (self.graph_source, self.endemic_source) != expected:
            raise ValueError("invalid graph or endemic source for this execution")
        if self.name == "e1_bench" and len(self.calibration_dirs) != len(
            self.noise_types
        ):
            raise ValueError("bench requires one calibration directory per noise")
        object.__setattr__(self, "output_dir", Path(self.output_dir).expanduser())


@dataclass(frozen=True)
class ArmSpec:
    """Only residual representation and relational graph vary between arms."""

    name: str
    residuals: str
    graph_id: str | None


@dataclass(frozen=True)
class RunResult:
    """Artifact directory, technical execution status and evaluation outcomes."""

    path: Path
    status: str
    metrics: pd.DataFrame


def build_arms(n_placebos: int) -> tuple[ArmSpec, ...]:
    """Build the independent floor, corrected baseline and all relational arms."""
    if type(n_placebos) is not int or n_placebos != 30:
        raise ValueError("E1 requires 30 placebo arms")
    return (
        ArmSpec("B0", "base", None),
        ArmSpec("B1*", "reconciled", None),
        ArmSpec("B2", "reconciled", "observed"),
        *(
            ArmSpec(f"B2-placebo-{i:02d}", "reconciled", f"placebo-{i:02d}")
            for i in range(n_placebos)
        ),
    )


def arms_for_replicate(
    cfg: ExperimentConfig,
    arms: tuple[ArmSpec, ...],
    partition: str,
    label: str,
    index: int,
) -> tuple[ArmSpec, ...]:
    """Return arms scored for this address in the approved transition subset."""
    limit = cfg.n_placebo_transition_per_cell
    if limit is None or partition != "evaluation" or label != "T" or index < limit:
        return arms
    return tuple(arm for arm in arms if arm.name in {"B0", "B1*", "B2"})


def _digest(array):
    return hashlib.sha256(np.ascontiguousarray(array).tobytes()).hexdigest()


def _child(seed, *key):
    # Fixed addresses under the six root children; independent of loop/arm order.
    return np.random.SeedSequence(seed.entropy, spawn_key=(*seed.spawn_key, *key))


def _seed_record(seed):
    return {"entropy": seed.entropy, "spawn_key": list(seed.spawn_key)}


def _inputs(cfg, seed):
    if cfg.graph_source == "synthetic_cycle_smoke_only":
        A = np.zeros((13, 13), dtype=np.uint8)
        for i in range(13):
            A[i, (i + 1) % 13] = A[(i + 1) % 13, i] = 1
    else:
        A, _ = adjacency()
    graphs = {
        "observed": A,
        **{
            f"placebo-{i:02d}": graph
            for i, graph in enumerate(
                placebos(A, cfg.n_placebos, np.random.default_rng(seed))
            )
        },
    }
    hazards, provenance = {}, {}
    for noise, directory in zip(cfg.noise_types, cfg.calibration_dirs, strict=False):
        path = Path(directory)
        manifest = json.loads((path / "manifest.json").read_text())
        artifact = path / "endemic_calibration.npz"
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        if (
            manifest["status"] != "ready"
            or manifest["config"]["noise"] != noise
            or manifest["config"]["profile_id"] != SimConfig().profile_id
            or manifest["artifact_sha256"][artifact.name] != digest
        ):
            raise ValueError("invalid endemic calibration provenance")
        with np.load(artifact, allow_pickle=False) as saved:
            if tuple(saved["names"]) != hierarchy().leaves:
                raise ValueError("calibration names must be canonical")
            hazards[noise] = tuple(saved["hazards"].tolist())
        provenance[noise] = {
            "artifact_sha256": digest,
            "manifest_sha256": hashlib.sha256(
                (path / "manifest.json").read_bytes()
            ).hexdigest(),
        }
    return graphs, hazards, provenance


def _replicates(cfg, weights, streams, hazards):
    for noise in ("white", "env", "dem"):
        if noise not in cfg.noise_types:
            continue
        for epsilon in (0.0, 0.05, 0.2):
            if epsilon not in cfg.epsilon_levels:
                continue
            cell = ("white", "env", "dem").index(noise) * 3 + (0.0, 0.05, 0.2).index(
                epsilon
            )
            for partition, label, n in (
                ("calibration", "N", cfg.n_calibration),
                ("evaluation", "T", cfg.n_transition),
                ("evaluation", "N", cfg.n_null),
            ):
                for i in range(n):
                    address = (cell, int(label == "N"), i)
                    seed = _child(streams[partition], *address)
                    seed_region = int(
                        np.random.default_rng(
                            _child(streams["data"], *address)
                        ).integers(13)
                    )
                    simulation = SimConfig(
                        noise=noise,
                        label=label,
                        epsilon=epsilon,
                        seed_region=seed_region,
                        endemic_hazard=hazards.get(noise, 1e-6),
                    )
                    result = simulate(simulation, weights, np.random.default_rng(seed))
                    record = {
                        "replicate_id": f"{noise}:{epsilon:g}:{partition}:{label}:{i:04d}",
                        "noise": noise,
                        "epsilon": epsilon,
                        "partition": partition,
                        "label": label,
                        "replicate_index": i,
                        "seed_region": seed_region,
                        **_seed_record(seed),
                        "simulation_params": json.dumps(result.params, sort_keys=True),
                    }
                    detector_seed = _child(
                        streams["detectors"],
                        cell,
                        int(partition == "evaluation"),
                        int(label == "N"),
                        i,
                    )
                    yield record, result, detector_seed


def _score(counts, cfg, arms, graphs, seed, address=None):
    """Fit D5 once, then use identical components/seeds for all representations."""
    active_arms = (
        arms
        if address is None
        else arms_for_replicate(
            cfg,
            arms,
            address["partition"],
            address["label"],
            address["replicate_index"],
        )
    )
    observed = np.vstack((counts.sum(axis=0), counts))
    fit = fit_nb2(observed, cfg.train_months)
    fitted = forecast_mean(fit, np.arange(132))
    scores = np.full((len(active_arms), 13, 72), np.nan)
    shared = {"forecasts": fitted, "coherent_forecasts": np.full_like(fitted, np.nan)}
    valid = bool(
        fit.converged.all()
        and np.isfinite(fitted).all()
        and (fitted > 0).all()
        and np.isfinite(fit.alpha).all()
        and (fit.alpha > 0).all()
    )
    audit = {
        "fit_valid": valid,
        "forecast_converged": fit.converged.tolist(),
        "forecast_alpha": fit.alpha.tolist(),
        "detector_seed": _seed_record(seed),
        "pool_fits": 0,
        "active_arms": [arm.name for arm in active_arms],
    }
    if not valid:
        return scores, shared, audit
    mint = fit_mint(observed, fitted, cfg.train_months)
    coherent = reconcile(
        fitted,
        summing_matrix(hierarchy()),
        cfg.reconciliation,
        covariance=mint.covariance,
    )
    shared["coherent_forecasts"] = coherent
    residuals = {
        "base": standardize(observed - fitted),
        "reconciled": standardize(observed - coherent),
    }
    local = {key: FEATURES["local"](value).values for key, value in residuals.items()}
    cache = {}
    for a, arm in enumerate(active_arms):
        features = local[arm.residuals][1:]
        if arm.graph_id:
            relational = FEATURES["neighbors"](
                residuals["reconciled"][1:],
                row_normalize(graphs[arm.graph_id]),
                cfg.window,
            )
            features = np.concatenate((features, relational.values), axis=-1)
        for j in range(13):
            # Same eligible training prefix for every arm, including Moran warmup.
            X = features[j, cfg.window - 1 :]
            key = (j, _digest(X))
            if key not in cache:
                raw = []
                for name in cfg.detectors:
                    child = _child(seed, j, list(DETECTORS).index(name))
                    detector = DETECTORS[name](
                        DetectorConfig(int(child.generate_state(1)[0]))
                    )
                    detector.fit(X[: cfg.train_months - cfg.window + 1])
                    raw.append(detector.score(X))
                selected = SELECTORS[cfg.selector](
                    np.column_stack(raw),
                    cfg.train_months - cfg.window + 1,
                    SelectionConfig(window=cfg.window, k=cfg.selection_k),
                )
                cache[key] = selected.scores[-72:]
                audit["pool_fits"] += 1
            scores[a, j] = cache[key]
    return scores, shared, audit
