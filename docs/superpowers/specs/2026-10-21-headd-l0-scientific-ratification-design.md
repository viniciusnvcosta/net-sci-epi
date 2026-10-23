# HEADD L0 scientific ratification and preliminary evidence design

**Date:** 21 October 2026

**Status:** Approved by the project author on 21 October 2026 for protocol/status amendment and read-only E0* diagnosis under the approved SDD+TDD plan. Prospective rules are recorded in D-RATIFY-2026-10-21; approval does not pass a scientific gate or authorize interpretation.

**Basis:** PR #3 at `194116d`, the preserved 30 September E0\* run, and the 20 October D-COST/D-REACH record.

## 1. Purpose and success criteria

The project needs a defensible 23 October preliminary report about whether geographic adjacency improves outbreak detection at fixed false-alarm rate. Layer 0 non-inferiority remains mandatory, and the report must include layer 1 (epidemic injection into real counts) and layer 2 (the synthetic bench) to claim a conclusive RQ1′ result. A valid negative result is conclusive; a failed scientific gate, incomplete run, or unavailable comparison is inconclusive. The report must not promise a positive finding.

This design settles protocol choices before effects are inspected, preserves earlier failed results, and orders the work needed to produce eligible evidence. It separates a **ratified rule** from a **gate passed on data** and from **interpretation authorized**. The current E0\* and real-data FAR failures remain failures. A complete bench alone cannot override them.

## 2. Evidence and constraints at the decision point

- D-G0 authorized the corrected `B1*` baseline and recorded E0 as inconclusive. D-E0*-R1 made the 13 regional tasks inferential and PA descriptive. The preserved `results/e0-star-scoring-20260930` run failed E0* against the causal z-score and failed FAR in three task/arm pairs. Its lower paired 95% AP-difference bound is −0.20186060618499926. A read-only calculation from its `metrics.parquet` gives mean regional ΔAP(B1\* − z-score) ≈ −0.131; B1* is lower in 12 of 13 regions. These values are diagnostics, not a basis for changing the gate.
- D-P5-IMPL fixed `P5-IMPL-2026-10-19-v1`, a deterministic equation fixture, and a monthly adaptation as technical conventions. Scientific ratification and G4 are pending. The archived Gao white-noise table has median CV(T)=0.7695323012078741 and CV(N)=0.8337873367675575. The official archive bytes are not currently local; recorded hashes and medians are historical evidence, not a fresh verification.
- D-COST froze 200 T and 200 N per noise/ε cell, 200 additional calibration N, and the same fixed T0000–T0099 for B2 and all 30 placebos. Its serial projection on the recorded WSL hardware is 82.29–104.74 hours, excluding some setup and publication work. D-REACH passed at ε=0.20 for all three noises. The full bench has not run.
- PR #3 supplies a gated descriptive exporter and the layer 2 reduced-design runner. Layer 1 epidemic injection and its runner are not implemented. The current exporter must continue to block inference on incomplete coverage or failed gates.

Sources: [protocol decisions](../../protocol-decisions.md), [Gao preparation](../../gao-source-preparation.md), [execution provenance](../../reference-provenance.md), and [global plan](../plans/headd-l0-global.md). Historical records remain dated and unchanged.

## 3. Proposed scientific amendments

### 3.1 P5 source target and G4

Ratify Gao supplemental equations 1–3 as the **equation target**, with the predecessor implementation used only to document divergences. Ratify `P5-IMPL-2026-10-19-v1` as a fixed _synthetic design profile_, not an estimate of Pará epidemiology or an exact reproduction of an upstream trajectory. Its effective population, rates, observation fraction, time conversion, burn-in, and onset conventions retain the provenance and limitations recorded in `docs/gao-source-preparation.md` and `tests/reference/gao_manifest.json`. Any change creates a new dated profile and invalidates comparability to runs using the old profile.

For **source characterization**, preserve the archived T/N labels and test AR1(T)>AR1(N) in white, environmental, and demographic noise. Test CV(T)<CV(N) in white and CV(T)>CV(N) in environmental and demographic noise. Match the six archived median pairs and source hashes at their recorded tolerance when the official bytes are available. Missing bytes mean `source_archive_verification=pending`, not a pass. The equation fixture independently checks one-step algebra; it does not establish T/N separation.

The monthly observed-incidence adaptation is a different observable. Report its prespecified 64 T/64 N per-noise AR1 and CV medians, valid-window counts, clipping frequency, incidence conservation, θ boundary behavior, and onset coverage without imposing the source table's CV signs on monthly counts. G4 approval requires the source/equation checks, complete monthly diagnostics, deterministic tests, and scientific review of the fixed-profile diagnostics. The monthly AR1/CV summaries do not automatically approve G4, and parameters or seeds may not be adjusted to obtain a preferred sign. This replaces the all-noise CV direction in `AGENTS.md` and the graph/simulation plan through a new dated protocol decision; until that amendment, G4 remains pending.

### 3.2 Zero-coupling equivalence and primary inference

Ratify an operational margin of **±1 month** for the paired mean restricted lead gain `B2 − B1*` at ε=0. For each preregistered noise stratum, the paired 10,000-draw percentile 95% bootstrap interval must lie strictly inside (−1,+1) month. Layer 1 applies the same test separately to each preregistered size `k ∈ {1,3,6}`; no favorable stratum is selected after seeing results. A confidence interval containing zero is insufficient. The margin is a design tolerance at monthly resolution, not a measured epidemiological quantity.

