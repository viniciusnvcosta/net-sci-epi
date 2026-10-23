# Preserved E0* diagnostic — 21 October 2026

Descriptive evidence only. E0 remains inconclusive; the 30 September E0*/FAR
failures remain failed. G4/source-byte verification is pending, the full bench
has not executed, and `interpretation_allowed=false`. Diagnostic exit 0 means
that the artifact audit completed; it does not pass a scientific gate.

## Provenance and reproduction

- Historical source: `/home/vinvs/projects/net-sci-epi/.worktrees/second-execution/results/e0-star-scoring-20260930`.
- Run/code: `e0-star-scoring-20260930`, `017bd1a0d6cd3ecf1e8d8efe55a4826c234b3132`;
  reference CDADE `fbfa609bba6cb0b0f2a9e8d73be18022aec319b7`, root seed 42,
  `baseline_id=B1*`.
- Diagnostic/current audit code: `023a8d21bd4dbda0b049f51541055708f90c1df3`.
- The five hashes in [the prior pinned summary](../pr-2/e0-star-summary.json)
  are checked before diagnostic completion. [diagnostics.json](diagnostics.json)
  contains those `pinned_sha256` values and all twelve consumed file hashes in
  `observed_sha256`. Seven newly observed auxiliary hashes are explicitly
  unpinned historical artifacts; recording them now does not create earlier provenance.
- The controller's initial full source inventory covered all 18 files. Its
  byte digest is `bfa83cafbe87b577cf5516519a4723322cdaf02b5bb27d5a0cdb2f1813453589`.
  Full relative-path membership and SHA-256 equality against that inventory were
  required before publication and after verification, including unused null panels.
  The inventory itself remains byte-identical. The prior pinned summary is unchanged.

Run from this checkout with the existing shared environment; `PYTHONPATH=src`
selects this worktree and `--no-sync` avoids changing the environment:

```bash
env UV_PROJECT_ENVIRONMENT=/home/vinvs/projects/net-sci-epi/.venv   UV_CACHE_DIR=/tmp/headd-ratification-uv PYTHONPATH=src   uv run --no-sync python -m headd_l0.e0_diagnostics   --source /home/vinvs/projects/net-sci-epi/.worktrees/second-execution/results/e0-star-scoring-20260930   --evidence docs/evidence/pr-2/e0-star-summary.json   > /tmp/headd-e0-diagnostics-task3-first.json
```

The published JSON is the captured stdout, created exclusively along with this
note. A second invocation must compare equal as parsed JSON. Existing evidence
files must never be overwritten; any later diagnostic requires a new versioned
path. No fitting, detector scoring, threshold calibration, bootstrap, historical
artifact write, or new gate execution occurs in this diagnostic.

## Numerical observations

The canonical 13 regional pairs have evaluation months 60–131 (72 months per
region); both classes are present. Mean AP is 0.5471615984892939 for B1* and
0.6781268454330207 for causal z-score. Mean paired ΔAP(B1*−z-score) is
**−0.13096524694372677**, with lower B1* AP in **12 of 13** regions. Each
region's AP, prevalence and positive/negative denominators appear in the JSON.
All 26 regional AP values recomputed from saved scores/labels match to `1e-12`.
PA has 72 positive and zero negative months; its AP remains undefined (`null`)
and excluded from regional pairing. No substitute PA discrimination is inferred.
The **historical**, unrecomputed bootstrap lower bound remains
**−0.20186060618499926** and E0* still fails `trivial_baseline`.

Each regional/arm evaluation-null FAR denominator is 200×72=14,400 months.
All 26 stored FARs, flags and calibration achieved FARs agree with recomputation
from saved scores and fixed thresholds. The target is `1/60`, tolerance `1/300`,
with an inclusive band [0.013333333333333332, 0.02]. The three failed pairs are:

| Task / arm | Evaluation FAR | Calibration achieved FAR |
| --- | --- | --- |
| ARAGUAIA / B1* | 0.012986111111111111 | 0.016666666666666666 |
| XINGU / B1* | 0.012777777777777779 | 0.016666666666666666 |
| RIO CAETES / zscore | 0.01138888888888889 | 0.01423611111111111 |

All failures are below the bilateral FAR band. Calibration's conservative
upper bound does not guarantee bilateral closeness on independent evaluation N.
This distinction is specified behavior, not an implementation defect established
by poor scores. No FAR tolerance, threshold, seed, pool or selector was changed.
All 14 NB2 fits are valid and convergent, with finite coefficients, positive
finite dispersion and forecast means, and no fallback used. Calibration and
evaluation have 200 unique panel IDs each; all 400 spawn keys are unique, have
root entropy 42 and the expected separate stream prefix (0 or 1).

## Causal audit: historical code and current verification

Historical references below identify files at commit
`017bd1a0d6cd3ecf1e8d8efe55a4826c234b3132` (H). Inspect them with
`git show 017bd1a0d6cd3ecf1e8d8efe55a4826c234b3132:src/headd_l0/<file>`.
Current references identify `023a8d21bd4dbda0b049f51541055708f90c1df3` (C).
A scoped `git diff H C -- src/headd_l0/{e0_scoring,forecast,features,reconcile,detectors,select,threshold}.py`
was inspected separately: forecast, features, reconcile, detectors and select
are byte-identical; scoring only adds feature-name manifest logging after H
line 278, and threshold only adds `FARCheck`/`check_far` before the unchanged
calibration implementation. Thus current test execution is identified separately
from historical source inspection.

