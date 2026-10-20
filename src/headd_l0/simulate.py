"""Gao equations and the P5 single-region adaptation; G4 remains pending."""

from copy import deepcopy
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from scipy.stats import binom

_PROFILE_ID = "P5-IMPL-2026-10-19-v1"
# Fixed implementation conventions, not fitted epidemiological parameters.
_MONTHLY = {
    "start": "2009-01-01",
    "end_exclusive": "2020-01-01",
    "months": 132,
    "population": 100000.0,
    "initial_infected": 7.0,
    "recovery": 1 / 14,
    "mortality": 1 / 365,
    "burn_in_days": 365,
    "max_step_days": 7,
    "R0_start": 0.8,
    "R0_end_T": 1.6,
    "ramp_start_day": 313 * 7,
    "ramp_end_day": 365 * 7,
    "endemic_hazard": 1e-6,
    "seasonal_amplitude": 0.1,
    "seasonal_period_days": 365.25,
    "white_sigma": (1.0, 1.0),
    "env_sigma": (0.01, 0.01),
    "seed_region": 0,
    "epsilon": 0.0,
}
_ORIGIN = np.datetime64(_MONTHLY["start"], "D")
_MONTH_EDGES = (
    np.arange("2009-01", "2020-02", dtype="datetime64[M]").astype("datetime64[D]")
    - _ORIGIN
).astype(int)


@dataclass(frozen=True)
class SimConfig:
    """Select a noise, scenario and observation rate within the fixed P5 profile."""

    profile_id: str = _PROFILE_ID
    noise: Literal["white", "env", "dem"] = "white"
    label: Literal["T", "N"] = "T"
    testing_rate: float = 0.5

    def __post_init__(self) -> None:
        if (
            self.profile_id != _PROFILE_ID
            or self.noise not in ("white", "env", "dem")
            or self.label not in ("T", "N")
            or not 0 <= self.testing_rate <= 1
        ):
            raise ValueError("invalid P5 simulation configuration")


@dataclass(frozen=True)
class SimResult:
    """Monthly observed counts, common-noise twin, onsets and provenance."""

    counts: np.ndarray
    twin_counts: np.ndarray
    onset: np.ndarray
    seed_region: int
    label: Literal["T", "N"]
    params: dict


