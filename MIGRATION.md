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

| Finding | Evidence (runtime unless noted) |
|---|---|
| `missing_14_tasks` | evaluation yields one task, `sivep`: labels are `mask.max(axis=1)`, shape (132,) (D7) |
| `single_class_test_labels` | the 26 test months are all anomalous, so AP = 1.0 for every method and the ranking is all ties |
| `stage_failed:pipeline_detect_{lof,knn,hbos}` | wrappers pass `random_state` to PyOD 3.6.1, which rejects it; `run_detect`'s fallback then raises `TypeError` |
| `stage_failed:pipeline_detect_mcd` | `X[indices]` on a DataFrame raises `KeyError` (D3) |
| `stage_failed:pipeline_reconcile_min_t` | 13×13 S against the single `score` column raises `ValueError` in matmul (D1, D2) |
| D3 | PCA wrapper negates PyOD's score: outliers score lower than inliers |
| D4 | `EVTReconciler.fit` raises `ValueError: too many values to unpack` |
| D5 | reconcile input is `leaf_forecasts.csv` with the single column `score` |
| D6 | shifting scores from t = 90 changes blended scores at t = 80–84, 87, 89 |
| D8 | with Friedman p = 0.32, DM and Cliff's δ still run; Wilcoxon stops |
| D9 | NAB/F1 threshold is the median of evaluated scores (static) |

Other observations: leaf sums equal the PA series in all 132 months; the
default injection leaves 408 negative cells; `evaluate` uses 26 test months
while baselines score 27 and are truncated; the pinned rerun matches the local
`results/metrics/sivep/metrics.json` (a clue, not a golden) for the rows it
recomputes. Recurrent `b6`–`b8` were not rerun.

## Ports

| Component | Original path | New path | Parity check | Dropped and why |
|---|---|---|---|---|
| data | `cdade/data/sivep.py` (`load_raw`, `prepare_counts`, `prepare_state_counts`, `_LEAVES`) | `src/headd_l0/data.py` | `tests/test_data.py::test_counts_match_original_exactly`: counts, PA series, test totals, leaf order and months equal the pinned export, tolerance zero | Registry/plugin loader, canonical `entity/timestamp/level/value` layer and Hydra config (replaced by `configs/data.toml`). Added: missing region-months, regions or months and PA/regional mismatches raise instead of being filled with zeros |
| reconcile | `cdade/reconciliation/summing_matrix.py`, `bottom_up.py` | `src/headd_l0/reconcile.py` | `tests/test_reconcile.py::test_s_matches_original` and `test_bottom_up_exact`: S equals the exported 14×13 matrix and bottom-up reproduces PA = leaf sum, tolerance zero | Registry classes and the 13×13 S inside `min_t.py`/`bottom_up.py` (the MinT one raised in the audit). MinT(Shrink) is new, per D2: diagonal target, Schäfer–Strimmer λ as in `hts::MinT`, solve-based projection, no clipping; it reconciles NB2 count forecasts, never scores (D5) |
| forecast | none (new, D5/D-GT3) | `src/headd_l0/forecast.py` | Behaviour tests in `tests/test_forecast.py`: design by hand, parameter recovery, training-only fit, recorded non-convergence | NB2 with trend and two harmonic pairs, Poisson starting values, per series |

MinT on the real SIVEP data (2026-09-27, diagnostic only): all 14 NB2 fits converge, λ̂ = 0.100. The independent PA forecast differs from the sum of regional forecasts by a median of 848 cases/month in months 60–131; MinT moves the PA forecast by a median of 26% and 409 of 1,848 reconciled means are negative (406 in months 60–131; CARAJAS, LAGO DE TUCURUI, MARAJO II, METROPOLITANA III, RIO CAETES, TOCANTINS, XINGU, MARAJO I, PA). Per D2 they are not clipped; residuals y − P·μ̂ stay coherent.

## Not ported

| Original | Reason |
|---|---|
| `data/tycho.py`, `data/loaders/{tycho,uci_394,uci_501}.py` | Tycho/UCI out of scope |
| `baselines/farrington.py` (`b1`) | Farrington excluded |
| `baselines/static_topk.py` (`b4`) | Top-k Eze excluded |
| `baselines/recurrent_baseline.py`, `models/recurrent.py` (`b6`–`b8`) | recurrent baselines excluded |
| `detectors/{ocsvm,cblof,cof,sos}.py` | outside the six-detector pool |
| `registry.py`, `data/{base,dataset_paths,prepare,validate_schema}.py`, Hydra `main`s, MLflow logging, `dvc.yaml`, `justfile`, `reporting/`, `ablation/`, `evaluation/{stats_cli,stats_matrix}.py` | glue replaced by TOML, `results/<run_id>/` and plain dicts |
| `ensemble/` | DVC stage whose output `evaluate` does not read |
| `selection`: `NaiveTopKSelector`, `generate_windowed_labels`, `windowed_diversity`, `scan_for_drift`, Page-Hinkley | no caller in the pipeline |
| `reconciliation/identity.py`, `reconciliation/evt.py` | no caller in the default pipeline; `evt.fit` raises (D4) |