| Path / exact historical lines | Trace and present-code checks |
| --- | --- |
| [forecast.py](../../../src/headd_l0/forecast.py), H/C 69–99; H e0_scoring.py 162–195 | NB2 fits months 0–59 only; a fixed log-linear/two-harmonic fit generates means for 0–131. Evaluation is 60–131. No later count refits parameters. `test_fit_uses_training_only`, `test_forecast_positive_and_shaped`, `test_real_sivep_series_converge`. |
| [reconcile.py](../../../src/headd_l0/reconcile.py), H/C 114–152; H e0_scoring.py 278–291 | MinT covariance and residual SD use only months 0–59. Counts minus reconciled means are standardized with training SD; no score reconciliation. Training fits are in-sample residuals of the fixed NB2 fit; they are not a rolling refit experiment. `test_training_months_only`, `test_standardize_uses_training_sd`, `test_reconciled_residuals_coherent`. |
| [features.py](../../../src/headd_l0/features.py), H/C 40–57; H e0_scoring.py 98–110, 279–291 | Local columns are current residual, lag-one residual, and their difference. Month-zero lag is a zero placeholder excluded from detector training (months 1–59). Current-month observations are available to detection at that month. `test_prefix_invariance`, `test_node_and_feature_axes`. |
| [detectors.py](../../../src/headd_l0/detectors.py), H/C 40–88, 94–142, 181–232, 235–255 | Six detectors fit local features only at 1–59. PyOD decision functions preserve higher-is-more-anomalous orientation; independent MCD returns square-root Mahalanobis distance. Score calls do not refit. The z-score uses absolute departures against strictly previous 12 months. `test_outlier_has_larger_score` and `test_scoring_batch_does_not_refit` (all six), `test_mcd_against_sklearn`, `test_rolling_zscore_is_causal`. |
| [select.py](../../../src/headd_l0/select.py), H/C 128–174; H e0_scoring.py 98–110 | Detector score stream `features[j,1:]` has 131 rows for months 1–131; exclusive cutoff 59 means training 1–59. Output `[59:]` maps exactly to months 60–131 (72 rows). Scaling and .95 vote quantiles use only those 59 training rows; selection at stream row t uses votes `[start:t]` and blends row t. ADWIN resets future windows; each panel gets a fresh selector. Ground-truth outbreak labels never enter selection. `test_prefix_invariance`, `test_competence_uses_previous_window_precision_and_recall`, `test_drift_resets_only_future`, `test_no_labels_argument_and_training_normalization`. |
| H e0_scoring.py 32–39, 214–268, 308–325; [threshold.py](../../../src/headd_l0/threshold.py), H 42–110 / C 78–146 | Separate calibration/evaluation `SeedSequence` children generate NB2 evaluation months, preserving shared real training counts; PA is recomputed from regional sums. Threshold estimation receives calibration scores only. GPD and empirical safety threshold use strict exceedances; evaluation uses `score > threshold`, never ≥. Historical scoring 116–135 uses the bilateral tolerance; current `check_far` C 41–64 expresses inclusive bounds. Actual saved flags match. `test_no_evaluation_input`, `test_far_with_ties`, `test_unconditional_tail_probability_and_empirical_adjustment`, `test_far_on_independent_nulls`, `test_evaluation_far_gate_keeps_both_tolerance_boundaries`. |
| H e0_scoring.py 326–374 | Injected labels/scores are paired by task, metric window is 60–131, PA AP is undefined if single-class, and only regional rows enter FAR/gate. Historical E0* bootstrap uses its separate recorded stream; this diagnosis reads the historical result without resampling. |

Saved arrays alone cannot prove training causality. This audit combines the
pinned artifact identity, historical source inspection and current component
behavior tests; it is not a fresh historical execution or environment recreation.
The historical `components.log` reports 122 passed in 5.69s, and the run manifest
records that execution's component command/source identity. Those are preserved
historical records; the 108 tests below were newly executed on current code.

## Verification and stop decision

With the environment prefix above:

```bash
uv run --no-sync pytest -o addopts='' tests/test_forecast.py tests/test_features.py tests/test_detectors.py tests/test_reconcile.py tests/test_select.py tests/test_threshold.py -q
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest
git diff --check
```

The focused causal suite passed **108 tests in 5.87s** with marker exclusions
removed. Full Ruff lint/format and the default pytest suite are reported in the
execution handoff; default `pytest` excludes `slow`, `reference` and `integration`
through `-m 'not slow and not reference and not integration'`. These are current
technical checks and do not establish G4 or full scientific validation.

**Decision:** this read-only audit establishes no independently justified
baseline implementation defect. The regional AP loss and low FAR are preserved
outcomes, not permission to tune them. No baseline correction or prospective
E0* run is authorized by this evidence. If a separately demonstrated contract
violation later supplies an independently motivated failing reproduction test,
its correction requires a separate spec/plan, distinct code/profile version,
seed and run ID while retaining `baseline_id=B1*`. Preserve this failed run.
Otherwise inference stops with an inconclusive report. P5 official-byte/equation
checks, fixed monthly diagnostics and scientific G4 review remain a separate
eligible evidence cycle; layer 1 design and verified parallel layer 2 execution
remain separate cycles, gated before scoring. A conclusive positive or negative
RQ1′ statement requires mandatory layer 0 and completed layers 1/2 with every
applicable gate passing. See [D-RATIFY](../../protocol-decisions.md#d-ratify-2026-10-21--ratificação-científica-prospectiva).
