# HEADD-Series L0 development instructions

Project instructions for Claude Code working on **HEADD-Series L0** (relational structure builder + E1′ experiment). This repo rebuilds the CDADE v1 baseline from the original repository with less code and fewer tools, then adds the graph layer. Read this before touching code. Keep edits surgical.

## Behavioral guidelines to reduce common LLM coding mistakes

> Tradeoff: these guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think before coding

Don't assume. Don't hide confusion. Surface tradeoffs.

- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity first

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.
- Ask: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical changes

Touch only what you must. Clean up only your own mess.

- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.
- Remove imports/variables/functions that YOUR changes made unused. Don't remove pre-existing dead code unless asked.
- The test: every changed line should trace directly to the user's request.

### 4. Goal-driven execution

Define success criteria. Loop until verified.

- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Port X from CDADE" → write a parity test against the original's output, then make it pass.

For multi-step tasks, state a brief plan:

```text
1. [Step] → verify: [check]
2. [Step] → verify: [check]
```

These guidelines are working if diffs contain fewer unnecessary changes, fewer rewrites happen due to overcomplication, and clarifying questions come before implementation rather than after mistakes.

---

## Project in one line

Test whether geographic adjacency **A** between the 13 health regions of Pará, fed to the CDADE ensemble as neighbour features, shortens outbreak detection lead time at a fixed false-alarm rate — and whether that gain vanishes under degree-preserving placebo graphs. Full protocol: `README.md` §5.

## Scope (deadline: 16/10/2026)

**In scope:** S (summing matrix), A (queen contiguity), placebo graphs, Φ as species layers (exploratory, real data only), the metapopulation simulator, the ported CDADE baseline, arms B0/B1/B2/B2-placebo (B-Gao and B3 optional), evaluation and statistics.

**Out of scope — do not implement without an explicit request:** mobility layer M (REGIC, SIVEP infection→notification network), GANF/GDN or any GNN, full hhh4, Project Tycho, sequential layer L4, phenotype emitter L5, SEIRS+ agent-based runs.

## Stack & invariants

- Python ≥ 3.12 · **uv** (env + deps) · **ruff** (lint + format) · **pytest**.
- **Removed from the CDADE stack on purpose** — do not reintroduce without asking:

  | CDADE tool         | Replaced by                                                                                      | Reason                                          |
  | ------------------ | ------------------------------------------------------------------------------------------------ | ----------------------------------------------- |
  | Hydra + OmegaConf  | one `.toml` per experiment, read with stdlib `tomllib` into a frozen dataclass                   | a few experiments, no config composition needed |
  | MLflow             | `results/<run_id>/` with `metrics.parquet` + `manifest.json` (config, seed, git hash, timestamp) | single user, local runs                         |
  | DVC                | raw data committed (≈230 KB); synthetic data regenerated from seeds                              | nothing large to version                        |
  | `just`             | the `uv run` commands below                                                                      | one less tool                                   |
  | Factory + Registry | a plain `dict[str, Callable]` in the module that owns the components                             | same lookup, no metaprogramming                 |
  | Quarto             | notebooks in `notebooks/` + README                                                               | reports are course deliverables, not a site     |

- **Raw data is immutable.** Never modify `data/raw/`. Derived data goes to `data/processed/` (gitignored, regenerable by one command).
- **Counts, not proportions.** Reconcile and aggregate counts; derive rates post hoc. S coherence is exact on this data — a test enforces it.
- **No look-ahead.** Every feature, threshold, and competence estimate at month _t_ uses data ≤ _t_ only. Anything estimated from data (placebo draws aside) is fitted on the training window.
- **Determinism.** Use `numpy.random.Generator`. One root seed per experiment; per-replicate seeds via `SeedSequence(root).spawn(n)`. Record seeds in the manifest.
- **One variable per arm.** Arms differ only in the relational information they receive. Pool, reconciliation, selection, and threshold stay identical across B1, B2, and B2-placebo.
- **Fixed false-alarm rate.** Thresholds are calibrated on null replicates to the same target FAR for every arm (pre-registered in the config) before lead time is compared.

