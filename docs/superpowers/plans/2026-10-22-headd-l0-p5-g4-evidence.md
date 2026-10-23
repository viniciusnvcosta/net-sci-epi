# HEADD L0 P5/G4 Evidence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Preserve the user's chosen SDD+TDD method; obtain review of this plan before implementation.

**Goal:** Assemble reproducible official-source checks, fixed single-region monthly diagnostics and technical verification for scientific G4 review, keeping E0*/FAR failures and blocked interpretation unchanged.

**Architecture:** A read-only source verifier checks explicit local archive/supplement paths against the frozen manifest. A separate validation CLI reuses the existing simulator and EWS calculation, records every frozen replicate address and publishes a complete immutable evidence directory. Scientific G4 approval is a later explicit decision on that directory, never an automatic consequence of successful execution.

**Tech Stack:** Python >=3.12, stdlib tomllib/hashlib/json/csv/zipfile/ctypes, existing NumPy/pandas/PyArrow/SciPy, uv, Ruff, pytest. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-21-headd-l0-scientific-ratification-design.md` §§3.1, 4.3 and 5, approved in chat. Binding current decision: `docs/protocol-decisions.md`, D-RATIFY-2026-10-21. Numeric/seed authority: `tests/reference/gao_manifest.json`. First-cycle evidence: `docs/evidence/2026-10-21-e0-diagnostics/README.md`.

## Global Constraints

- Existing results and raw data are never overwritten. Commits remain local; no push or merge is part of this design.
- Preserve `results/e0-star-scoring-20260930`, E0*/FAR failed and `interpretation_allowed=false`. No baseline correction or prospective E0* run is in this cycle.
- Preserve `P5-IMPL-2026-10-19-v1`, its numeric profile, source/fixture hashes and fixed seed tree. No parameter/seed search, changed window, added replicate or replacement source to obtain a preferred result.
- Source characterization preserves archived T/N labels: AR1(T)>AR1(N) in white/env/dem; CV(T)<CV(N) in white and CV(T)>CV(N) in env/dem. All six T/N median pairs use absolute tolerance `1e-12`.
- Equation fixture: six rows, `rtol=0`, `atol=1e-10`; demographic diffusion has no extra sigma multiplier. It checks algebra, not source trajectories or T/N separation.
- Monthly diagnostics use 64 T/64 independent N per noise, 132 observed months, epsilon=0, one region, theta=.5, the fixed uncalibrated single-region hazard `1e-6/day`, and 12 months strictly before the designated T onset. Do not substitute regional endemic calibration or layer-1 settings.
- Do not impose source CV directions on monthly counts. Invalid statistics are explicitly masked, excluded from their medians and counted; no minimum-valid-count or clipping acceptance threshold is invented here.
- Source/equation checks, complete monthly diagnostics, deterministic tests and scientific review are required for G4. Missing evidence remains pending; technical defects remain failures. No software path in this cycle emits `G4=passed` or enables inference.
- No detector scoring, E1 bench, layer-1 injection/runner, coupled simulation, parallel execution, exporter amendment or optional arm belongs to this cycle.

## Review Focus

- Absent bytes, changed archive members or reversed halves must never become a source pass: Task 1 tests pending/mismatch/row/median cases.
- Independent N and paired T twins must remain distinguishable, with the exact frozen addresses: Task 2 tests seed identities and reordering/replay, and publishes full coverage.
- Undefined monthly CV/AR1 and all-invalid strata must not become zero-valued evidence of separation: Task 2 tests validity/counts/null medians.
- A destination appearing at publication must not be replaced or expose a partial completed package: Task 2 tests actual no-replace publication at that boundary.
- Complete technical evidence still requires scientific approval: Task 2 tests unconditional inference refusal; Task 3 records pending review and explicit review prerequisites.

---

## Workspace, inputs and artifact responsibilities

Continue in `.worktrees/ratification-design`, branch `docs/headd-l0-ratification-design`, execution base `addca52852903aff0cbb72bc39aca601d256fc62`. Preserve the two existing unstaged user formatting diffs in the ratification spec and architecture. Do not reuse or change the first cycle's SDD directory; initialize this plan's own ledger at execution time.

Existing code: `simulate.py` owns SimConfig/SimResult/simulate and the numerical integrator; `features.py:rolling_ews` owns SD/CV/AR1 formulas. Existing `configs/simulation.toml` names the profile and validation root seed/counts but has no CLI. The older `configs/sim_single.toml` command is historical future text; do not add another competing simulator entry point. No production integrator or original fixture change is planned.

New ownership: `gao_sources.py` verifies external bytes without downloading/executing/extracting upstream code. `sim_validation.py` orchestrates fixed diagnostics and immutable publication; it does not own new SDE equations. `configs/g4_validation.toml` supplies paths/run identity and references the existing simulation TOML. Tests mirror the two new modules. Target each module at 150–300 lines; hard limit 400, with a focused split only if necessary.

Inputs are explicit paths under `data/processed/gao-p5-v1/`: `Code.zip`, `supplement.pdf`, and optional acquisition metadata. These are regenerable local source caches, never `data/raw/` and never committed. Resolve paths from the execution directory and record absolute paths in provenance; document running from the worktree root.

On 22 October the read-only official API `https://zenodo.org/api/records/10967222` returned record DOI `10.5281/zenodo.10967222`, title `Code and Data for Early detection of disease outbreaks and non-outbreaks`, `Code.zip` size 200527444 bytes and content URL `https://zenodo.org/api/records/10967222/files/Code.zip/content`. Its metadata version field is absent: do not require a literal version field or follow a concept DOI to latest. This metadata lookup did not verify archive bytes. The exact archive SHA-256 and supplement DOI/hash remain those in the frozen manifest; metadata MD5 is not a substitute.

