"""Equation parity and the frozen P5 single-region monthly adaptation."""

import json
import tomllib
from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import numpy as np
import pytest

REFERENCE = Path(__file__).parent / "reference"
MANIFEST = json.loads((REFERENCE / "gao_manifest.json").read_text())


def _fixture():
    path = REFERENCE / "gao_single.npz"
    assert sha256(path.read_bytes()).hexdigest() == MANIFEST["fixture"]["sha256"]
    with np.load(path, allow_pickle=False) as archive:
        arrays = dict(archive)
    assert set(arrays) == set(MANIFEST["fixture"]["shapes"])
    for name, shape in MANIFEST["fixture"]["shapes"].items():
        assert arrays[name].shape == tuple(shape), name
        if name not in {"profile_id", "noise", "label"}:
            assert arrays[name].dtype == np.float64, name
    assert arrays["profile_id"].item() == MANIFEST["profile_id"]
    assert list(zip(arrays["noise"], arrays["label"], strict=True)) == [
        ("white", "T"),
        ("white", "N"),
        ("env", "T"),
        ("env", "N"),
        ("dem", "T"),
        ("dem", "N"),
    ]
    return arrays


def test_equation_fixture_contract():
    arrays = _fixture()
    np.testing.assert_allclose(
        arrays["expected_state"],
        MANIFEST["fixture"]["expected_state"],
        rtol=0,
        atol=1e-10,
    )


@pytest.mark.parametrize("row", range(6))
def test_one_step_matches_independent_decimal_fixture(row):
    from headd_l0.simulate import _coefficients, _step

    fixture = _fixture()
    state = fixture["state"][row]
    flow = fixture["beta"][row] * state[0] * state[1]
    arguments = {
        "noise": str(fixture["noise"][row]),
        "sigma": fixture["sigma"][row],
        "recruitment": fixture["recruitment"][row],
        "recovery": fixture["recovery"][row],
        "mortality": fixture["mortality"][row],
    }
    drift, diffusion = _coefficients(state, flow, **arguments)
    output, incidence, clipped = _step(
        state, flow, fixture["dt"][row], fixture["gaussian"][row], **arguments
    )
    for actual, key in [
        (drift, "expected_drift"),
        (diffusion, "expected_diffusion"),
        (output, "expected_state"),
        (incidence, "expected_incidence"),
    ]:
        np.testing.assert_allclose(actual, fixture[key][row], rtol=0, atol=1e-10)
    assert not clipped.any()
    np.testing.assert_array_equal(state, [500, 7])


def test_demographic_covariance_has_no_sigma_multiplier_and_handles_zero():
    from headd_l0.simulate import _coefficients

    arguments = {"noise": "dem", "recruitment": 100, "recovery": 1, "mortality": 1}
    _, diffusion = _coefficients(
        np.array([500.0, 7.0]), 52.5, sigma=[99, 0], **arguments
    )
    np.testing.assert_allclose(
        diffusion @ diffusion.T, [[652.5, -52.5], [-52.5, 66.5]], rtol=0, atol=1e-10
    )
    assert (np.linalg.eigvalsh(diffusion) >= 0).all()
    drift, diffusion = _coefficients(
        np.zeros(2),
        0,
        noise="dem",
        sigma=[99, 0],
        recruitment=0,
        recovery=1,
        mortality=1,
    )
    np.testing.assert_array_equal(drift, [0, 0])
    np.testing.assert_array_equal(diffusion, np.zeros((2, 2)))


def test_projection_clips_only_negative_coordinates_without_reset_or_upper_bound():
    from headd_l0.simulate import _step

    output, incidence, clipped = _step(
        np.array([2.0, 3.0]),
        0.0,
        4.0,
        np.array([-2.0, 100.0]),
        noise="white",
        sigma=[1, 1],
        recruitment=0,
        recovery=0,
        mortality=0,
    )
    np.testing.assert_array_equal(output, [0, 203])
    np.testing.assert_array_equal(clipped, [True, False])
    assert incidence == 0


