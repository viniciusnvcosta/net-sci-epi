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