def _coefficients(
    state: np.ndarray,
    flow: np.ndarray,
    *,
    noise: str,
    sigma: np.ndarray,
    recruitment: float,
    recovery: float,
    mortality: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Evaluate supplement equations 1–3 at one shared left endpoint."""
    susceptible, infected = state[..., 0], state[..., 1]
    removal = (recovery + mortality) * infected
    drift = np.stack(
        (recruitment - flow - mortality * susceptible, flow - removal), axis=-1
    )
    diffusion = np.zeros((*state.shape, 2))
    if noise == "dem":
        a, c = recruitment + flow + mortality * susceptible, flow + removal
        root = np.sqrt(np.maximum(a * c - flow * flow, 0))
        denominator = np.sqrt(a + c + 2 * root)[..., None, None]
        diffusion[..., 0, 0], diffusion[..., 1, 1] = a + root, c + root
        diffusion[..., 0, 1] = diffusion[..., 1, 0] = -flow
        np.divide(diffusion, denominator, out=diffusion, where=denominator > 0)
    else:
        amplitude = np.asarray(sigma) * (state if noise == "env" else 1)
        diffusion[..., 0, 0] = amplitude[..., 0]
        diffusion[..., 1, 1] = amplitude[..., 1]
    return drift, diffusion


def _step(
    state: np.ndarray,
    flow: np.ndarray,
    dt: float,
    gaussian: np.ndarray,
    **coefficients,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Advance simultaneously, returning latent incidence and projection flags."""
    drift, diffusion = _coefficients(state, flow, **coefficients)
    proposed = (
        state
        + drift * dt
        + np.einsum("...ij,...j->...i", diffusion, gaussian) * np.sqrt(dt)
    )
    return np.maximum(proposed, 0), np.maximum(flow, 0) * dt, proposed < 0


def _calendar(start: int, end: int) -> np.ndarray:
    """Return day offsets splitting at origin-anchored weeks and every month."""
    first_month = (_ORIGIN + np.timedelta64(start, "D")).astype("datetime64[M]")
    last_month = (_ORIGIN + np.timedelta64(end, "D")).astype("datetime64[M]")
    months = (
        np.arange(
            first_month, last_month + np.timedelta64(1, "M"), dtype="datetime64[M]"
        ).astype("datetime64[D]")
        - _ORIGIN
    ).astype(int)
    week = _MONTHLY["max_step_days"]
    weeks = np.arange((start // week + 1) * week, end, week)
    return np.unique(
        np.r_[start, weeks, months[(months > start) & (months < end)], end]
    )


def _integrate(
    cfg: SimConfig,
    times: np.ndarray,
    state: np.ndarray,
    gaussian: np.ndarray,
    label: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Accumulate left-endpoint flows by month; negative times are burn-in."""
    p = _MONTHLY
    latent = np.zeros((p["months"], len(state)))
    clipped = np.zeros_like(state, dtype=int)
    sigma = p["env_sigma"] if cfg.noise == "env" else p["white_sigma"]
    for t, dt, innovation in zip(times[:-1], np.diff(times), gaussian, strict=True):
        ramp = (
            np.clip(
                (t - p["ramp_start_day"]) / (p["ramp_end_day"] - p["ramp_start_day"]),
                0,
                1,
            )
            if label == "T"
            else 0
        )
        beta = (p["R0_start"] + (p["R0_end_T"] - p["R0_start"]) * ramp) * (
            p["recovery"] + p["mortality"]
        )
        endemic = p["endemic_hazard"] * (
            1
            + p["seasonal_amplitude"]
            * np.cos(2 * np.pi * t / p["seasonal_period_days"])
        )
        flow = (beta * state[:, 1] / p["population"] + endemic) * state[:, 0]
        state, incidence, projected = _step(
            state,
            flow,
            dt,
            innovation,
            noise=cfg.noise,
            sigma=sigma,
            recruitment=p["mortality"] * p["population"],
            recovery=p["recovery"],
            mortality=p["mortality"],
        )
        clipped += projected
        if t >= 0:
            latent[np.searchsorted(_MONTH_EDGES, t, side="right") - 1] += incidence
    return latent, state, clipped


def _observe(latent: np.ndarray, uniforms: np.ndarray, theta: float) -> np.ndarray:
    """Round each monthly total once, then apply a shared binomial quantile."""
    floor = np.floor(latent)
    trials = (floor + (uniforms[..., 0] < latent - floor)).astype(np.int64)
    if theta == 0:
        return np.zeros_like(trials)
    if theta == 1:
        return trials
    quantiles = np.maximum(uniforms[..., 1], np.nextafter(0.0, 1.0))
    return binom.ppf(quantiles, trials, theta).astype(np.int64)


def simulate(cfg: SimConfig, W: np.ndarray, rng: np.random.Generator) -> SimResult:
    """Simulate one outbreak/null replicate under the approved technical profile.

    Args:
        cfg: Frozen profile selector; theta extremes support observation checks.
        W: One-region adjacency weights, shape [1, 1]; epsilon is fixed at zero.
            Coupled simulation is not implemented yet.
        rng: Caller-owned Generator, normally from SeedSequence(root).spawn(n).

    Returns:
        Frozen result with [1, 132] integer counts, [1] zero-based onset (-1
        for N), paired null counts, profile values and projection diagnostics.
        Scientific ratification and G4 remain pending.
    """
    weights = np.asarray(W, dtype=float)
    if weights.shape != (1, 1) or not np.isfinite(weights).all() or (weights < 0).any():
        raise ValueError("single-region validation requires finite nonnegative 1x1 W")
    if not isinstance(rng, np.random.Generator):
        raise TypeError("rng must be a numpy.random.Generator")
    p = _MONTHLY
    regions = len(weights)
    burn_times = _calendar(-p["burn_in_days"], 0)
    times = _calendar(0, int(_MONTH_EDGES[-1]))
    rng_state = deepcopy(rng.bit_generator.state)
    # All draws precede integration: neither branching nor clipping consumes RNG.
    burn_noise = rng.standard_normal((len(burn_times) - 1, regions, 2))
    noise = rng.standard_normal((len(times) - 1, regions, 2))
    uniforms = rng.random((p["months"], regions, 2))
    state = np.tile(
        [p["population"] - p["initial_infected"], p["initial_infected"]], (regions, 1)
    )
    _, state, burn_clip = _integrate(cfg, burn_times, state, burn_noise, "N")
    latent, _, clip = _integrate(cfg, times, state, noise, cfg.label)
    twin_latent, _, twin_clip = _integrate(cfg, times, state, noise, "N")
    onset = np.full(regions, -1, dtype=int)
    if cfg.label == "T":
        crossing = p["ramp_start_day"] + (1 - p["R0_start"]) / (
            p["R0_end_T"] - p["R0_start"]
        ) * (p["ramp_end_day"] - p["ramp_start_day"])
        onset[p["seed_region"]] = (
            np.searchsorted(_MONTH_EDGES, crossing, side="right") - 1
        )
    projection = {}
    for name, counts, steps in (
        ("burn_in", burn_clip, len(burn_times) - 1),
        ("outbreak", clip, len(times) - 1),
        ("twin", twin_clip, len(times) - 1),
    ):
        projection[name] = {
            "clipped_coordinates": counts.tolist(),
            "steps": steps,
            "fraction": float(counts.sum() / (steps * regions * 2)),
        }
    params = {
        **asdict(cfg),
        "monthly_profile": p.copy(),
        "rng_initial_state": rng_state,
        "projection": projection,
        "scientific_ratification": "pending",
        "G4": "pending",
        "interpretation_allowed": False,
    }
    return SimResult(
        _observe(latent, uniforms, cfg.testing_rate).T,
        _observe(twin_latent, uniforms, cfg.testing_rate).T,
        onset,
        p["seed_region"],
        cfg.label,
        params,
    )
