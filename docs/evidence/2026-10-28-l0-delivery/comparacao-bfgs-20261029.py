import contextlib
import io
import runpy
import warnings

import numpy as np
import statsmodels.api as sm

from headd_l0.forecast import _fit_series, harmonic_design

with contextlib.redirect_stdout(io.StringIO()):
    d = runpy.run_path("docs/evidence/2026-10-28-l0-delivery/diagnostico-nb2.py")
X = harmonic_design(np.arange(60))
ref = np.load("tests/reference/data.npz")
real = np.vstack([ref["state"], ref["counts"].T])[:, :60]
for group, ys in [("pilot", d["panel"]), ("real", real)]:
    print(group)
    for i, y in enumerate(ys):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            p = sm.GLM(y, X, family=sm.families.Poisson()).fit()
            mu = p.fittedvalues
            alpha = max(float(np.mean(((y - mu) ** 2 - y) / mu**2)), 1e-3)
            fit = sm.NegativeBinomial(y, X, loglike_method="nb2").fit(
                start_params=np.r_[p.params, alpha], method="bfgs", maxiter=500, disp=0
            )
            old = _fit_series(y, X)
            params = np.asarray(fit.params)
            diff = (
                np.max(np.abs(params - np.r_[old[0], old[1]]))
                if old[2]
                else float("nan")
            )
            print(
                i,
                "alpha",
                format(params[-1], ".7g"),
                "ok",
                fit.mle_retvals["converged"],
                "finite",
                np.isfinite(params).all(),
                "dLL",
                format(fit.llf - p.llf, ".7g"),
                "maxdiff",
                format(diff, ".7g"),
            )
