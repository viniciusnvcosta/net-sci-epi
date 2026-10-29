"""Reproduce a count-series numerical failure without changing the forecaster."""

import numpy as np
from scipy.special import gammaln

from headd_l0.forecast import _fit_series, harmonic_design


def test_poisson_example_yields_invalid_nb2_fit():
    """One fixed equidispersed-generating example reproduces the observed failure."""
    counts = np.random.default_rng(42).poisson(50, 60)
    coefficients, alpha, valid = _fit_series(counts, harmonic_design(np.arange(60)))
    assert not valid
    assert not np.isfinite(alpha) or not np.isfinite(coefficients).all()


def test_nb2_boundary_score_matches_one_sided_likelihood_derivative():
    """Verify the dispersion score independently using the exact NB2 density."""
    y = np.array([0.0, 2.0, 4.0, 9.0])
    mu = np.array([1.2, 2.5, 3.0, 5.0])
    score = 0.5 * np.sum((y - mu) ** 2 - y)
    poisson_ll = np.sum(y * np.log(mu) - mu - gammaln(y + 1))
    alpha = 1e-5
    nb_ll = np.sum(
        gammaln(y + 1 / alpha)
        - gammaln(1 / alpha)
        - gammaln(y + 1)
        + y * np.log(alpha * mu)
        - (y + 1 / alpha) * np.log1p(alpha * mu)
    )
    np.testing.assert_allclose((nb_ll - poisson_ll) / alpha, score, rtol=1e-3)