Expected evidence directory `results/g4-evidence-20261022/` contains `manifest.json`, `source_checks.json`, `counts.npz`, `replicates.parquet`, `summary.parquet`. `counts.npz` stores counts and twin_counts with axes `[noise,label,replicate,month] = [3,2,64,132]`, plus theta-zero/theta-one control arrays for those same addresses, and Unicode axis labels. Never store object arrays. The 384 primary realizations comprise 192 T and 192 independent N; twins are paired auxiliary data, not additional independent N.

### Task 1: Verify official source bytes against the frozen evidence

**Files:** Create `src/headd_l0/gao_sources.py`, `tests/test_gao_sources.py`. Read only `tests/reference/gao_manifest.json`, `tests/reference/gao_single.npz` and provided external files.

**Interfaces:** `verify_sources(archive: Path, supplement: Path, manifest: Path) -> dict` returns strict-JSON-compatible source checks with component statuses, expected/observed hashes, table row counts, fixed label ranges, recomputed medians, direction/tolerance checks and reasons. No filesystem writes or network calls. Missing paths yield pending components; supplied corrupt/mismatched bytes yield failed components. Only fully verified source components can pass; this result never approves G4.

- [ ] **Step 1: Write behavior tests first.** Build synthetic ZIP/PDF inputs and a temporary manifest with their hashes; preserve real fixture files. Use 12,000-row synthetic tables, exactly 6,000 T then 6,000 N, with independent known AR1/CV medians. Required cases: `test_absent_sources_remain_pending`, `test_hash_mismatch_fails_before_characterization`, `test_complete_sources_preserve_archived_label_directions`, `test_bad_table_members_rows_or_values_fail`, `test_reversed_halves_fail_expected_medians`, `test_source_read_is_immutable`.

```python
assert missing["status"] == "pending"
assert missing["source_archive_verification"] != "passed"
assert verified["status"] == "passed"
assert verified["tables"]["white"]["CV"]["T"] < verified["tables"]["white"]["CV"]["N"]
assert verified["tables"]["env"]["CV"]["T"] > verified["tables"]["env"]["CV"]["N"]
```

Parameterize archive/supplement/three-member mismatches, truncated ZIP, missing/duplicate expected ZIP member, wrong row count, missing AR1/CV columns, nonfinite values and a median outside absolute `1e-12`. In synthetic fixtures update only synthetic pins when isolating semantic validation from hash validation.

- [ ] **Step 2: Verify RED.** `uv run pytest -o addopts='' tests/test_gao_sources.py -q` must fail because the new verifier is absent.
- [ ] **Step 3: Implement the verifier.** Read source/fixture expectations directly from the pinned manifest, not duplicated literals. Verify archive and supplement independently; an absent supplement must not conceal a verified archive or falsely complete aggregate source checks. Read the three exact CSV members with zipfile, without extractall or upstream code execution. Use the declared row halves, raw unscaled CV and medians over all 6,000 rows per class; do not drop nonfinite rows, relabel classes, detrend or compute features from fresh trajectories. Record source errors without claiming a new verification from cached summary numbers. Verify the local equation-fixture file hash separately; numerical algebra remains exercised by existing tests.
- [ ] **Step 4: Verify GREEN and owned lint/format.** Run the targeted tests and Ruff on the two files; require all passing. No remote download belongs in pytest.
- [ ] **Step 5: Commit** only the new files: `feat: verify frozen Gao source evidence`.

### Task 2: Produce the fixed monthly diagnostic package

**Files:** Create `src/headd_l0/sim_validation.py`, `tests/test_sim_validation.py`, `configs/g4_validation.toml`. Read only `configs/simulation.toml`, `tests/reference/gao_manifest.json`, and existing simulator/features modules.

