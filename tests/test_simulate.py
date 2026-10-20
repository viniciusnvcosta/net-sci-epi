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


def _ring_weights():
    weights = np.zeros((13, 13))
    for i in range(13):
        weights[i, (i - 1) % 13] = weights[i, (i + 1) % 13] = 0.5
    return weights


def test_thirteen_region_shape_comes_from_weights():
    from headd_l0.simulate import SimConfig, simulate

    result = simulate(SimConfig(), _ring_weights(), np.random.default_rng(42))
    assert result.counts.shape == result.twin_counts.shape == (13, 132)
    assert result.onset.shape == (13,)
    assert np.issubdtype(result.counts.dtype, np.integer)
    assert (result.counts >= 0).all()
    assert (result.twin_counts >= 0).all()


@pytest.mark.parametrize("epsilon", [0, 0.2, 1])
def test_coupled_flow_uses_receiver_beta_and_row_weights(epsilon):
    from headd_l0.simulate import SimConfig, _integrate

    # At day 2555, only seed 1 has R0=1.6; all other R0 values remain 0.8.
    # Unequal directed weights catch transposing W or applying the sender's beta.
    weights = np.array([[0, 1, 0], [0.25, 0, 0.75], [1, 0, 0]])
    cfg = SimConfig(epsilon=epsilon, seed_region=1, endemic_hazard=0)
    latent, _, _ = _integrate(
        cfg,
        np.array([2555, 2556]),
        np.array([[90000.0, 10.0], [80000.0, 30.0], [70000.0, 50.0]]),
        np.zeros((1, 3, 2)),
        "T",
        weights,
    )
    expected = np.array(
        [
            0.8 * (1 / 14 + 1 / 365) * (10 + 20 * epsilon) * 0.9,
            1.6 * (1 / 14 + 1 / 365) * (30 + 10 * epsilon) * 0.8,
            0.8 * (1 / 14 + 1 / 365) * (50 - 40 * epsilon) * 0.7,
        ]
    )
    np.testing.assert_allclose(latent.sum(axis=0), expected, rtol=0, atol=1e-12)


@pytest.mark.parametrize("noise", ["white", "env", "dem"])
def test_zero_coupling_has_exactly_no_remote_excess(noise):
    from headd_l0.simulate import SimConfig, simulate

    result = simulate(
        SimConfig(noise=noise, epsilon=0, seed_region=5),
        _ring_weights(),
        np.random.default_rng(42),
    )
    remote = np.arange(13) != 5
    np.testing.assert_array_equal(result.counts[remote], result.twin_counts[remote])
    np.testing.assert_array_equal(result.onset[remote], -1)
    assert result.onset[5] == 75
    assert result.seed_region == 5
    assert not np.array_equal(result.counts[5], result.twin_counts[5])


@pytest.mark.parametrize("noise", ["white", "env", "dem"])
def test_coupled_twin_matches_separate_null_with_the_same_fixed_draws(noise):
    from headd_l0.simulate import SimConfig, simulate

    generators = [
        np.random.default_rng(np.random.SeedSequence(71).spawn(1)[0]) for _ in range(3)
    ]
    cfg = SimConfig(noise=noise, epsilon=0.2)
    result = simulate(cfg, _ring_weights(), generators[0])
    repeated = simulate(cfg, _ring_weights(), generators[1])
    null = simulate(
        SimConfig(noise=noise, epsilon=0.2, label="N"),
        _ring_weights(),
        generators[2],
    )
    np.testing.assert_array_equal(result.counts, repeated.counts)
    np.testing.assert_array_equal(result.onset, repeated.onset)
    np.testing.assert_array_equal(result.twin_counts, null.counts)
    np.testing.assert_array_equal(null.counts, null.twin_counts)
    np.testing.assert_array_equal(null.onset, -1)
    np.testing.assert_array_equal(result.counts[:, :72], result.twin_counts[:, :72])
    assert all(
        generators[0].bit_generator.state == rng.bit_generator.state
        for rng in generators[1:]
    )
    assert np.any(result.counts[1:] != result.twin_counts[1:])
    for i in range(1, 13):
        exceedances = np.flatnonzero(
            result.counts[i] - result.twin_counts[i]
            > 2 * np.std(result.twin_counts[i, :60], ddof=1)
        )
        assert result.onset[i] == (exceedances[0] if len(exceedances) else -1)


def test_remote_onsets_use_strict_frozen_training_sd_and_censoring():
    from headd_l0.simulate import SimConfig, _onsets

    twin = np.zeros((5, 132))
    # This training sample has mean=10 and sample variance exactly 60.
    twin[1:3] = 10
    twin[1:3, :59] = 9
    twin[1:3, 59] = 69
    # SD is sqrt(60): ddof=0 would incorrectly accept an excess of 15.4.
    counts = twin.copy()
    counts[1, 70:73] += [15.4, 2 * np.sqrt(60), 16]
    counts[1:3, 100:] = twin[1:3, 100:] = 1000000
    counts[3, 90] = 1
    np.testing.assert_array_equal(
        _onsets(counts, twin, SimConfig()), [75, 72, -1, 90, -1]
    )
    np.testing.assert_array_equal(_onsets(counts, twin, SimConfig(label="N")), -1)


@pytest.mark.parametrize(
    "change",
    [
        {"epsilon": -0.01},
        {"epsilon": 1.01},
        {"epsilon": np.nan},
        {"seed_region": -1},
        {"seed_region": 0.5},
        {"seed_region": True},
        {"endemic_hazard": -1},
        {"endemic_hazard": np.nan},
        {"endemic_hazard": (0, np.inf)},
    ],
)
def test_invalid_coupled_configuration_is_rejected(change):
    from headd_l0.simulate import SimConfig

    with pytest.raises(ValueError):
        SimConfig(**change)


@pytest.mark.parametrize(
    "weights", [np.zeros((0, 0)), np.ones((2, 3)), np.ones((13, 13)), np.ones(13)]
)
def test_weights_must_be_square_and_row_normalized(weights):
    from headd_l0.simulate import SimConfig, simulate

    with pytest.raises(ValueError):
        simulate(SimConfig(), weights, np.random.default_rng(42))


@pytest.mark.parametrize(
    "change", [{"seed_region": 13}, {"endemic_hazard": (0.001, 0.002)}]
)
def test_region_configuration_matches_weights(change):
    from headd_l0.simulate import SimConfig, simulate

    with pytest.raises(ValueError):
        simulate(SimConfig(**change), _ring_weights(), np.random.default_rng(42))


def test_regional_endemic_hazards_enter_the_local_flow():
    from headd_l0.simulate import SimConfig, _integrate

    latent, _, _ = _integrate(
        SimConfig(endemic_hazard=(0, 0.001)),
        np.array([0, 1]),
        np.array([[100000.0, 0], [100000.0, 0]]),
        np.zeros((1, 2, 2)),
        "N",
    )
    np.testing.assert_allclose(latent.sum(axis=0), [0, 110], rtol=0, atol=1e-12)
