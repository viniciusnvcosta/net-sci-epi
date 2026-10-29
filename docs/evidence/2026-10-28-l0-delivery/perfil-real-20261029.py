import warnings

import numpy as np
import statsmodels.api as sm
from scipy.optimize import minimize_scalar
from scipy.special import gammaln

from headd_l0.forecast import harmonic_design

ref = np.load("tests/reference/data.npz")
ys = np.vstack([ref["state"], ref["counts"].T])[:, :60]
X = harmonic_design(np.arange(60))
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    for i, y in enumerate(ys):
        p = sm.GLM(y, X, family=sm.families.Poisson()).fit()
        mu = p.fittedvalues
        a = max(float(np.mean(((y - mu) ** 2 - y) / mu**2)), 1e-3)
        n = sm.NegativeBinomial(y, X, loglike_method="nb2").fit(
            start_params=np.r_[p.params, a], method="newton", maxiter=100, disp=0
        )

        def profile(z, y=y):
            a = np.exp(z)
            f = sm.GLM(y, X, family=sm.families.NegativeBinomial(alpha=a)).fit(
                maxiter=100, tol=1e-10
            )
            if not f.converged:
                raise ValueError("IRLS")
            mu = f.fittedvalues
            ll = np.sum(
                gammaln(y + 1 / a)
                - gammaln(1 / a)
                - gammaln(y + 1)
                + y * np.log(a * mu)
                - (y + 1 / a) * np.log1p(a * mu)
            )
            return ll, f.params

        opt = minimize_scalar(
            lambda z: -profile(z)[0],
            bounds=(np.log(1e-6), np.log(10)),
            method="bounded",
            options={"xatol": 1e-8},
        )
        par = np.r_[profile(opt.x)[1], np.exp(opt.x)]
        se = n.bse
        ratios = np.abs(par - n.params) / se
        print(
            i,
            "old_ok",
            n.mle_retvals["converged"],
            "profile_ok",
            opt.success,
            "alpha",
            round(par[-1], 8),
            "max_delta_se",
            float(ratios.max()),
            "all_pass",
            bool(np.isfinite(se).all() and (se > 0).all() and (ratios < 1e-3).all()),
            flush=True,
        )