**Interfaces:** A frozen `G4Config` holds `run_id: str`, `output_dir: Path`, `simulation_config: Path`, `archive_path: Path`, `supplement_path: Path`. `run_validation(config_path: Path) -> Path` loads/validates it, creates the evidence package and returns the final path. `main() -> int` implements `python -m headd_l0.sim_validation configs/g4_validation.toml`. Return 2 for published evidence still pending/failed scientific eligibility; malformed config, runtime failure or occupied destination also returns nonzero with a precise reason. No return value is a scientific pass.

The new config selects `run_id="g4-evidence-20261022"`, `output_dir="results"`, `simulation_config="configs/simulation.toml"` and the two cache paths above. Reject changes to frozen root_seed=42, replicates_per_noise_label=64, profile, theta, epsilon and single-region settings rather than exposing tuning flags. Record the exact config/manifest/source-code/fixture hashes, git SHA, dependency versions and source-check results in the output manifest. Do not rewrite the historical status fields of the profile manifest or SimResult.

- [ ] **Step 1: Write tests before code.** Required tests: `test_config_rejects_frozen_design_overrides`, `test_seed_addresses_match_the_manifest`, `test_window_excludes_onset_and_n_uses_design_month`, `test_undefined_statistics_have_validity_counts_and_null_medians`, `test_independent_n_is_not_the_t_twin`, `test_partial_or_duplicate_coverage_cannot_complete`, `test_publication_refuses_destination_appearing_at_commit`, `test_complete_evidence_still_requires_scientific_review`, `test_cli_reports_pending_or_invalid_evidence`.

Assert exact monthly branch keys `(1, cell, replicate)` with cell order white:T, white:N, env:T, env:N, dem:T, dem:N. Use real small simulations to check replay and independent N versus T twins; use hand-computed windows to check statistics, not a full 64-replicate scientific run inside each unit test. A window `np.arange(1,13)` has mean 6.5, CV `np.std(window, ddof=1)/6.5` and AR1=1; all-zero windows have invalid CV/AR1, zero valid counts and null medians. Changing month 75 or later must not change statistics from `[63:75]`. A failed source check and a favorable monthly fixture must both preserve `interpretation_allowed=False` and `G4 != passed`.

- [ ] **Step 2: Verify RED.** `uv run pytest -o addopts='' tests/test_sim_validation.py -q` must fail for the missing runner.
- [ ] **Step 3: Implement fixed generation and summaries.** Spawn all three root branches, reserve source=0/calibration=2 and use monthly=1; spawn all six cells then 64 replicates each. Use `simulate(SimConfig(...), np.zeros((1,1)), np.random.default_rng(seed))`; epsilon=0 and fixed hazard. Obtain each independent N from its own cell stream. Retain T twins separately. Replay each primary address at theta=0 and theta=1 for observation controls (1,152 total simulator calls including 384 primary calls), without consuming another primary stream or changing its address.

The designated T crossing is month 75 under the fixed profile. Derive/check it from the manifest's ramp/calendar, never from a favorable observed detection time. T statistics use the 12 preceding observed months; independent N uses the same calendar months despite its own onset=-1. Reuse rolling_ews for CV/AR1 and its validity masks, with independent hand-calculated tests. Record per-replicate onset, window, values/masks, entropy/spawn_key and projection counts/step denominators. Emit exactly six summary rows with all 64 requested IDs per cell, valid/invalid counts per statistic and medians over valid values only. If none are valid, median is null. Report N onset absence as expected, not missing T coverage. Reject incomplete/duplicate generation; do not silently skip a failed realization.

Technical evidence includes 132 finite nonnegative integer counts per primary/control, theta-zero counts zero, theta-one nonnegative integer trials and observed .5 counts bounded by matched theta-one trials, N/twin equality, T/twin pre-ramp equality, and the recorded clipping frequencies by phase and coordinate. Do not assert stochastic counts equal continuous incidence. Calendar/flow conservation and one-step algebra are evidenced by the existing deterministic tests in Task 3; SimResult does not expose latent-flow arrays, so this plan does not invent a latent conservation result from observed counts.

- [ ] **Step 4: Implement immutable publication and verify GREEN.** Stage the package in a sibling temporary directory, close files, verify exact coverage and artifact hashes, and publish with Linux `renameat2(RENAME_NOREPLACE)` via stdlib ctypes. A precheck plus Path.rename/os.rename is insufficient. On unsupported no-replace operation fail explicitly; do not overwrite. Test the destination-appears boundary against the real filesystem and preserve the competing destination bytes. Keep staging/diagnostic information on a failed publication; no completed final package may be exposed. Run owned tests, Ruff and format checks. `manifest.json` distinguishes run completion from source checks, `G4=pending`/`failed`, `scientific_review=not_requested`, and `interpretation_allowed=false`; no inference.json is emitted.
- [ ] **Step 5: Commit** the three new files: `feat: export fixed single-region G4 diagnostics`.

