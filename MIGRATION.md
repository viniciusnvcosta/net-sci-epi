# CDADE → HEADD L0 migration log

Source of every port: `/home/vinvs/projects/hybrid-theory` at
`fbfa609bba6cb0b0f2a9e8d73be18022aec319b7`, read only through `git archive`.
The original repository is licensed Apache-2.0 (root `LICENSE`; source files
carry no per-file headers). Code ported from it keeps that attribution through
the component rows below, which name the original path of each port.

Names: the original's `b1`…`b8` are its baselines (`b1` = Farrington, `b2` best
single, `b3` ensemble average, `b4` static top-k, `b5` reconciliation + EVT,
`b6`–`b8` recurrent). They are unrelated to the HEADD arms B0/B1/B2.

## Reference audit (Task 1, G0 evidence)

Historical procedure: the three one-time exporter scripts were retired after
Task 9 at the author’s request. Recover `scripts/` from HEADD commit `98187ee`
in a temporary directory to rerun the command below. Current tests validate
archived array hashes directly and do not require the legacy interpreter.

```bash
uv run python scripts/export_cdade_reference.py --repo /home/vinvs/projects/hybrid-theory \
  --revision fbfa609bba6cb0b0f2a9e8d73be18022aec319b7 --output results/reference-audit
```

The exporter (`scripts/export_cdade_reference.py`, stdlib only) runs the
worker (`scripts/_reference_worker.py` for `dvc.yaml` pipeline stages,
`scripts/_reference_primitives.py` for primitives on fixed seeded inputs) with
the original `.venv` interpreter as a read-only runtime. Pinned hashes live in
`tests/reference/manifest.json`; `.npz` container bytes vary between exports,
the per-array hashes do not.

Accepted operational choices (D-OPS, 2026-09-27): the second helper script
`scripts/_reference_primitives.py` and the `*.md` exclusion in
`[tool.ruff.format]`, which keeps ruff 0.16 from reformatting plan snippets.

Result on 2026-09-26: **exit 2, reference insufficient for E0**. Installed
reference packages match `uv.lock`; original HEAD, status and raw hashes were
unchanged by the run.

| Finding                                       | Evidence (runtime unless noted)                                                                               |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `missing_14_tasks`                            | evaluation yields one task, `sivep`: labels are `mask.max(axis=1)`, shape (132,) (D7)                         |
| `single_class_test_labels`                    | the 26 test months are all anomalous, so AP = 1.0 for every method and the ranking is all ties                |
| `stage_failed:pipeline_detect_{lof,knn,hbos}` | wrappers pass `random_state` to PyOD 3.6.1, which rejects it; `run_detect`'s fallback then raises `TypeError` |
| `stage_failed:pipeline_detect_mcd`            | `X[indices]` on a DataFrame raises `KeyError` (D3)                                                            |
| `stage_failed:pipeline_reconcile_min_t`       | 13×13 S against the single `score` column raises `ValueError` in matmul (D1, D2)                              |
| D3                                            | PCA wrapper negates PyOD's score: outliers score lower than inliers                                           |
| D4                                            | `EVTReconciler.fit` raises `ValueError: too many values to unpack`                                            |
| D5                                            | reconcile input is `leaf_forecasts.csv` with the single column `score`                                        |
| D6                                            | shifting scores from t = 90 changes blended scores at t = 80–84, 87, 89                                       |
| D8                                            | with Friedman p = 0.32, DM and Cliff's δ still run; Wilcoxon stops                                            |
| D9                                            | NAB/F1 threshold is the median of evaluated scores (static)                                                   |

Other observations: leaf sums equal the PA series in all 132 months; the
default injection leaves 408 negative cells; `evaluate` uses 26 test months
while baselines score 27 and are truncated; the pinned rerun matches the local
`results/metrics/sivep/metrics.json` (a clue, not a golden) for the rows it
recomputes. Recurrent `b6`–`b8` were not rerun.

## Ports

