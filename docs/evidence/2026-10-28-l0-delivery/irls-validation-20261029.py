"""Run two frozen high-mean diagnostic cohorts against Poisson-start IRLS."""

import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy
import statsmodels

source = Path("docs/evidence/2026-10-28-l0-delivery/nb2_profile_poisson_start.py")
spec = importlib.util.spec_from_file_location("profile_poisson_start", source)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
out = Path("results/l0-nb2-irls-poisson-start-validation-20261029-v1.json")
if out.exists():
    raise FileExistsError(out)
groups = {}
for seed in (204, 804):
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(30):
        y = rng.negative_binomial(1 / 0.0005, 1 / (1 + 0.0005 * 3300), 600)
        rows.append({"index": i, **module.fit_profile(y)})
    groups[str(seed)] = rows
    print(f"seed {seed}: completo", flush=True)
record = {
    "status": "diagnostic_only",
    "interpretation_allowed": False,
    "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
    "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "plan": "docs/superpowers/plans/2026-10-29-irls-validacao-e-integracao.md",
    "numpy": np.__version__,
    "scipy": scipy.__version__,
    "statsmodels": statsmodels.__version__,
    "groups": groups,
}
with out.open("x") as f:
    json.dump(record, f, indent=2, allow_nan=False)
    f.write("\n")