### Task 3: Acquire official bytes, execute once and prepare scientific review

**Files:** Create `docs/evidence/2026-10-22-p5-g4/README.md` and `docs/evidence/2026-10-22-p5-g4/verification.json`. Modify `docs/development.md`, `docs/gao-source-preparation.md`, `docs/superpowers/plans/headd-l0-global.md` with dated current status/evidence links only. New local cache/results directories above remain uncommitted.

**Interfaces:** Consumes Tasks 1/2 and existing deterministic tests. Produces an immutable results directory, source-acquisition provenance and a committed review note identifying exact artifact hashes, checks, limitations and pending decisions. This task requests/prepares review; it cannot provide scientific approval on the author's behalf.

- [ ] **Step 1: Acquire official bytes without overwriting existing files.** Read metadata from the fixed official record; fetch Code.zip from its exact content URL and follow the supplement DOI from the frozen manifest. Stream into newly created cache paths with exclusive creation, record requested/effective URLs, record ID, timestamps, byte sizes and hashes. Existing files may only be reused after hash verification; mismatched or partial files are preserved and recorded as failures, not replaced. A new acquisition attempt uses a fresh cache directory/config. Do not execute R scripts or unpack the entire archive. Record acquisition failures honestly; do not substitute a different version, mirror, cached medians or predecessor repository. No download or license-verification claim is made merely from the planning-time metadata lookup.
- [ ] **Step 2: Run source checks and deterministic evidence.** Invoke the verifier and record its full strict-JSON result. Check the archive-contained Figure S5/S6/S7 label declarations against the archived row convention in the manifest, recording exact members/lines without executing them. Run `uv run pytest -o addopts='' tests/test_reference.py tests/test_simulate.py tests/test_features.py -q` on the committed implementation and retain command, git/source identity, marker settings, exit/output and log hash. This covers fixture/covariance, clipping, calendar partial intervals/leap days, once-monthly integerization, observation boundaries and deterministic behavior; test results are not a scientific G4 pass.
- [ ] **Step 3: Execute the frozen monthly CLI.** Run `uv run python -m headd_l0.sim_validation configs/g4_validation.toml`; expect a complete package and exit 2 while review is pending. Missing source bytes do not authorize inference and need not prevent the independently useful monthly diagnostics; publish source pending/failed distinctly. A numerical/structural generation failure must not create a completed package. Do not reduce counts for the deadline. Record elapsed time and all effective denominators; no fresh source-I trajectory experiment or full bench is required here.
- [ ] **Step 4: Verify exact replay and final checks.** Use a distinct replay run_id with the same seed/profile/source inputs and compare counts/control arrays, per-replicate statistics/projections, seed identities and summary tables for exact equality. Exclude only timestamp/path/run_id/duration provenance fields from the equality comparison. Rehash all cache/fixture/profile inputs and first-package artifacts before/after. Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run pytest`, and `git diff --check`; report default marker exclusions explicitly. Do not repeat those successful checks unless code changes or a concrete unresolved concern requires it.
- [ ] **Step 5: Publish the scientific-review packet and commit.** Create the note/verification JSON once, without replacing an existing evidence destination. Include expected/observed hashes, all six archived median pairs, six monthly summaries/valid counts, clipping/controls/onset coverage, deterministic-test evidence, immutable result/config identities, and an explicit distinction between source I and monthly incidence. Missing bytes/checks remain missing; unusual monthly summaries are reported without tuning or inventing a direction gate. Commit owned docs only: `docs: record P5 G4 evidence for scientific review`. No automatic dated decision saying G4 passed is part of this commit.

## Review decision and stopping rule

Present the completed packet for explicit scientific review. A later dated decision may record G4 passed only after every applicable source/equation/diagnostic/test requirement is reviewed; otherwise keep pending/failed with exact reasons. Lack of an approved numerical clipping/validity acceptance cutoff is not permission to invent one after inspecting the summaries.

Even a future G4 pass leaves the preserved E0*/FAR failures in place. This cycle never enables layer 1 or an inferential E1 run. A conclusive positive or negative RQ1′ statement still requires all mandatory layers/gates; failures or incomplete work at 23 October mean an inconclusive preliminary report. User review of this implementation plan is separate from scientific review of results not yet generated.

## Plan self-review

Spec §3.1 is covered by Task 1 source checks, Task 2 monthly evidence and Task 3 deterministic checks/review packet. Spec §4.3's explicit scientific review remains a subsequent decision; no task can fake it with a process exit code. Other spec workstreams are excluded explicitly. The five Review Focus cases map to Task 1/2 tests or Task 3 review boundaries. Existing simulator/feature code and both original user diffs remain untouched; no new statistical or numerical profile choice is introduced.
