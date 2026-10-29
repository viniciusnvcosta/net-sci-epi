"""Run the committed three-cohort IRLS parameter-criterion diagnostic."""

import hashlib
import importlib.util
import json
import warnings
from pathlib import Path

import numpy as np
import scipy
import statsmodels
import statsmodels.api as sm

from headd_l0.forecast import harmonic_design

source = Path("docs/evidence/2026-10-28-l0-delivery/nb2_profile_params.py")
spec = importlib.util.spec_from_file_location("profile_params", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
out = Path("results/l0-nb2-irls-params-validation-20261029-v1.json")
if out.exists():
    raise FileExistsError(out)
groups = {}
for seed in (204, 804, 904):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(30):
        y = rng.negative_binomial(1 / 0.0005, 1 / (1 + 0.0005 * 3300), 600)
        rows.append({"index": i, **module.fit_profile(y)})
    groups[str(seed)] = rows
    print(f"seed {seed}: completo", flush=True)
rng = np.random.default_rng(204)
for _ in range(3):
    y = rng.negative_binomial(1 / 0.0005, 1 / (1 + 0.0005 * 3300), 600)
x = harmonic_design(np.arange(600))
alpha = float(np.exp(np.log(1e-6)))
with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    old = sm.GLM(y, x, family=sm.families.NegativeBinomial(alpha=alpha)).fit(
        maxiter=100, tol=1e-10
    )
    new = sm.GLM(y, x, family=sm.families.NegativeBinomial(alpha=alpha)).fit(
        maxiter=100, tol=1e-10, tol_criterion="params"
    )
params = np.asarray(old.fit_history["params"][2:])
deviance = np.asarray(old.fit_history["deviance"][2:])
trajectory = {
    "alpha": alpha,
    "old_converged": bool(old.converged),
    "old_iterations": old.fit_history["iteration"],
    "new_converged": bool(new.converged),
    "new_iterations": new.fit_history["iteration"],
    "new_params_finite": bool(np.isfinite(new.params).all()),
    "deviance_changes": np.diff(deviance).tolist(),
    "max_parameter_changes": np.max(np.abs(np.diff(params, axis=0)), axis=1).tolist(),
}
record = {
    "status": "diagnostic_only",
    "interpretation_allowed": False,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "plan_commit": "17c06ef",
    "numpy": np.__version__,
    "scipy": scipy.__version__,
    "statsmodels": statsmodels.__version__,
    "trajectory": trajectory,
    "groups": groups,
}
with out.open("x") as f:
    json.dump(record, f, indent=2, allow_nan=False)
    f.write("\n")