The positive-coupling criterion retains its order: paired bootstrap at ε>0, then strict rank against all 30 matched placebos, then the joint decision. Under the frozen subset, B2 and placebos use the same 100 T IDs; `29/30 > .95` and `28/30` does not. Report detection probability, censoring, unavailable timing, and effective denominators beside lead gain. Compare arms only where independent evaluation-null FAR is within the predeclared target/tolerance and the paired observations are complete. Preserve the layer 0 non-inferiority check and the ordered real-data secondary protocol.

### 3.3 Layer 1 design parameters

Ratify the coupled conventions in `P5-IMPL-2026-10-19-v1`, including `R0 ~ Uniform[1.2,1.8]`, as fixed synthetic design choices, **not** estimates for malaria in Pará. Retain D-GT2/D-GT4's local/imported infection-flow provenance, ν=0 for the outbreak component, `k ∈ {1,3,6}`, seed introduction months 72–118, truncation reporting, and imported-case onset rule. The observed flow is added to an immutable copy of real counts and PA is recomputed as the regional sum. Propose 100 paired T replicates for each predeclared noise/ε/k cell, with every active arm and placebo evaluated on the same IDs; D-GT3 retains 200 calibration and 200 evaluation null series per region, in disjoint streams. These counts must be recorded before layer 1 scoring. The layer 1 run waits for G4 and E0\*. Ratifying these design values does not pass G4, FAR, or the layer 1 evidence gate.

### 3.4 E0\*, real-data FAR, and D-GT3

Preserve the 30 September E0*/FAR failure and its immutable artifacts. Diagnose the regional AP differences, forecasts, detector orientation, feature causality, and null calibration without selecting a replacement score rule from those outcomes. A correction is eligible for a new gate run only when an independently justified implementation defect is reproduced by a failing test and fixed. Keep `baseline_id=B1*`; record a distinct code/profile version, seed, and run ID. If no defect is established or a new gate still fails, RQ1′ interpretation remains blocked. A later pass does not rewrite the historical failure.

Amend D-GT3 prospectively: a nonconvergent or invalid regional NB2 fit **fails closed** and marks that region/gate unavailable. Do not silently switch to an unspecified block bootstrap. A block-bootstrap null may be designed later as a separately ratified experiment; it is not a fallback in the 23 October protocol. The preserved E0\* run had convergent fits, so this amendment neither explains nor changes its failure. The fixed FAR target 1/60 and tolerance 1/300 are unchanged.

## 4. Gate and execution flow

1. Record the dated amendments above, update conflicting current instructions and the global plan's status, and verify that historical entries and artifact hashes remain intact.
2. Complete read-only E0\* diagnosis. If an independently demonstrable defect exists, implement and test its correction under a separate plan, then run a new immutable E0* evaluation. If E0\* or real-data FAR fails, stop the inferential path and publish an inconclusive report.
3. Verify the official P5 source bytes when available, run the fixed single-region diagnostics, and review G4. Missing evidence or failed checks leave G4 pending/failed. Confirm that the coupled run references the ratified profile and hash before layer 1 generation.
4. Once prerequisite gates pass, complete the mandatory layer 0 comparison, implement layer 1 under its own spec/plan, and run layers 1 and 2. The layer 2 run uses the frozen D-COST IDs and checks synthetic FAR on independent evaluation N **after** execution and **before** inference. D-REACH remains a separate pre-arm reach check.
5. To address the serial cost without changing the experiment, a separate execution plan may partition the frozen work by stable noise/ε/replicate addresses. Before full execution, compare a small parallel shard set with a serial reference for identical seeds, counts, scores, and metrics. Publish immutable shards; merge only if every predeclared cell, arm, ID, denominator, and hash is present exactly once. Partial shards never authorize inference.
6. The exporter reports gate statuses and descriptive evidence even on failure. Inferential tables and a conclusive positive **or negative** RQ1′ statement require completed layer 0, layer 1, and layer 2 evidence, comparable FAR, E0\*, G4, D5, reach, and all applicable gates. If any fail or work is incomplete by 23 October, the preliminary report says inconclusive with the precise reasons.

This is a dependency order, not a claim that the work fits the deadline. The existing E0\* failure, absent layer 1 runner, and 82–105 hour serial layer 2 projection make a conclusive 23 October report uncertain.

## 5. Work split and verification

The first implementation cycle after this spec is a **protocol/status amendment and E0\* diagnostic**. Separate design and implementation cycles own (a) any validated baseline correction, (b) layer 1 injection and runner, and (c) parallel bench execution/merging. No optional B-Gao, Φ/B3, SEIRS, mobility, or GNN work enters the critical path. No full bench starts solely because a decision is ratified; its prerequisite gates must pass.

The protocol amendment is accepted when the decision record, AGENTS instructions, architecture, global plan, graph/simulation plan, experiment plan, README, and report language agree on current versus historical status; exact source hashes, thresholds, profile IDs, and D-COST IDs agree; and no document calls technical validation a gate pass. E0\* diagnostics are read-only and reproducible from the preserved artifacts. Later implementation cycles require targeted red/green tests, full Ruff/pytest verification, manifest/coverage checks, and serial/parallel identity before claims of completion. Existing results and raw data are never overwritten. Commits remain local; no push or merge is part of this design.
