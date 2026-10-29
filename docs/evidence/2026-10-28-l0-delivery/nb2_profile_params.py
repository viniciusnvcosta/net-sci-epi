"""Isolated, predeclared Monte Carlo diagnostic; not a production estimator."""

import warnings

import numpy as np
import statsmodels.api as sm
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

from headd_l0.forecast import harmonic_design

LOW, HIGH = np.log(1e-6), np.log(10.0)


def fit_profile(y):
    """Fit one panel and return diagnostics; never used by the runner."""
    y = np.asarray(y, dtype=float)
    if y.ndim != 1 or len(y) < 12 or not np.isfinite(y).all() or np.any(y < 0):
        return {"valid": False, "error": "invalid input"}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            x = harmonic_design(np.arange(len(y)))
            poisson = sm.GLM(y, x, family=sm.families.Poisson()).fit()
            if not poisson.converged:
                raise ValueError("Poisson did not converge")
            mu = poisson.fittedvalues
            score = float(0.5 * np.sum((y - mu) ** 2 - y))

            def ll(z):
                alpha = np.exp(z)
                fit = sm.GLM(
                    y, x, family=sm.families.NegativeBinomial(alpha=alpha)
                ).fit(maxiter=100, tol=1e-10, tol_criterion="params")
                if not fit.converged:
                    raise ValueError("NB2 IRLS did not converge")
                m = fit.fittedvalues
                value = np.sum(
                    gammaln(y + 1 / alpha)
                    - gammaln(1 / alpha)
                    - gammaln(y + 1)
                    + y * np.log(alpha * m)
                    - (y + 1 / alpha) * np.log1p(alpha * m)
                )
                if not np.isfinite(value):
                    raise ValueError("nonfinite likelihood")
                return float(value)

            opt = minimize_scalar(
                lambda z: -ll(z),
                bounds=(LOW, HIGH),
                method="bounded",
                options={"xatol": 1e-8},
            )
            if not opt.success:
                raise ValueError("profile optimizer failed")
            grid = [ll(z) for z in np.linspace(LOW, HIGH, 17)]
            best_grid = max(grid)
            dll = float(-opt.fun - poisson.llf)
            boundary = score <= 0
            contradiction = bool(best_grid > poisson.llf + 1e-7) if boundary else False
            missed_grid = bool(best_grid > -opt.fun + 1e-7)
            alpha = 0.0 if boundary else float(np.exp(opt.x))
            se = None
            if not boundary:
                if opt.x < LOW + 1e-3 or opt.x > HIGH - 1e-3:
                    raise ValueError("interior estimate at search boundary")
                step = 1e-3
                curvature = (
                    -(ll(opt.x + step) - 2 * ll(opt.x) + ll(opt.x - step)) / step**2
                )
                if not np.isfinite(curvature) or curvature <= 0:
                    raise ValueError("invalid profile curvature")
                se = float(alpha / np.sqrt(curvature))
            return {
                "valid": not (contradiction or (missed_grid and not boundary)),
                "boundary": boundary,
                "score": score,
                "alpha": alpha,
                "se": se,
                "delta_ll": dll,
                "grid_contradiction": contradiction,
                "grid_exceeds_optimizer": missed_grid,
            }
    except (ValueError, ArithmeticError, np.linalg.LinAlgError) as exc:
        return {"valid": False, "error": str(exc)}