## Commands

```bash
uv sync
uv run ruff check . && uv run ruff format --check .
uv run pytest
uv run python -m headd_l0.run configs/<experiment>.toml
```

## Layout (flat package, tests mirror modules 1:1)

```text
src/headd_l0/
  data.py        load SIVEP CSVs → long table (region × month × species); hierarchy spec
  graph.py       S; A from geobr + libpysal; row-normalised W; placebo rewiring; centralities
  simulate.py    metapopulation SIR (+ optional SEIRS variant); common random numbers; onsets
  inject.py      propagated injection on real series
  features.py    neighbour features (W·x_t, W·x_{t-1}, x − mean(neighbours)), local Moran, rolling EWS
  detectors.py   pool: PCA, LOF, KNN, HBOS, IF, MCD (from scratch)
  reconcile.py   bottom_up, mint_shrink
  select.py      competence, diversity, drift reset, active subset K*
  threshold.py   EVT/GPD threshold + FAR calibration on nulls
  evaluate.py    lead time, detection probability, observed FAR, AUC, AUC-PR, NAB
  stats.py       paired bootstrap, placebo rank, Friedman → Wilcoxon → DM → Cliff's δ
  run.py         config → arms → results/<run_id>/
configs/  data/raw/sivep/  data/processed/  results/  notebooks/  tests/
```

Target 150–300 lines per module; split only when a module exceeds ~400.

## Component contracts

- **Detector** (`detectors.py`): `fit(X) -> self`, `score(X) -> np.ndarray` (higher = more anomalous). Registered in `DETECTORS: dict[str, Callable]`. MCD is implemented from scratch (FAST-MCD C-steps); it must not delegate to `sklearn.covariance.MinCovDet`, but tests compare against it.
- **Reconciler** (`reconcile.py`): `summing_matrix(hierarchy) -> np.ndarray`; `reconcile(base, S, method) -> coherent`, with `method ∈ {"bottom_up", "mint_shrink"}`.
- **Selector** (`select.py`): per-window competence from pseudo-labels, diversity (Q-statistic), drift-triggered reset; returns the active subset K\*(w).
- **Threshold** (`threshold.py`): fits a GPD to score exceedances; `calibrate(null_scores, target_far) -> threshold`.
- **Graph** (`graph.py`): `adjacency() -> (A, names)` with names in the canonical order from `data.py`; `placebos(A, n, rng) -> list[np.ndarray]` preserving degree sequence and connectivity (fails loudly if a draw cannot be found).
- **Simulator** (`simulate.py`): `simulate(cfg, W, rng) -> SimResult` (frozen dataclass: `counts[13, 132]`, `twin_counts`, `onset[13]`, `seed_region`, `label ∈ {T, N}`, `params`). Noise types: `white`, `env`, `dem` (Gao et al. 2025, suppl. eqs 1–3). Weekly Euler–Maruyama → monthly sums; clip negative compartments at zero; binomial observation with testing rate θ.

## Approved protocol decisions

`docs/protocol-decisions.md` takes precedence over historical plan text.
D-G0 records E0 as inconclusive and authorizes B1*. E0* gates interpretation;
its current PA single-class failure must not be tuned away. Layer-0 injection
uses complete durations and coherent PA (regional sum and union labels).
Current commands and scope: `docs/development.md`.

## Porting from CDADE (the original repo)

Goal: extract methods, not architecture. Port only what arms B0–B2 need.