@pytest.mark.parametrize(
    "change",
    [
        {"noise": "pink"},
        {"label": "outbreak"},
        {"profile_id": "unapproved"},
        {"testing_rate": -0.1},
        {"testing_rate": 1.1},
        {"testing_rate": np.nan},
    ],
)
def test_invalid_configuration_fails(change):
    from headd_l0.simulate import SimConfig

    with pytest.raises(ValueError):
        SimConfig(**change)


def test_config_is_frozen_and_toml_runs_the_named_profile():
    from headd_l0.simulate import SimConfig, simulate

    document = tomllib.loads(
        (Path(__file__).parents[1] / "configs/simulation.toml").read_text()
    )
    cfg = SimConfig(**document["simulation"])
    with pytest.raises(FrozenInstanceError):
        cfg.noise = "env"
    result = simulate(cfg, np.zeros((1, 1)), np.random.default_rng(42))
    assert result.params["profile_id"] == MANIFEST["profile_id"]
    assert result.params["scientific_ratification"] == "pending"
    assert result.params["G4"] == "pending"
    assert result.params["interpretation_allowed"] is False


def test_calendar_splits_at_month_and_start_anchored_week_boundaries():
    from headd_l0.simulate import _calendar

    times = _calendar(0, 4017)
    np.testing.assert_array_equal(times[:7], [0, 7, 14, 21, 28, 31, 35])
    assert times[-1] == 4017
    assert (np.diff(times) > 0).all()
    assert (np.diff(times) <= 7).all()
    dates = np.datetime64("2009-01-01") + times.astype("timedelta64[D]")
    starts = np.arange("2009-01", "2020-02", dtype="datetime64[M]").astype(
        "datetime64[D]"
    )
    assert np.isin(starts, dates).all()
    assert np.isin(np.arange(0, 4018, 7), times).all()
    month = np.searchsorted(starts, dates[:-1], side="right") - 1
    days = np.bincount(month, weights=np.diff(times), minlength=132)
    np.testing.assert_array_equal(days, np.diff(starts).astype(int))
    assert days[37] == 29  # February 2012, not a 28-day approximation.
    assert days[85] == 29  # February 2016.
    burn_in = _calendar(-365, 0)
    assert tuple(burn_in[:2]) == (-365, -364)
    assert burn_in[-1] == 0
    assert np.diff(burn_in).sum() == 365


@pytest.mark.parametrize(
    "theta, expected", [(0, [0, 0, 0, 0]), (0.5, [1, 2, 2, 1]), (1, [2, 3, 3, 2])]
)
def test_monthly_integerization_and_binomial_quantiles(theta, expected):
    from headd_l0.simulate import _observe

    # At theta=.5, n=2 has CDF (.25,.75,1); n=3 has (.125,.5,.875,1).
    latent = np.array([2.25, 2.25, 2.75, 2.75])
    uniforms = np.array([[0.3, 0.5], [0.2, 0.6], [0.7, 0.8], [0.8, 0.6]])
    np.testing.assert_array_equal(_observe(latent, uniforms, theta), expected)


def test_integerization_is_once_after_summing_partial_interval_flows():
    from headd_l0.simulate import SimConfig, _integrate, _observe

    # No innovations; three left-endpoint flows at t=0,1,2 are hand-computed.
    latent, state, clipped = _integrate(
        SimConfig(),
        np.array([0, 1, 2, 3]),
        np.array([[99993.0, 7.0]]),
        np.zeros((3, 1, 2)),
        "N",
    )
    np.testing.assert_allclose(latent[0, 0], 1.5769867201638062, rtol=0, atol=1e-10)
    assert np.count_nonzero(latent) == 1
    assert not clipped.any()
    assert state.shape == (1, 2)
    uniforms = np.full((132, 1, 2), 0.7)
    # Rounding each of the three <1 flows at .7 would give zero, incorrectly.
    assert _observe(latent, uniforms, 1)[0, 0] == 1


