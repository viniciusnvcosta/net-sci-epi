# P5 G4 evidence for scientific review — 22 October 2026

Fresh official-source byte/label/median checks, complete fixed monthly diagnostics,
deterministic tests and exact replay are available. **G4 remains pending explicit
scientific review; `interpretation_allowed=false`.** This packet requests review
and records no scientific gate decision. E0* and FAR remain failed; mandatory
layers are incomplete, so RQ1′ remains inconclusive.

[verification.json](verification.json) contains the full strict-JSON source result,
requested/effective URLs, acquisition times/sizes/hashes, all clipping denominators,
command identities/output-log hashes, exact replay comparison and input/artifact
hashes. It supersedes older source-byte availability statements for this execution;
the frozen profile manifest and historical records remain unchanged.

## Identity and source acquisition

Execution code: `13dad73e52b5f0ede341578ae08e2dca7f3b638e`.
Fixed profile: `P5-IMPL-2026-10-19-v1`; root seed 42; monthly branch 1;
64 T and 64 independent N per noise. No profile, seed, count, window or sign rule
was changed. Sources were streamed into exclusive new files under
`data/processed/gao-p5-v1/`. Cache/results remain local and ignored by Git.

The [official record API](https://zenodo.org/api/records/10967222) identifies
record 10967222, DOI `10.5281/zenodo.10967222`, archive size 200,527,444 bytes
and license metadata `cc-by-4.0`. Its literal metadata version field is absent;
the fixed record was used, without following a concept DOI. This is an observation
of record metadata, not an audit of every archived file's license.

| Input | Observed bytes | Expected = observed SHA-256 |
| --- | ---: | --- |
| `Code.zip` | 200527444 | `3b519acdbc598c6129a3c5ea49715800e8dd4bc84d4644ad578bd2ee720e3e35` |
| `supplement.pdf` | 7049878 | `ea467449c4cc4de2e4e0d23a3053188f24d99017f1cb58b009f1d8e442f0e8a6` |
| `gao_single.npz` equation fixture | 4962 | `3d40f2edb962e67482dfeb6d229528317bc2f5220e90befed2930cbf366d3c27` |

Archive URL: [exact content endpoint](https://zenodo.org/api/records/10967222/files/Code.zip/content).
The [supplement DOI](https://doi.org/10.1371/journal.pcbi.1012782.s001)
resolved to the official PLOS Google Storage PDF; the complete requested/effective
URL is preserved in JSON. An initial restricted-network metadata attempt failed
with DNS resolution errors; the authorized network retry succeeded. No mismatched
or partial cache file was replaced. Metadata/DOI discovery responses are retained
in the local execution ledger. Monotonic elapsed times are authoritative; UTC wall
clock timestamps show small adjustments during this session.

Only required CSV members and Figure S5/S6/S7 scripts were read from the ZIP;
no upstream code was executed and no full archive extraction occurred. In
`Code/Code/Figures/Figure S5.R`, `Figure S6.R` and `Figure S7.R`, lines 8–10
state first 6000 transcritical (1), last 6000 null (0); lines 21–22 index
T=`1:6000`, N=`6001:12000`. Exact text/member hashes are in JSON.

## Archived source characterization

Each required table has 12,000 finite rows and its exact pinned hash. All six
T/N median pairs match at absolute tolerance `1e-12` (observed values equal the
frozen medians). The labels and white CV direction are preserved.

| Noise | Feature | T median | N median | Archived direction |
| --- | --- | ---: | ---: | --- |
| dem | AR1 | 0.5047929896716941 | -0.0206288632503289 | T > N |
| dem | CV | 1.019406821444585 | 0.57233734032215 | T > N |
| env | AR1 | 0.5880703663584995 | -0.09465763109109755 | T > N |
| env | CV | 0.8569538002486781 | 0.6270792751140045 | T > N |
| white | AR1 | 0.4589695136544245 | 0.06335934371952405 | T > N |
| white | CV | 0.7695323012078741 | 0.8337873367675575 | T < N |

These tables characterize **400 observations of infected state I**, without
retrofitting their direction rules to monthly counts. No new source-I trajectory
experiment was run. The equation fixture tests algebra separately at `rtol=0`,
`atol=1e-10`; it does not establish source trajectory or T/N separation parity.

## Monthly observed-incidence diagnostics

The primary package is local `results/g4-evidence-20261022/`; replay is
`results/g4-evidence-20261022-replay/`. Each contains exactly manifest,
source checks, counts, replicates and summary artifacts, with no inference file.
Both completed, each with 1,152 sequential simulator calls: 384 primary
realizations (192 T, 192 independent N) plus 768 theta-control realizations.
Paired twins are auxiliary and do not increase the independent N denominator.

All six cells completed IDs 0–63. Arrays are `[3,2,64,132]` int64; theta=.5,
epsilon=0, one region, uncalibrated hazard `1e-6/day`. Statistics use months
`[63,75)`, the 12 months strictly before designated T onset month 75. N uses the
same fixed window; its absent onset -1 is expected.

| Noise | Label | CV median | AR1 median | Valid CV | Valid AR1 |
| --- | --- | ---: | ---: | ---: | ---: |
| white | T | 0.478137883008598 | 0.3523729259051298 | 64/64 | 64/64 |
| white | N | 0.4926123776179972 | 0.3049280031910976 | 64/64 | 64/64 |
| env | T | 0.3903897463077025 | 0.4844513549643182 | 64/64 | 64/64 |
| env | N | 0.3652178994021459 | 0.33658741275439225 | 64/64 | 64/64 |
| dem | T | 0.5866626544627442 | 0.45642695808955336 | 64/64 | 64/64 |
| dem | N | 0.563809693003362 | 0.4271358581098069 | 64/64 | 64/64 |

Every cell has zero invalid CV/AR1 windows. All five technical checks hold for
384/384 primary addresses: 132 finite nonnegative integer counts; theta=0 zeros;
theta=.5 bounded by theta=1 trials; design onset (192/192 T at 75, 192/192 N at -1);
and null/all-time or T/pre-ramp `[0,72)` equality with its paired twin. Counts,
twins and both theta controls are retained; all original simulator scientific
status fields remain pending/blocked.

Clipping of S is zero throughout. The table below reports primary-run I clipping
by cell and phase, with the sum of actual integration steps as denominator.
`outbreak` is the simulator phase name for both T and N. Whole-state coordinate
fraction equals half the reported I fraction because S clipping is zero.
The full JSON retains all 54 cell/observation/phase summaries, including theta=0/1,
steps, coordinate steps and both coordinate counts/fractions. Per-replicate
fractions remain in Parquet.

| Noise | Label | Phase | I clipped / steps | I fraction |
| --- | --- | --- | ---: | ---: |
| white | T | burn_in | 250/4032 | 6.200397% |
| white | T | outbreak | 1478/43968 | 3.361536% |
| white | T | twin | 2594/43968 | 5.899745% |
| white | N | burn_in | 206/4032 | 5.109127% |
| white | N | outbreak | 2829/43968 | 6.434225% |
| white | N | twin | 2829/43968 | 6.434225% |
| env | T | burn_in | 0/4032 | 0.000000% |
| env | T | outbreak | 0/43968 | 0.000000% |
| env | T | twin | 0/43968 | 0.000000% |
| env | N | burn_in | 0/4032 | 0.000000% |
| env | N | outbreak | 0/43968 | 0.000000% |
| env | N | twin | 0/43968 | 0.000000% |
| dem | T | burn_in | 116/4032 | 2.876984% |
| dem | T | outbreak | 743/43968 | 1.689865% |
| dem | T | twin | 1279/43968 | 2.908934% |
| dem | N | burn_in | 104/4032 | 2.579365% |
| dem | N | outbreak | 1335/43968 | 3.036299% |
| dem | N | twin | 1335/43968 | 3.036299% |

White and demographic clipping require scientific review. No approved numerical
clipping/validity cutoff exists here, and none was invented after viewing these
values. Monthly medians have no imposed source CV sign gate. SimResult does not
expose a new per-realization latent-flow artifact: conservation/calendar splitting,
partial intervals/leap days, once-monthly integerization and observation boundary
algebra are covered by deterministic tests; monthly realized flow totals were not
independently reconstructed.

## Execution, replay and checks

Commands ran from the worktree root with:

```sh
UV_PROJECT_ENVIRONMENT=/home/vinvs/projects/net-sci-epi/.venv UV_CACHE_DIR=/tmp/headd-g4-uv PYTHONPATH=src uv run --no-sync ...
```

- `pytest -o addopts='' tests/test_reference.py tests/test_simulate.py tests/test_features.py -q`: 76 passed in 1.35s, exit 0. This includes six fixture rows, covariance/no extra sigma, clipping, calendar/conservation/observation checks, replay and no-future-data feature behavior.
- `python -m headd_l0.sim_validation configs/g4_validation.toml`: completed primary package, exit 2, 34.21467129001394s monotonic elapsed.
- Same CLI with the ledger's `g4-replay.toml`: completed distinct replay package, exit 2, 34.27699254502659s. The replay TOML differs only in run ID.
- Exact comparison: every array dtype/value/axis, all 384 replicate rows including seeds/statistics/projections/controls, six summary rows and source JSON equal. All four non-manifest artifact hashes are also equal. Manifest comparison excludes only timestamps/run IDs and the corresponding config-file identity, after checking parsed config equality outside run ID and each config hash. Cache/fixture/profile/config hashes and every first-package artifact hash are unchanged before/after replay.
- `ruff check .`: exit 0; `ruff format --check .`: exit 0, 51 files already formatted.
- `pytest`: 466 passed, 1 deselected in 188.81s, exit 0. Default exclusions are `slow`, `reference`, `integration`; the targeted deterministic command cleared addopts.

The runner's immutable manifests correctly say `deterministic_tests=not_run_by_runner`
and `scientific_review=not_requested`; this external packet links executed tests
and requests review without rewriting those manifests. Published exit 2 signals
blocked interpretation and pending review, not a failed generation or gate approval.

| Primary artifact | SHA-256 |
| --- | --- |
| `counts.npz` | `3b2c17a6e82046e55eeeae2d0ea5e0ea831b8380f67ff2d5137713d5449d6078` |
| `manifest.json` | `5a40a77b8165926a7b50be3f101d5ca78194116220a2d3ead3731c53a1f70d3b` |
| `replicates.parquet` | `9c2a2cb2f28573056019e3eb665251e902b108f9d8fe5e03dbe76a0008fad5af` |
| `source_checks.json` | `cf80ab54a05d583f351fb5d377ff9e1fa60f0b6e8e15e689829e465b1100f94f` |
| `summary.parquet` | `14197e2e8583aeb60bef395806336e52cfb18a0f41a853a4174c51ea34ba788d` |

Source/config/code hashes, replay manifest identity, installed package versions,
command logs and their hashes are in JSON. Original user spec-formatting edits,
protected implementation/profile/fixture bytes and preserved E0* artifacts remain
unchanged. No baseline fix, prospective E0*, coupled/inferential run, push, merge
or G4-passed decision is part of this packet.
