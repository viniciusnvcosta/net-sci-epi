"""Replay failed high-mean addresses and record each original IRLS evaluation."""

import hashlib
import importlib.util
import inspect
import json
import linecache
from pathlib import Path

import numpy as np
import statsmodels.api as sm

ROOT = Path("docs/evidence/2026-10-28-l0-delivery")
INPUT = Path("results/l0-nb2-profile-monte-carlo-20261029-v1.json")
OUTPUT = Path("results/l0-nb2-irls-diagnostic-20261029-v2.json")
spec = importlib.util.spec_from_file_location(
    "profile_harness", ROOT / "nb2_profile_harness.py"
)
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
old = json.loads(INPUT.read_text())
expected = old["source_sha256"]
assert (
    hashlib.sha256((ROOT / "nb2_profile_harness.py").read_bytes()).hexdigest()
    == expected
)
failed = {r["index"] for r in old["groups"]["nb3300"]["replicates"] if not r["valid"]}
original = sm.GLM.fit
records = []
active = []


def instrumented(model, *args, **kwargs):
    """Record unchanged fits; keep their convergence decision intact."""
    result = original(model, *args, **kwargs)
    alpha = getattr(model.family, "alpha", None)
    if alpha is not None:
        stack = inspect.stack(context=0)
        names = [frame.function for frame in stack]
        caller = next(frame for frame in stack if frame.function == "fit_profile")
        line = linecache.getline(caller.filename, caller.lineno).strip()
        phase = (
            "search"
            if "<lambda>" in names
            else "grid"
            if line.startswith("grid =")
            else "curvature"
        )
        history = result.fit_history
        active.append(
            {
                "phase": phase,
                "caller_line": caller.lineno,
                "alpha": float(alpha),
                "converged": bool(result.converged),
                "iterations": int(history.get("iteration", -1)),
            }
        )
    return result


sm.GLM.fit = instrumented
try:
    rng = np.random.default_rng(204)
    for index in range(30):
        y = rng.negative_binomial(2000, 1 / (1 + 0.0005 * 3300), 600)
        if index in failed:
            active.clear()
            result = harness.fit_profile(y)
            records.append(
                {"index": index, "result": result, "evaluations": list(active)}
            )
finally:
    sm.GLM.fit = original

payload = {
    "status": "diagnostic_only",
    "original_sha256": hashlib.sha256(INPUT.read_bytes()).hexdigest(),
    "harness_sha256": expected,
    "seed": 204,
    "records": records,
}
with OUTPUT.open("x") as f:
    json.dump(payload, f, indent=2, allow_nan=False)
    f.write("\n")