@pytest.mark.parametrize("noise", ["white", "env", "dem"])
@pytest.mark.parametrize("label", ["T", "N"])
def test_single_region_result_is_reproducible_and_twin_uses_common_draws(noise, label):
    from headd_l0.simulate import SimConfig, SimResult, simulate

    cfg = SimConfig(noise=noise, label=label)
    rng = np.random.default_rng(np.random.SeedSequence(42).spawn(1)[0])
    again_rng = np.random.default_rng(np.random.SeedSequence(42).spawn(1)[0])
    result = simulate(cfg, np.zeros((1, 1)), rng)
    again = simulate(cfg, np.zeros((1, 1)), again_rng)
    assert isinstance(result, SimResult)
    assert result.counts.shape == result.twin_counts.shape == (1, 132)
    assert result.onset.shape == (1,)
    assert result.seed_region == 0
    assert result.label == label
    assert result.onset[0] == (75 if label == "T" else -1)
    assert np.issubdtype(result.counts.dtype, np.integer)
    assert (result.counts >= 0).all()
    assert (result.twin_counts >= 0).all()
    np.testing.assert_array_equal(result.counts, again.counts)
    np.testing.assert_array_equal(result.twin_counts, again.twin_counts)
    assert rng.bit_generator.state == again_rng.bit_generator.state
    # Before the ramp begins in January 2015, T and twin must be identical.
    np.testing.assert_array_equal(result.counts[:, :72], result.twin_counts[:, :72])
    if label == "N":
        np.testing.assert_array_equal(result.counts, result.twin_counts)
    else:
        assert not np.array_equal(result.counts, result.twin_counts)
    with pytest.raises(FrozenInstanceError):
        result.label = "N"
    for phase in ("burn_in", "outbreak", "twin"):
        diagnostics = result.params["projection"][phase]
        clipped = np.asarray(diagnostics["clipped_coordinates"])
        assert clipped.shape == (1, 2)
        assert np.issubdtype(clipped.dtype, np.integer)
        assert (clipped >= 0).all()
        assert diagnostics["fraction"] == clipped.sum() / (2 * diagnostics["steps"])


def test_rng_consumption_is_fixed_across_noise_label_and_testing_rate():
    from headd_l0.simulate import SimConfig, simulate

    final_states = []
    outputs = []
    for noise, label, theta in [("white", "T", 0), ("env", "N", 1), ("dem", "T", 0.5)]:
        rng = np.random.default_rng(77)
        outputs.append(
            simulate(
                SimConfig(noise=noise, label=label, testing_rate=theta),
                np.ones((1, 1)),
                rng,
            )
        )
        final_states.append(rng.bit_generator.state)
    assert final_states[0] == final_states[1] == final_states[2]
    assert not outputs[0].counts.any()
    assert not outputs[0].twin_counts.any()
    assert outputs[1].counts.any()


def test_different_seeds_produce_different_replicates():
    from headd_l0.simulate import SimConfig, simulate

    seeds = np.random.SeedSequence(42).spawn(2)
    results = [
        simulate(SimConfig(), np.zeros((1, 1)), np.random.default_rng(seed))
        for seed in seeds
    ]
    assert not np.array_equal(results[0].counts, results[1].counts)


@pytest.mark.parametrize(
    "weights", [np.zeros((13, 13)), np.array([[np.nan]]), np.array([[-1]])]
)
def test_single_region_scope_rejects_invalid_weights(weights):
    from headd_l0.simulate import SimConfig, simulate

    with pytest.raises(ValueError):
        simulate(SimConfig(), weights, np.random.default_rng(42))


def test_generator_is_required():
    from headd_l0.simulate import SimConfig, simulate

    with pytest.raises(TypeError):
        simulate(SimConfig(), np.zeros((1, 1)), 42)