| Component | Original path                                                                           | New path                    | Parity check                                                                                                                                                             | Dropped and why                                                                                                                                                                                                                                                                     |
| --------- | --------------------------------------------------------------------------------------- | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| data      | `cdade/data/sivep.py` (`load_raw`, `prepare_counts`, `prepare_state_counts`, `_LEAVES`) | `src/headd_l0/data.py`      | `tests/test_data.py::test_counts_match_original_exactly`: counts, PA series, test totals, leaf order and months equal the pinned export, tolerance zero                  | Registry/plugin loader, canonical `entity/timestamp/level/value` layer and Hydra config (replaced by `configs/data.toml`). Added: missing region-months, regions or months and PA/regional mismatches raise instead of being filled with zeros                                      |
| reconcile | `cdade/reconciliation/summing_matrix.py`, `bottom_up.py`                                | `src/headd_l0/reconcile.py` | `tests/test_reconcile.py::test_s_matches_original` and `test_bottom_up_exact`: S equals the exported 14×13 matrix and bottom-up reproduces PA = leaf sum, tolerance zero | Registry classes and the 13×13 S inside `min_t.py`/`bottom_up.py` (the MinT one raised in the audit). MinT(Shrink) is new, per D2: diagonal target, Schäfer–Strimmer λ as in `hts::MinT`, solve-based projection, no clipping; it reconciles NB2 count forecasts, never scores (D5) |
| forecast  | none (new, D5/D-GT3)                                                                    | `src/headd_l0/forecast.py`  | Behaviour tests in `tests/test_forecast.py`: design by hand, parameter recovery, training-only fit, recorded non-convergence                                             | NB2 with trend and two harmonic pairs, Poisson starting values, per series                                                                                                                                                                                                          |

MinT on the real SIVEP data (2026-09-27, diagnostic only): all 14 NB2 fits converge, λ̂ = 0.100. The independent PA forecast differs from the sum of regional forecasts by a median of 848 cases/month in months 60–131; MinT moves the PA forecast by a median of 26% and 409 of 1,848 reconciled means are negative (406 in months 60–131; CARAJAS, LAGO DE TUCURUI, MARAJO II, METROPOLITANA III, RIO CAETES, TOCANTINS, XINGU, MARAJO I, PA). Per D2 they are not clipped; residuals y − P·μ̂ stay coherent.

## Not ported

| Original                                                                                                                                                                                          | Reason                                                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| `data/tycho.py`, `data/loaders/{tycho,uci_394,uci_501}.py`                                                                                                                                        | Tycho/UCI out of scope                                     |
| `baselines/farrington.py` (`b1`)                                                                                                                                                                  | Farrington excluded                                        |
| `baselines/static_topk.py` (`b4`)                                                                                                                                                                 | Top-k Eze excluded                                         |
| `baselines/recurrent_baseline.py`, `models/recurrent.py` (`b6`–`b8`)                                                                                                                              | recurrent baselines excluded                               |
| `detectors/{ocsvm,cblof,cof,sos}.py`                                                                                                                                                              | outside the six-detector pool                              |
| `registry.py`, `data/{base,dataset_paths,prepare,validate_schema}.py`, Hydra `main`s, MLflow logging, `dvc.yaml`, `justfile`, `reporting/`, `ablation/`, `evaluation/{stats_cli,stats_matrix}.py` | glue replaced by TOML, `results/<run_id>/` and plain dicts |
| `ensemble/`                                                                                                                                                                                       | DVC stage whose output `evaluate` does not read            |
| `selection`: `NaiveTopKSelector`, `generate_windowed_labels`, `windowed_diversity`, `scan_for_drift`, Page-Hinkley                                                                                | no caller in the pipeline                                  |
| `reconciliation/identity.py`, `reconciliation/evt.py`                                                                                                                                             | no caller in the default pipeline; `evt.fit` raises (D4)   |

## Corrected detector pool (D3, 2026-09-27)

`src/headd_l0/detectors.py` replaces `cdade/detectors/{pca,lof,knn,hbos,iforest,mcd}.py`
from the pinned SHA. Added dependency: PyOD 3.6.6 via `uv add pyod`.
LOF/KNN/HBOS omit the invalid `random_state`; PCA retains the positive PyOD
score rather than the original wrapper's inversion. IF/PCA library seeds are
derived from `SeedSequence`; FAST-MCD uses `Generator`. The original's audit
arrays remain unchanged. `test_detector_reference` compares the functioning
IF/PCA numerical primitives in the installed environment (PCA with corrected
sign), rtol=1e-7/atol=1e-9; this is not end-to-end legacy parity.