1. **One component at a time**, in this order: `data` → `reconcile` → `detectors` → `threshold` → `select` → `evaluate` → `stats`.
2. For each component: read the original, write a **parity test first** (same input, same seed → same output within a stated tolerance), then port the minimum code that passes it. Drop config knobs the E1′ experiment does not use.
3. Log each port in `MIGRATION.md`: component · original path · new path · parity check · what was dropped and why.
4. Do **not** port unless asked: Farrington, Top-k Eze, point-adjusted F1, Tycho loaders, MLflow/Hydra glue, or any code without a caller in the original pipeline (list it in `MIGRATION.md` instead).
5. **Historical parity gate (E0; superseded by D-G0/E0* above).** The original requirement was: before any E1′ result is interpreted, the rebuilt B1 must reproduce CDADE v1 per-task results on the 14 SIVEP tasks (13 regions + aggregate), using the original injection protocol: |ΔAUC-PR| ≤ 0.01 per task and the same method ranking. If it does not, stop and report the discrepancy — do not tune to match.

## Simulator rules

- Validate a **single region first**: reproduce Gao et al.'s T/N separation for AR1 and CV (suppl. Figs F–H). Test: median AR1 and CV of T windows > those of N windows, for each noise type.
- Coupling: λᵢ = βᵢ(t) · Σⱼ Cᵢⱼ Iⱼ/Nⱼ with C = (1 − ε)·I + ε·W. ε = 0 must yield zero spread from the seed beyond the endemic background — test this.
- Endemic background νᵢ is calibrated from real regional medians; store the calibration in `data/processed/` with the code that produced it.
- Onsets: seed region = month R0 crosses 1; other regions = first month the excess over the twin run exceeds 2 SD. Twin runs share the replicate's random stream except for the outbreak.
- Do not add `seirsplus` as a dependency. Its network model breaks on networkx ≥ 3 and is too slow for the replicate budget.

## Hypothesis-testing protocol (do not reorder)

Primary (synthetic bench, README §5.4):

```text
1. Paired bootstrap of Δ lead time (B2 − B1) per replicate, stratified by ε → 95% CI
2. Placebo rank: share of the 30 placebo graphs that B2 beats
3. Criterion: CI > 0 for ε > 0, no gain at ε = 0, B2 above 95% of placebos
```

Secondary (real SIVEP data, continuity with CDADE v1):

```text
1. Friedman omnibus on average ranks      → if p > .05, stop
2. Wilcoxon signed-rank, pairwise         → Bonferroni α/C(k,2)
3. Diebold-Mariano on predictive accuracy → HAC (Newey-West) variance
4. Cliff's delta effect size              → 95% bootstrap CI
```

## Task routing

- **background** — scaffolding, boilerplate, config stubs, docstrings.
- **default** — module implementation (loaders, detectors, features, metrics).
- **think** — theory-critical: SDE discretisation and metapopulation coupling, onset definitions, MinT, EVT/FAR calibration, META-DES competence, placebo rewiring validity, DM and Cliff's δ correctness. Hard-assign these here.
- **longContext** — cross-module synthesis: CDADE porting plans, `run.py` wiring, results write-up.

## Do / Don't

- DO read `README.md` §5 before touching `simulate.py`, `features.py`, or `run.py`.
- DO add a pytest case with every new public function.
- DO add dependencies only via `uv add`, and mention each one in the PR/commit message.
- DON'T compare arms at different false-alarm rates.
- DON'T reconcile on proportions.
- DON'T report point-adjusted F1 alone — lead time is primary; AUC-PR and NAB are secondary.
- DON'T expand the graph (add M, Φ, or GNNs) to rescue a null result.
- DON'T push, change access controls, or delete data; ask the user.

## Coding style

- Type hints on all public functions; Google-style docstrings.
- Frozen dataclasses for configs and results.
- Conventional Commits (`feat/fix/docs/refactor/test/chore`). Commit locally; do not push without explicit instruction.

## Definition of done (per component)

- [ ] Implemented with type hints + docstrings, ≤ 400 lines.
- [ ] Parity test (if ported) or behaviour test (if new) passing.
- [ ] `uv run ruff check .` and `uv run pytest` green.
- [ ] Referenced from a config by name, not imported ad hoc in `run.py`.
- [ ] Writes its outputs under `results/<run_id>/` with the manifest updated.
