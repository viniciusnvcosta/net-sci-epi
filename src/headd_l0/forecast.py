# ABOUTME: NB2 count forecaster with a linear trend and two annual harmonic pairs, per series.
# ABOUTME: Fitted on training months only; feeds MinT reconciliation (D5) and NB2 nulls (D-GT3).
"""Negative binomial (NB2) forecaster fixed by decisions D5 and D-GT3.

For each series, ``log mu_t = b0 + b1 t + sum_k [a_k sin(2 pi k t / 12) + b_k cos(...)]``
for k = 1, 2, with t in months (0 = 2009-01) and the NB2 dispersion estimated by
maximum likelihood (statsmodels). The model is static after training, so
``forecast_mean`` for t >= ``train_months`` is the one-step-ahead forecast and,
for earlier months, the in-sample fit. A series whose fit fails or does not
converge is recorded in ``NB2Fit.converged``; no substitute model is fitted.
"""

import warnings
from dataclasses import dataclass

import numpy as np
import statsmodels.api as sm


@dataclass(frozen=True)
class NB2Fit:
    """Per-series NB2 fit: coefficients ``[n_series, 6]``, alpha and convergence ``[n_series]``."""

    coefficients: np.ndarray
    alpha: np.ndarray
    converged: np.ndarray
    train_months: int


def harmonic_design(months: np.ndarray) -> np.ndarray:
    """Return the design matrix ``[len(months), 6]``: 1, t, then sin/cos for k = 1, 2.

    Args:
        months: Month indices, 0 = 2009-01.
    """
    t = np.asarray(months, dtype=float)
    columns = [np.ones_like(t), t]
    for k in (1, 2):
        angle = 2 * np.pi * k * t / 12
        columns += [np.sin(angle), np.cos(angle)]
    return np.column_stack(columns)


def _fit_series(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, float, bool]:
    """Fit one series from Poisson starting values; failures return NaN parameters."""
    failed = np.full(X.shape[1], np.nan), np.nan, False
    with warnings.catch_warnings():
        # The outcome is judged below by convergence and finite parameters.
        warnings.simplefilter("ignore")
        try:
            poisson = sm.GLM(y, X, family=sm.families.Poisson()).fit()
            mu = poisson.fittedvalues
            alpha = max(float(np.mean(((y - mu) ** 2 - y) / mu**2)), 1e-3)
            result = sm.NegativeBinomial(y, X, loglike_method="nb2").fit(
                start_params=np.append(poisson.params, alpha),
                method="newton",
                maxiter=100,
                disp=0,
            )
        except (np.linalg.LinAlgError, ValueError):
            return failed
    params = np.asarray(result.params, dtype=float)
    converged = bool(result.mle_retvals["converged"]) and bool(
        np.isfinite(params).all()
    )
    return params[:-1], float(params[-1]), converged


def fit_nb2(counts: np.ndarray, train_months: int = 60) -> NB2Fit:
    """Fit the NB2 model to each series using months ``0 .. train_months - 1`` only.

    Args:
        counts: Count panel ``[n_series, n_months]``; later months are ignored.
        train_months: Number of leading months used for fitting.

    Returns:
        The per-series fit, with non-converged series flagged.
    """
    train = np.asarray(counts, dtype=float)[:, :train_months]
    X = harmonic_design(np.arange(train_months))
    fits = [_fit_series(y, X) for y in train]
    return NB2Fit(
        coefficients=np.array([f[0] for f in fits]),
        alpha=np.array([f[1] for f in fits]),
        converged=np.array([f[2] for f in fits]),
        train_months=train_months,
    )


def forecast_mean(fit: NB2Fit, months: np.ndarray) -> np.ndarray:
    """Return the NB2 mean ``[n_series, len(months)]``; NaN rows mark failed fits.

    Args:
        fit: Result of :func:`fit_nb2`.
        months: Month indices to forecast, 0 = 2009-01.
    """
    return np.exp(fit.coefficients @ harmonic_design(months).T)