MCD is independent NumPy/SciPy code: 50 starts without replacement,
h=floor((n+p+1)/2), at most 50 C-steps, logdet tolerance 1e-7, fixed ridge
1e-8\*max(mean(training variances),1). It applies Gaussian consistency
alpha/F_chi2(p+2)(q_chi2(p)(alpha)) at raw support fraction h/n and after
reweighting at chi2(.975). Reference: [MCD and extensions](https://arxiv.org/abs/1709.07045);
[sklearn reference algorithm](https://github.com/scikit-learn/scikit-learn/blob/main/sklearn/covariance/_robust_covariance.py).
No sklearn MCD is imported in production. Behavior tests compare covariance
(relative error <=.15) and score Spearman correlation (>=.95) with MinCovDet,
and check C-step descent, contamination, singular geometry and determinism.

All detectors freeze their training constant-feature mask. Fully constant
training data uses Euclidean deviation from the training mean; partial constant
features are excluded. This is explicit behavior outside legacy parity.
Features retain their D5 scale; PCA's own standardization fits only on training.
The existing negative-forecast diagnostic is unchanged (D2 forbids clipping).

## EVT/FAR (Task 5, 2026-09-27)

`threshold.py` ports the functioning `_fit_gpd` primitive from
`cdade/baselines/reconciliation_evt.py` (pinned SHA, Apache-2.0), not the
broken two-parameter unpack in `reconciliation/evt.py`. `tests/reference/evt.npz`
is copied unchanged from the audit; all array hashes match the existing manifest.
Parameter parity uses the original absolute residuals only in the fixture,
rtol=1e-7/atol=1e-9. Production scores retain their signed anomaly orientation.

Calibration uses the observed strict-exceedance fraction in the unconditional
GPD quantile, then raises the threshold if necessary to enforce calibration
FAR <= target under `score > threshold`. Fewer than20 exceedances, degenerate
fits or a target outside the fitted tail use named empirical fallbacks.
`Calibration` records method, size, target and achieved calibration FAR;
unseen-null FAR is measured independently, not promised equal. Tests include
independent SeedSequence streams, ties, shift invariance and missing/nonfinite
inputs. Registry name is `evt_gpd`; complete experiment wiring belongs to the experiments plan.

## Causal selection (D6, Task 6, 2026-09-27)

`select.py` ports Q-statistic and exhaustive subset scoring from pinned CDADE
`selection/diversity.py` and `selection/selector.py` (Apache-2.0), dropping
greedy/top-k, true labels and forward-looking window assignment. Added river
0.26.1 via `uv add river`. Original `select.npz` arrays are copied unchanged
and verified against the manifest. Q/subset parity tolerance is1e-12;
the fixed ADWIN signal matches exported flags across the library versions.
That last check is dependency compatibility, not whole-stream legacy parity.

The corrected flow learns min/max and per-detector .95 vote cutoffs on training
only. Constant training columns normalize to zero. Majority vote is strict
(>half); ties are negative. Competence is mean precision/recall over the previous
window, or negative agreement if that window has no positive pseudo-labels.
The blend is the mean normalized score of selected detectors. ADWIN observes
mean competence after the current decision; a flag at t clears history and
uses competence .5 with the first lexicographic subset at t+1. Subsequent
windows rebuild from t+1; no past output changes. Training scores are NaN to
mark warmup outside evaluation, with deterministic active indices.

Tests cover future suffix changes, actual prefix truncation, hand-computed
competence, drift/reset and training-only normalization. Registry `meta_des`
will be wired and serialized by the experiment runner; component tests do not approve E0*.

## Evaluation (Task 7, 2026-09-27)

`evaluate.py` ports AP, precision/recall/F1 and the explicitly simplified NAB
formula from pinned `evaluation/metrics.py` (Apache-2.0). `metrics.npz` is the
unchanged audit export, verified against manifest hashes. Numerical parity is
1e-12 when tests supply the original median-derived alarms; production never
learns a threshold from evaluation scores and applies no point adjustment.
Both-class discrimination is required: the combined report returns None for
AP/ROC on single-class tasks, and standalone AP raises ValueError.

Detection uses the first alarm in the inclusive clipped onset±12 window;
lead=onset-alarm, delay=-lead. Misses retain restricted_lead through censoring
at window-end+1; no onset (-1) has no timing value and no detection denominator.
FAR uses only explicitly eligible monitored null months; empty eligibility is
an error. Runner must mask training alarms and serialize undefined metrics.

## Statistical inference (Task 8, 2026-09-27)

`stats.py` retains the pinned `evaluation/stats.py` Friedman/Wilcoxon primitives
and Cliff point statistic (Apache-2.0); `stats.npz` is copied from the audit with
all manifest array hashes verified. The exported non-significant Friedman
(stat5.836734693877531, p.32243093781203774) and Cliff point value match to1e-12.
All follow-ups now stop at Friedman p>.05, including DM and Cliff; no stub
p-values or artificial intervals are generated. All-zero paired Wilcoxon
differences return stat0/p1; other pairs use SciPy with .05/C(k,2).

Primary bootstrap resamples entire replicates with all regions together.
Task bootstrap accepts already-paired differences; D-GT1 callers pass13regions
and report PA separately, using the lower95% bound. Circular block bootstrap
resamples within each retained region; n_units there counts series, not an
independent-month/effective sample size. Cliff intervals resample paired region
indices with Generator (10000draws); RandomState interval equality is not claimed.

DM implements Bartlett HAC with lag12 in the secondary protocol, applied
separately per task to the predeclared squared binary-alarm losses (Experiments
Task4). Positive DM means the first method has higher loss. It never flattens
region boundaries into temporal lags. Exact equal losses yield(0,1); nonzero
constant differences yield undefined statistic/p, serialized as None with
zero_hac_variance status. A regression covers decimal roundoff. No numerical
fallback substitutes ordinary variance or fabricates significance.
Reference: [Newey–West/Bartlett](https://www.statsmodels.org/dev/generated/statsmodels.stats.sandwich_covariance.cov_hac.html).

## Task 9 — bounded injection and E0\* preparation

- `inject.py` ports `cdade/data/synthetic.py` types/magnitudes and random draw
  order; finite duration is drawn after direction, late onsets shifted left.
  PA is recomputed, mask is the union. Events preserve proposed/actual onset,
  kind, duration, direction and amplitude; negative values are not clipped.
- Literal original injection exists only in `tests/legacy_injection.py`, checked
  against all arrays in `inject.npz`. It reproduces the 26 all-positive legacy
  evaluation months. The corrected seed42 panel also exposes a single-class
  PA (72/72) because it combines 13 independently injected leaves. No redraw.
- `rolling_zscore` uses the preceding12months, ddof1, absolute orientation and
  unit scale for a constant history. `check_e0_star` pairs by task name and
  bootstraps13regions, excluding PA, with10000draws.
- `configs/e0_star.toml` runs preparation, not the future scoring/calibration
  experiment. It writes coherent injection, event and class diagnostics and
  a manifest; exit2 means no interpretation. With seed42:110negative cells,
  2adjusted onsets, E0inconclusive and E0\*failed(single_class:PA).
- Removed the3transient importer scripts and their subprocess tests; kept
  fixtures, raw hashes, original source SHA, descriptive results and a
  historical exporter commit. Local array integrity tests replace reimports.

Execution commands and current gate limitations: [development guide](docs/development.md).

## P6 causal residual features (Graph/Simulation Task 4, 2026-09-29)

`src/headd_l0/features.py` is new, not a CDADE port; no legacy parity claim
applies. It accepts only standardized residuals supplied by D5 and produces
full-axis local or leaf-neighbor `FeatureBatch` arrays. The names and order are
fixed by `tests/test_features.py`; the future runner must write them into its
manifest. Lag-one month zero and incomplete trailing-Moran windows carry zero
placeholders and are excluded by caller eligibility. `rolling_ews` returns
SD, signed CV, Pearson AR1, uncorrected skewness and Pearson kurtosis with an
elementwise validity mask. Hand calculations, constant inputs and prefix
invariance are behavior tests. Graph acquisition, scoring and simulator output
are outside this component.

## D-E0*-R1 regional pre-gate (Task 2, 2026-09-29)

`run.py` now enforces both classes and finite AP only for the 13 canonical
regional tasks in the 72-month test window. It rejects malformed regional
counts, missing/duplicate/unknown task-arm rows and mismatched regional labels.
Optional PA rows are descriptive and do not enter AP or class criteria. The
10,000-draw paired bootstrap remains over named regions. The root-seed-42
`inject_original_bounded` stream, labels and counts are unchanged; preflight
retains all 14 tasks, writes PA union/coherence diagnostics, and remains pending
until component and trivial-baseline evidence exists. The earlier
`single_class:PA` failure remains a historical artifact; E0 is inconclusive.
Behavior tests in `tests/test_run.py` cover this revision. No new dependency.

## P4 regional graph (2026-09-29)

`graph.py` and `graph_io.py` are new components, not CDADE ports. Synthetic
behavior tests cover Queen vertex contact, canonical ordering, rejected islands,
invalid geometry, bounded rewiring, labeled degrees, deterministic distinct
placebos, GEXF exports and verified caches. Acquisition tests replace only the
network boundary, retain real geometry/graph operations and verify diagnostic
artifacts on source/cardinality/topology failures. No dependency was added.

`configs/l0_graph.toml` fixes DataSUS via geobr, vintage 2013, micro regions of
PA and `simplified=false` before acquisition. The resolved geobr 2.1.1 reader
unions municipalities and removes interior holes; manifests record this
upstream operation and its source hash. Local invalid geometries are rejected,
not repaired. Original codes/names and their accent/case normalization are
retained in an audit table, checked against the exact 13 code/name pairs in
`PA_HEALTH_REGIONS_2013` (audit version `datasus-pa-2013-v1`). The table is
pinned to the acquired DataSUS/geobr 2013 source hash; unknown codes or swapped
code/name assignments fail before a ready cache is written. No year,
resolution or contiguity fallback is selected to obtain connectivity.

Each placebo candidate starts from A and accepts 10×|E| double-edge swaps,
rejecting loops, duplicate edges and disconnected proposals, within at most
1,000×|E| attempts. At most 10,000 candidates yield 30 distinct nonoriginal
connected graphs; exhaustion raises. Degree is preserved by node identity.
These budgets do not establish uniform mixing. Manifests retain RNG seed,
attempt counts, edge symmetric-difference distances, all pairwise distances,
hashes, source metadata, dependency versions and measured acquisition cost.
A valid cache requires compatible provenance, canonical names, an intact hash
and a connected simple undirected A. Acquisition status and scientific gate
limitations are recorded in [development](docs/development.md).

## P5 Gao simulator source preparation (29/09/2026)

P5 is a new scientific component, not a CDADE port. The
[source preparation note](docs/gao-source-preparation.md) identifies the Gao
supplement/Zenodo archive, pinned Chakraborty predecessor, equations,
parameter distributions and frozen feature-table hashes/medians. It records
the white-noise CV direction conflict with the planned all-noise test. The
[protocol entry](docs/protocol-decisions.md#pending-p5-source-parity-and-profile-revision--29092026)
is **pending**, not a profile approval. The requested machine-readable
`tests/reference/gao_manifest.json` and numeric `gao_single.npz` remain absent;
no `simulate.py` implementation, parity fixture, simulator run or scientific
gate result exists. P4 graph and P6 features are separate new components,
implemented and technically validated as recorded above; neither approves
G3/G5 or E1′ interpretation.

## Task 6 — approved E0* scoring integration (30/09/2026)

`forecast.sample_nb2` and `e0_scoring.py` are new orchestration, not CDADE
parity ports. They consume the existing corrected B1* components and unchanged
local P6 features after decision `50f8b3f` (D-E0*-R1). The preparation entry
point remains unchanged; `run.run_e0_scoring` and `--score-e0` select scoring.
Training is raw months 0–59; pool training excludes lag placeholder month 0.
Nulls retain the training prefix and sample 72 NB2 months, with coherent PA,
200 calibration panels and 200 independent evaluation panels. The injection
keeps the root RNG, including its unmodified negative injected cells.

Behavior tests cover NB2 moments/integer draws/determinism, failed D5 fits,
training isolation, calibration/evaluation separation, component source
identity, injection preservation, regional prevalence and CLI dispatch.
Existing detector/selector/threshold defaults are unchanged. Component suites
are executed by the runner and tied to SHA plus source digest; each output
records the applicable model/fallback diagnostics. Failed base fits block
before MinT/AP. D-GT3 block-bootstrap construction remains unspecified and
unimplemented; Task 6 remains partial. E0 stays inconclusive and no E1 gate
is authorized by this integration. No dependency was added.
