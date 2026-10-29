import contextlib
import io
import runpy
import warnings

import numpy as np
import statsmodels.api as sm
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

from headd_l0.forecast import harmonic_design

with contextlib.redirect_stdout(io.StringIO()):
    d = runpy.run_path("docs/evidence/2026-10-28-l0-delivery/diagnostico-nb2.py")
X = harmonic_design(np.arange(60))
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for name, y in zip(("PA", *d["hierarchy"]().leaves), d["panel"]):
        p = sm.GLM(y, X, family=sm.families.Poisson()).fit()
        score = 0.5 * np.sum((y - p.fittedvalues) ** 2 - y)

        def likelihood(z, y=y):
            a = np.exp(z)
            f = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=a)).fit(
                maxiter=100, tol=1e-10
            )
            if not f.converged:
                raise RuntimeError("IRLS did not converge")
            m = f.fittedvalues
            return np.sum(
                gammaln(y + 1 / a)
                - gammaln(1 / a)
                - gammaln(y + 1)
                + y * np.log(a * m)
                - (y + 1 / a) * np.log1p(a * m)
            )

        v = minimize_scalar(
            lambda z: -likelihood(z),
            bounds=(-13.815510557964274, 2.302585092994046),
            method="bounded",
            options={"xatol": 1e-8},
        )
        print(
            name,
            "score",
            round(score, 3),
            "alpha",
            format(np.exp(v.x), ".8g"),
            "dll",
            format(-v.fun - p.llf, ".6g"),
            "ok",
            v.success,
            flush=True,
        )
