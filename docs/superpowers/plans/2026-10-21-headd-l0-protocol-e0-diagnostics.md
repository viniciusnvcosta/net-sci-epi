# HEADD L0 Protocol Ratification and E0* Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Record the approved prospective scientific rules and produce reproducible, read-only diagnostics of the preserved E0*/FAR failure without authorizing inference.

**Architecture:** Append dated protocol amendments and align current documentation while preserving historical records. A small standalone diagnostic module reads existing artifacts, validates their provenance and pairing, and emits JSON to stdout; it never fits, scores, calibrates, or writes into a source run. A dated evidence note separates numerical observations, implementation audit, and decisions about subsequent work.

**Tech Stack:** Python >=3.12, existing NumPy/pandas/PyArrow, stdlib argparse/hashlib/json, uv, Ruff, pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-21-headd-l0-scientific-ratification-design.md`, approved by the user in chat on 21 October 2026 ("aprovado, inicie"). This approval covers the written design, not a gate pass.

## Global Constraints

- Existing results and raw data are never overwritten. Commits remain local; no push or merge is part of this design.
- Preserve the 30 September E0*/FAR failure and its immutable artifacts.
- Keep `baseline_id=B1*`; a subsequent eligible correction requires a distinct code/profile version, seed, and run ID.
- The fixed FAR target `1/60` and tolerance `1/300` are unchanged.
- Zero-coupling equivalence: paired 10,000-draw percentile 95% bootstrap interval strictly inside `(−1,+1)` month, separately by noise and, for layer 1, `k ∈ {1,3,6}`.
- `P5-IMPL-2026-10-19-v1` is a fixed synthetic design profile; `R0 ~ Uniform[1.2,1.8]` is not an estimate for Pará malaria.
- D-COST remains 200 T/200 evaluation N plus 200 calibration N per noise/ε cell; all 30 placebos and matched B2 use T0000–T0099.
- Layer 1 proposes 100 paired T per noise/ε/k cell and 200 calibration/200 evaluation null series per region in disjoint streams; this plan does not implement or run layer 1.
- A nonconvergent or invalid regional NB2 fit fails closed; there is no unspecified block-bootstrap fallback.
- Conclusive positive or negative RQ1′ statements require mandatory layer 0 and completed layers 1 and 2 with all applicable gates passing. Incomplete work or failed gates by 23 October means inconclusive.
- No optional B-Gao, Φ/B3, SEIRS, mobility, or GNN work enters the critical path.

## Review Focus

- Missing or modified historical artifacts must prevent a verified diagnostic claim; Task 2 tests missing files and hash mismatches.
- PA's single-class labels and undefined AP remain descriptive; Task 2 tests PA exclusion and complete regional pairing.
- Reordered, duplicated, missing, or nonfinite regional rows must never manufacture a paired gain; Task 2 tests row invariance and rejects malformed keys/values.
- Floating-point FAR boundaries must use the established inclusive comparison; Task 2 exercises both boundaries and a value outside each boundary.
- Read-only diagnosis must preserve source bytes and keep inference blocked even on a favorable fixture; Task 2 snapshots source files and tests a favorable synthetic input.

---

## Workspace and evidence map

Continue in the existing linked worktree `.worktrees/ratification-design`, branch `docs/headd-l0-ratification-design`, based on `ef0f838` / PR #3 head `194116d5cc789fcae342559353386043cd838b81`. At planning time the user has unstaged formatting changes in the design spec and `headd-l0-architecture.md`. Preserve them, stage only owned changes, and do not require a destructive reset to obtain a clean checkout.

Historical source: `/home/vinvs/projects/net-sci-epi/.worktrees/second-execution/results/e0-star-scoring-20260930`. It is absent from the design worktree. Require an explicit CLI source path; do not copy it into a new experiment or infer it from the working directory.

Pinned historical evidence: `docs/evidence/pr-2/e0-star-summary.json` contains the run/code/reference identity and five artifact hashes. Additional consumed artifact hashes must be recorded in the diagnostic output as newly observed hashes, distinguished from the five previously pinned hashes.

Current source audit targets: `e0_scoring.py` (`_score_panels`, `_calibrate_scores`), `forecast.py`, `features.py`, `reconcile.py`, `detectors.py`, `select.py`, and `threshold.py`. Historical behavior must be checked with `git show 017bd1a0d6cd3ecf1e8d8efe55a4826c234b3132:<path>`; current code is not proof of historical behavior.

### Task 1: Record prospective amendments and align current status

**Files:**

- Modify: `docs/protocol-decisions.md`, `AGENTS.md`, `README.md`, `docs/development.md`.
- Modify: `docs/superpowers/specs/2026-10-21-headd-l0-scientific-ratification-design.md` (approval status only), `docs/superpowers/specs/headd-l0-architecture.md`.
- Modify: `docs/superpowers/plans/headd-l0-global.md`, `docs/superpowers/plans/headd-l0-graph-simulation.md`, `docs/superpowers/plans/headd-l0-experiments.md`.

**Interfaces:**

- Consumes: approved spec §§1–5, existing decision/provenance records and `tests/reference/gao_manifest.json`.
- Produces: dated current decision `D-RATIFY-2026-10-21` with explicit supersession links; no programmatic gate status is changed.

- [ ] **Step 1: Capture documentary discrepancies.** Read the files above and list the current all-noise CV rule, unspecified NB2 fallback, pending R0/equivalence choices, incomplete layer requirements, and stale implementation status. Preserve dated historical passages; identify which current instructions need a supersession pointer.
- [ ] **Step 2: Append the dated decision and synchronize current instructions.** Copy exact values from the spec. Source characterization is AR1(T)>AR1(N) in all three noises, CV(T)<CV(N) in white, CV(T)>CV(N) in env/dem. Missing official bytes leave source verification pending. Monthly 64 T/64 N diagnostics per noise do not independently pass G4. Preserve profile/source hashes verbatim. Record ±1-month equivalence, strict placebo ranking (29/30 passes; 28/30 fails), R0 range, NB2 fail-closed rule, prospective E0* requirements, and mandatory three-layer completion. Mark the spec approved without declaring any gate passed.
- [ ] **Step 3: Describe the layer 1 schedule accurately.** With the existing noise set and ε grid `{0,.05,.20}`, 100 T across 27 noise/ε/k cells means 2,700 outbreak realizations before arm/placebo scoring. Do not apply layer 2's 200 T schedule to layer 1. Record that precision, cost, stable seed addresses, cross-cell null reuse, and disjoint calibration/evaluation streams must be settled in its own design before scoring; this amendment supplies no unstated power guarantee or reuse rule.
- [ ] **Step 4: Verify documentary consistency.** Run `git diff --check`; search the changed documents for `G4`, `CV`, `fallback`, `R0`, `equivalence`, `inconclusive`, `200`, and `100`. Manually confirm that current statements agree and historical failures/hashes remain intact. Do not add a brittle prose-matching pytest suite for this documentation change.
- [ ] **Step 5: Commit owned documentation changes.** Use `docs: ratify prospective HEADD L0 scientific rules`; exclude pre-existing user formatting changes from staged hunks.

### Task 2: Add a minimal read-only artifact diagnostic

**Files:**

- Create: `src/headd_l0/e0_diagnostics.py` (target <=300 lines).
- Create: `tests/test_e0_diagnostics.py`.
- Read only: `docs/evidence/pr-2/e0-star-summary.json`, historical run artifacts, existing data hierarchy and FAR comparison implementation.

**Interfaces:**

- Consumes: `source: Path`, `evidence: Path`; canonical tasks from `headd_l0.data.hierarchy().leaves`.
- Produces: `diagnose_e0(source: Path, evidence: Path) -> dict`, JSON-serializable with `schema_version=1`, source identity, `pinned_sha256`, `observed_sha256`, `regional_ap`, `mean_delta_ap`, `n_regions_b1_lower`, `far`, `fits`, `partitions`, `forecast`, `score_checks`, `historical_gates`, and `interpretation_allowed=False`.
- Produces: `main() -> int`, CLI `python -m headd_l0.e0_diagnostics --source <path> --evidence docs/evidence/pr-2/e0-star-summary.json`; success emits strict JSON to stdout and returns 0. Invalid/missing evidence emits a reason to stderr, returns nonzero, and emits no successful JSON. Success means diagnostic completion, never a scientific pass.

- [ ] **Step 1: Write synthetic artifact fixture and failing behavior tests.** Use tmp_path artifacts with the historical schemas, canonical task ordering, 28 metric rows (13 paired regions plus PA), and disjoint null IDs. Pin the fixture's five hashes in a synthetic evidence file. Do not commit copies of historical null panels.

Required assertions:

```python
assert report["interpretation_allowed"] is False
assert len(report["regional_ap"]) == 13
assert report["n_regions_b1_lower"] == 12
assert report["mean_delta_ap"] == pytest.approx(-0.11)
# Fixture: twelve differences -0.12 and one +0.01; PA AP is undefined.
assert set(report["pinned_sha256"]) == set(evidence["artifact_sha256"])
```

Name the tests `test_paired_regional_summary_excludes_pa`, `test_metric_row_order_is_irrelevant`, `test_missing_duplicate_nonfinite_or_unknown_regional_rows_rejected`, `test_missing_or_changed_pinned_artifact_rejected`, `test_far_inclusive_boundaries`, `test_read_only_and_favorable_fixture_never_authorize_inference`, and `test_cli_emits_strict_json_or_nonzero_error`. Parameterize malformed rows and hash defects. Snapshot every source file before and after the diagnostic; require equal bytes and directory membership.

- [ ] **Step 2: Verify RED.** Run `uv run pytest -o addopts='' tests/test_e0_diagnostics.py -q`; expect failure because the diagnostic module does not exist.
- [ ] **Step 3: Implement `diagnose_e0` and `main`.** Verify pinned hashes and run/code/reference identity before interpreting tables. Require exactly one metric row per canonical task/arm, valid regional AP/class counts/window 60–131, and consistent paired labels; allow PA's undefined AP. Pair by task, compute B1* minus zscore AP, and retain prevalence/denominators.

Read `far.parquet` (26 rows), `fits.parquet` (14 rows), `null_partitions.parquet` (400 rows), `forecast.npz`, `injection.npz`, and `scores_{injected,calibration,evaluation}.npz` with `allow_pickle=False`. Check task/arm axes explicitly. Summarize fit validity, positive finite forecast means, unique/disjoint 200+200 partition identities and spawn keys, finite scores, regional AP recomputation from saved injected scores/masks, and evaluation FAR recomputation with saved thresholds. Compare stored and recomputed values; expose disagreements as diagnostic findings, never repair them. Include the unchanged historical CI lower bound and gate status from the pinned manifest; do not regenerate a bootstrap or fit/calibrate a replacement model. Use `json.dumps(..., allow_nan=False)` and convert descriptive undefined values to null. No output directory, fitting, pipeline execution, RNG selection, or alternate threshold/score search belongs in this module.

- [ ] **Step 4: Verify GREEN.** Run the new tests and `uv run ruff check src/headd_l0/e0_diagnostics.py tests/test_e0_diagnostics.py`; expect all tests passing and no lint errors. Format only the two owned Python files and rerun their format check.
- [ ] **Step 5: Commit.** Stage only these two files; use `feat: add read-only E0 artifact diagnostics`.

### Task 3: Publish reproducible diagnostics and audit the causal path

**Files:**

- Create: `docs/evidence/2026-10-21-e0-diagnostics/diagnostics.json`.
- Create: `docs/evidence/2026-10-21-e0-diagnostics/README.md`.
- Modify: `docs/development.md`, `docs/superpowers/plans/headd-l0-global.md` (evidence links/current status only).

**Interfaces:**

- Consumes: Task 2's JSON stdout and historical source identified above.
- Produces: dated descriptive evidence with the exact command, source path, source run SHA, diagnostic code SHA, source hashes, audit citations, and explicit stop/next-cycle decision.

- [ ] **Step 1: Verify the historical diagnostic.** Run Task 2's CLI against the explicit source path and capture stdout to a temporary file. Require matching pinned hashes, 13 paired regions, 12 regions with lower B1* AP, approximately −0.131 mean ΔAP, historical CI lower bound −0.20186060618499926, and the failed FAR pairs ARAGUAIA/B1*, XINGU/B1*, RIO CAETES/zscore. Investigate discrepancies as provenance/diagnostic issues; do not change expected evidence to force agreement.
- [ ] **Step 2: Audit forecasts, orientation, feature causality, and calibration.** Inspect historical and current code separately. Trace months 0–59 training and 60–131 evaluation; local residual feature construction; detector higher-is-more-anomalous contracts; selection stream indices; calibration-only threshold estimation; independent evaluation N and strict score exceedances. Cite exact code paths/commit identities and existing tests. Saved arrays alone cannot prove training causality. Run focused existing tests with `uv run pytest -o addopts='' tests/test_forecast.py tests/test_features.py tests/test_detectors.py tests/test_reconcile.py tests/test_select.py tests/test_threshold.py -q`. Label present-code test results as current verification, not historical execution.
- [ ] **Step 3: Write the evidence note and publish new files once.** Use exclusive creation for `diagnostics.json` and the note; existing destinations require a new dated/versioned evidence path, never overwrite. Describe numerical findings, provenance, causal audit, limitations, and any independently justified suspected defect. A bad score alone is not an implementation defect. Record whether a correction investigation is justified; do not implement a correction or run a prospective gate in this cycle. Add evidence links and keep E0*/FAR failed, G4 pending, full bench unexecuted, and interpretation blocked.
- [ ] **Step 4: Complete verification.** Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, and `git diff --check`. Recompute source hashes and require identity with the pre-diagnostic inventory. Re-run the diagnostic and compare parsed JSON for deterministic equality. Report default pytest marker exclusions explicitly; these checks do not establish G4 or full scientific validation.
- [ ] **Step 5: Commit and report.** Use `docs: record preserved E0 failure diagnostics`. Report changed files, verification evidence, pending gates, and the next eligible cycle. No push, merge, full bench, or inferential export.

## Separate downstream cycles (not executable tasks in this plan)

1. **Baseline correction, conditional on an independently justified defect:** separate spec/plan; failing reproduction test before a surgical fix; preserve B1* identity with distinct code/profile provenance; new immutable prospective E0*/FAR run. If no defect is established or the new gate fails, stop inference and report inconclusive.
2. **P5/G4 evidence and layer 1:** complete source-byte/equation checks and fixed monthly diagnostics, obtain scientific G4 review, and design the injection/runner separately. Resolve the 2,700-T workload, precision limits, shared null policy, stable seed addressing, truncation/onsets, PA coherence, and per-k equivalence before scoring. G4 and E0* must pass before the layer 1 run.
3. **Verified parallel layer 2 execution:** separate plan preserving frozen D-COST counts/IDs. Prove serial/shard identity for seeds, counts, scores, and metrics before full execution. Immutable shards and exact-once coverage/hash validation precede merge; independent evaluation-null FAR precedes inference.
4. **Report eligibility:** mandatory completed layer 0 plus layers 1/2 and all applicable gates; a valid negative finding is conclusive. Otherwise publish precise descriptive limitations and an inconclusive 23 October report.

## Plan self-review

The executable tasks cover the approved spec's first cycle (§§3.4, 4.1–4.2 diagnostic portion, 5). Task 1 records the other ratified rules without mistaking them for passed gates. G4 evidence, a conditional baseline correction, layer 1, and parallel bench implementation remain explicitly separate cycles rather than speculative implementation tasks. Every public function in Task 2 has behavior/CLI coverage; documentation-only Task 1 uses review rather than prose tests. No runtime, power, gate pass, or completion by the deadline is promised.
