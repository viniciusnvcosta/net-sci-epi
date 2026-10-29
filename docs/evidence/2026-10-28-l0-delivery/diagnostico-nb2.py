import json
import warnings
from pathlib import Path

import numpy as np
import statsmodels.api as sm

from headd_l0.data import hierarchy
from headd_l0.exploratory import load_graphs, load_hazards, simulate_replicate
from headd_l0.forecast import harmonic_design

root = Path("/home/vinvs/projects/net-sci-epi/.worktrees")
manifest = (
    root
    / "castro-data-provenance/results/l0-fixed-geography-candidate-v2/manifest.json"
)
calibration = root / "_archive/2026-10-23/second-execution/data/processed/endemic-white"
_, w, _, _ = load_graphs(manifest)
sim = simulate_replicate(w, 0.0, "T", "pilot", 0, load_hazards(calibration))
panel = np.vstack((sim.counts.sum(axis=0), sim.counts))[:, :60]
X = harmonic_design(np.arange(60))
rows = []
for name, y in zip(("PA", *hierarchy().leaves), panel):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            p = sm.GLM(y, X, family=sm.families.Poisson()).fit()
            mu = p.fittedvalues
            initial = max(float(np.mean(((y - mu) ** 2 - y) / mu**2)), 1e-3)
            fit = sm.NegativeBinomial(y, X, loglike_method="nb2").fit(
                start_params=np.append(p.params, initial),
                method="newton",
                maxiter=100,
                disp=0,
            )
            params = np.asarray(fit.params)
            rows.append(
                {
                    "region": name,
                    "alpha": float(params[-1]) if np.isfinite(params[-1]) else None,
                    "converged": bool(fit.mle_retvals["converged"])
                    and bool(np.isfinite(params).all()),
                    "optimizer_converged": bool(fit.mle_retvals["converged"]),
                    "iterations": int(fit.mle_retvals["iterations"]),
                    "pearson_ratio": float(
                        np.sum((y - mu) ** 2 / mu) / (len(y) - X.shape[1])
                    ),
                    "mean": float(y.mean()),
                    "variance": float(y.var()),
                    "warnings": sorted({str(x.message) for x in caught}),
                }
            )
        except (np.linalg.LinAlgError, ValueError) as e:
            rows.append(
                {
                    "region": name,
                    "error": repr(e),
                    "warnings": sorted({str(x.message) for x in caught}),
                }
            )
print(json.dumps(rows, indent=2, ensure_ascii=False, allow_nan=False))
