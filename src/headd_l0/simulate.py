"""Gao equations and the P5 metapopulation adaptation; G4 remains pending."""

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
    """Select scenario, coupling and calibrated hazards within the P5 profile."""

    profile_id: str = _PROFILE_ID
    noise: Literal["white", "env", "dem"] = "white"
    label: Literal["T", "N"] = "T"
    testing_rate: float = 0.5
    epsilon: float = 0.0
    seed_region: int = 0
    endemic_hazard: float | tuple[float, ...] = 1e-6

    def __post_init__(self) -> None:
        hazards = np.asarray(self.endemic_hazard, dtype=float)
        if (
            self.profile_id != _PROFILE_ID
            or self.noise not in ("white", "env", "dem")
            or self.label not in ("T", "N")
            or not 0 <= self.testing_rate <= 1
            or not 0 <= self.epsilon <= 1
            or type(self.seed_region) is not int
            or self.seed_region < 0
            or hazards.ndim > 1
            or not hazards.size
            or not np.isfinite(hazards).all()
            or (hazards < 0).any()
        ):
            raise ValueError("invalid P5 simulation configuration")
        if hazards.ndim:
            object.__setattr__(self, "endemic_hazard", tuple(hazards.tolist()))


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
    weights: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Accumulate left-endpoint flows by month; negative times are burn-in."""
    p = _MONTHLY
    latent = np.zeros((p["months"], len(state)))
    clipped = np.zeros_like(state, dtype=int)
    sigma = p["env_sigma"] if cfg.noise == "env" else p["white_sigma"]
    coupling = (
        (1 - cfg.epsilon) * np.eye(len(state)) + cfg.epsilon * weights
        if cfg.epsilon
        else None
    )
    hazard = np.asarray(cfg.endemic_hazard)
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
        r0 = np.full(len(state), p["R0_start"])
        r0[cfg.seed_region] += (p["R0_end_T"] - p["R0_start"]) * ramp
        beta = r0 * (p["recovery"] + p["mortality"])
        endemic = hazard * (
            1
            + p["seasonal_amplitude"]
            * np.cos(2 * np.pi * t / p["seasonal_period_days"])
        )
        # Preserve the reviewed single-region arithmetic exactly at epsilon=0.
        pressure = (
            beta * state[:, 1] / p["population"]
            if coupling is None
            else beta * (coupling @ (state[:, 1] / p["population"]))
        )
        flow = (pressure + endemic) * state[:, 0]
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


def _onsets(counts: np.ndarray, twin: np.ndarray, cfg: SimConfig) -> np.ndarray:
    """Locate continuous seed crossing and strict frozen-training exceedances."""
    onset = np.full(len(counts), -1, dtype=int)
    if cfg.label == "N":
        return onset
    exceed = counts - twin > 2 * np.std(twin[:, :60], axis=1, ddof=1)[:, None]
    reached = exceed.any(axis=1)
    onset[reached] = exceed[reached].argmax(axis=1)
    p = _MONTHLY
    crossing = p["ramp_start_day"] + (1 - p["R0_start"]) / (
        p["R0_end_T"] - p["R0_start"]
    ) * (p["ramp_end_day"] - p["ramp_start_day"])
    onset[cfg.seed_region] = np.searchsorted(_MONTH_EDGES, crossing, side="right") - 1
    return onset


def simulate(cfg: SimConfig, W: np.ndarray, rng: np.random.Generator) -> SimResult:
    """Simulate one outbreak/null replicate under the approved technical profile.

    Args:
        cfg: Frozen profile selector; theta extremes support observation checks.
        W: Finite nonnegative row-normalized weights [regions, regions].
            The original one-region epsilon=0 check also accepts W=[[0]].
        rng: Caller-owned Generator, normally from SeedSequence(root).spawn(n).

    Returns:
        Frozen result with [regions, 132] integer counts, zero-based onsets (-1
        for N), paired null counts, profile values and projection diagnostics.
        Scientific ratification and G4 remain pending.
    """
    weights = np.asarray(W, dtype=float)
    if (
        weights.ndim != 2
        or not len(weights)
        or weights.shape[0] != weights.shape[1]
        or not np.isfinite(weights).all()
        or (weights < 0).any()
    ):
        raise ValueError("W must be finite, nonnegative and square")
    if (len(weights) > 1 or cfg.epsilon) and not np.allclose(
        weights.sum(axis=1), 1, rtol=0, atol=1e-12
    ):
        raise ValueError("W must be row-normalized")
    if cfg.seed_region >= len(weights) or np.shape(cfg.endemic_hazard) not in (
        (),
        (len(weights),),
    ):
        raise ValueError("seed_region and endemic_hazard must match W")
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
    _, state, burn_clip = _integrate(cfg, burn_times, state, burn_noise, "N", weights)
    latent, _, clip = _integrate(cfg, times, state, noise, cfg.label, weights)
    twin_latent, _, twin_clip = _integrate(cfg, times, state, noise, "N", weights)
    counts = _observe(latent, uniforms, cfg.testing_rate).T
    twin_counts = _observe(twin_latent, uniforms, cfg.testing_rate).T
    projection = {}
    for name, clipped, steps in (
        ("burn_in", burn_clip, len(burn_times) - 1),
        ("outbreak", clip, len(times) - 1),
        ("twin", twin_clip, len(times) - 1),
    ):
        projection[name] = {
            "clipped_coordinates": clipped.tolist(),
            "steps": steps,
            "fraction": float(clipped.sum() / (steps * regions * 2)),
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
        counts,
        twin_counts,
        _onsets(counts, twin_counts, cfg),
        cfg.seed_region,
        cfg.label,
        params,
    )
