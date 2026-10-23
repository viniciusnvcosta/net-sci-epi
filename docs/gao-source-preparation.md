# Gao single-region source preparation (29/09/2026)

## Current evidence — 22/10/2026

The [scientific-review packet](evidence/2026-10-22-p5-g4/README.md) records fresh
verification of official archive/supplement bytes, pinned table hashes, all six
archived median pairs and Figure S5/S6/S7 labels. Fixed monthly diagnostics
completed 64 T/64 independent N per noise with exact replay and deterministic
test evidence. Clipping/validity summaries are retained without a new acceptance
cutoff. G4 remains pending explicit scientific review; interpretation is blocked.
The dated source/profile records below and frozen manifest remain historical,
unchanged records; their older availability statements do not describe this run.

The 29/09 source record below is preserved; the dated technical profile added
on 19/10 authorizes implementation and technical validation only under
[D-P5-IMPL](protocol-decisions.md#d-p5-impl--perfil-técnico-p5-19102026).
Scientific ratification and G4 remain pending, with
`interpretation_allowed=false`. The [Gao et al.
supplement](https://doi.org/10.1371/journal.pcbi.1012782.s001), SHA256
`ea467449c4cc4de2e4e0d23a3053188f24d99017f1cb58b009f1d8e442f0e8a6`,
and [official Zenodo record 10967222, v1](https://doi.org/10.5281/zenodo.10967222),
`Code.zip` SHA256
`3b519acdbc598c6129a3c5ea49715800e8dd4bc84d4644ad578bd2ee720e3e35`,
were verified locally on 29/09. The earlier evidence collection is dated
28/09; no new download or simulation was made for this integration.

## Source equations and numeric predecessor

Supplement page 1, equations 1–3, uses drift
`(Λ−β(t)SI−μS, β(t)SI−(α+μ)I)`: transmission is mass action `βSI`, not
`βSI/N`. White noise has independent additive amplitudes `(σS,σI)`;
environmental noise has `(σS S,σI I)`. For demographic noise set `f=βSI`,
`a=Λ+f+μS`, `b=−f`, `c=f+(α+μ)I`, `d=sqrt(ac−b²)` and
`e=sqrt(a+c+2d)`. Equation 3 uses `B=[[a+d,b],[b,c+d]]/e`, yielding
`BBᵀ=[[a,b],[b,c]]`. It specifies no extra `σ` factors. Its algebraic
critical β is `μ(α+μ)/Λ`; conversion to frequency-dependent β requires an
explicit population denominator that Gao does not supply for Pará.

Gao refers to [Chakraborty et al. (2024)](https://doi.org/10.1098/rsif.2024.0199)
for parameterization. The [pinned predecessor code](https://github.com/AmitKChakraborty/EWSofInfectiousDiseases/tree/2856a304584b1e723881be70d951d3781f9a4478/Training_Data_Generation)
uses `Λ=100`, `α=μ=1`, initial `(S,I)=(500,7)`, 100 source-time-unit
burn-in, Euler–Maruyama `dt=0.01`, horizon 1500 and saved spacing 1.
It samples `β0~triangular(0,0.005,0.01)`, null slope
`~triangular(0,(βc−β0)/3000,(βc−β0)/1500)`, T slope
`~triangular((βc−β0)/1500,(2βc−β0)/3000,(2βc−β0)/1500)`, where
`βc=0.02`, and independent `σS,σI~triangular(0,0.5,1)` per replicate.
These distributions are source facts, not a fixed HEADD profile or proof that
the predecessor generated the exact Gao batches. The physical meaning of its
time unit remains unspecified. A day label in a Gao plot does not establish a
seven-day numerical step or a monthly calendar conversion. The predecessor
supplies no testing rate, endemic immigration, seasonality or 132-month design.

The predecessor executable differs from the supplement: demographic Brownian
increments are already scaled by `σS,σI` before `B`, giving covariance
`B diag(σS²,σI²) Bᵀ dt` rather than equation 3 covariance. Negative infected
states are randomly reset (`Uniform(0,0.5)` in white; `Uniform(0.1,1)` in
environmental/demographic, with environmental threshold I<0.1), whereas
the HEADD contract clips negative states
to zero. Burn-in carries mutated `S0,I0` across replicates and updates `S0`
before computing the `I0` drift. `seed=0` is assigned but not applied; both
NumPy and Python global RNGs are used. The transition marker selects the
second sampled `β>βc`, not the exact crossing. These differences need a chosen
parity target before a deterministic one-step fixture can be derived.

## Frozen feature characterization

Supplement Table C and Figures F–H concern 400 observations of infected state
**I**, not integrated incidence. Gao Methods puts T windows at the transition
and N windows at a sampled endpoint; the archived feature tables lack the
sampled parameter/seed metadata. Archived
`Code/Code/Simulation Code/5EWSI/5EWSI_white.R` lines 20–22 calculate sample
SD and `CV=SD/mean`, with the same formulas in env/dem scripts. Table C prints
CV as percent, changing its scale but not its ordering. `Figure S5.R`,
`Figure S6.R` and `Figure S7.R` under `Code/Code/Figures/` label rows 1–6000
T and 6001–12000 N at lines 8–10 and 21–22. These are features of I, not
monthly incidence or predecessor Lowess residuals.

| Table in `Code/Data/Simulation/Training/EWSI/` | SHA256 | AR1 median T / N | CV median T / N |
| --- | --- | ---: | ---: |
| `EWSI_white_training.csv` | `c2d2684af45c975c1813ad243de2799cfaeb35b66f9734ac3ac32dc598fa82e5` | 0.4589695136544245 / 0.06335934371952405 | 0.7695323012078741 / 0.8337873367675575 |
| `EWSI_env_training.csv` | `079f4720537722cad787b78be27b81ac94483c97c53dddd237ad60b5d5946714` | 0.5880703663584995 / −0.09465763109109755 | 0.8569538002486781 / 0.6270792751140045 |
| `EWSI_dem_training.csv` | `7039d780069cf2c28350a9d55b7d9617527f8af54c699a190ae7605ef819f840` | 0.5047929896716941 / −0.0206288632503289 | 1.019406821444585 / 0.57233734032215 |

The archived **white CV(T) < CV(N)** contradicts the planned all-noise
`median(CV_T)>median(CV_N)` gate. D-P5-IMPL qualifies that requirement for
technical source characterization by preserving the archived labels and
directions. Scientific replacement of the historical gate remains pending
ratification in [protocol-decisions.md](protocol-decisions.md).
These medians describe frozen archive tables, not fresh simulation or monthly
validation.

To reproduce the table hashes and medians, obtain v1 `Code.zip` from the
linked Zenodo record, verify the archive hash above and run this read-only
command with its path. Python `statistics.median` averages the two center
values in each 6000-row half.

```sh
python3 - /path/to/Code.zip <<'PY'
import csv, hashlib, io, statistics, sys, zipfile
with zipfile.ZipFile(sys.argv[1]) as archive:
    for noise in ('white', 'env', 'dem'):
        member = f'Code/Data/Simulation/Training/EWSI/EWSI_{noise}_training.csv'
        payload = archive.read(member)
        rows = list(csv.DictReader(io.StringIO(payload.decode())))
        assert len(rows) == 12000
        medians = {label: {key: statistics.median(float(row[key]) for row in half)
                           for key in ('AR1', 'CV')}
                   for label, half in (('T', rows[:6000]), ('N', rows[6000:]))}
        print(noise, hashlib.sha256(payload).hexdigest(), medians)
PY
```

## Historical decision prerequisites (29/09/2026)

Task 2 Step 1 is partial. Choose the scientific parity target (supplement
equations, predecessor executable, or an explicitly corrected model) and
establish deterministic input states, dt, innovations, expected one-step output
and provenance. The exact Gao generator/batch metadata is not established.
Resolve demographic sigma scaling, infected-state resets, burn-in, crossing
and physical time mapping before generating a fixture.

The monthly adaptation separately needs an approved latent incidence definition
(infection flow versus demographic events), integerization rule and binomial
testing rate; rounding per step and per month have different variance. Fix
calendar start, partial intervals at month boundaries and leap days, innovation
handling, N/transmission conversion, initial states, endemic/seasonal
parameters, training length and T/N windows. Stochastic rounding of accumulated
nonnegative infection flow is a proposal only. The full single-region profile
must be approved before Task 2 Steps 2–6; the coupled profile and R0 range
before Task 3 or layer 1. No `gao_single.npz` or simulator result exists.
The planned machine-readable `gao_manifest.json` was still pending on 29/09.
The dated technical resolution below supersedes this preparation status only;
it does not supply scientific ratification.

## Technical profile P5-IMPL-2026-10-19-v1

The [manifest](../tests/reference/gao_manifest.json) is the machine-readable
profile. Every value below is fixed before production simulation. The
supplement and archive are absent locally on 19/10; their hashes and medians
are carried from the verified 29/09 record above, not claimed as freshly
recomputed. No new external source was downloaded or redistributed.

Target the supplement's equations 1–3 with unscaled demographic diffusion;
the predecessor is a non-target. Evaluate coefficients at the same left
endpoint, apply lower clipping only and report clipped-coordinate frequency.
No random resets; zero demographic covariance gives zero diffusion.
Recovered individuals leave the two-state S,I subsystem.

### Deterministic equation fixture

The self-generated [fixture](../tests/reference/gao_single.npz) has SHA-256
`3d40f2edb962e67482dfeb6d229528317bc2f5220e90befed2930cbf366d3c27`.
Rows are `white:T, white:N, env:T, env:N, dem:T, dem:N`; state order is S,I.
Each starts from `(500,7)`, Λ=100, α=μ=1, dt=0.01, σ=(0.4,0.6) and
standard Gaussian innovations z=(0.25,−0.75), multiplied by sqrt(dt) once.
β is 0.015 for T and 0.005 for N. These are independent test inputs, not
states recovered from an official trajectory. T/N name the fixed source
scenarios below; a single row does not establish a transition.

| Noise | Label | Expected S | Expected I |
| --- | --- | ---: | ---: |
| white | T | 495.485 | 7.340 |
| white | N | 495.835 | 6.990 |
| env | T | 500.475 | 7.070 |
| env | N | 500.825 | 6.720 |
| dem | T | 496.2299408118578 | 6.74561406756831 |
| dem | N | 496.4892099426444 | 6.6019005286399945 |

The manifest lists all NPZ keys/shapes: float64 numbers, Unicode labels,
no pickle; compare with `rtol=0, atol=1e-10`. Expected states/diffusion use
60-digit Decimal arithmetic, checked independently by eigendecomposition.

### Fixed source experiment (implementation convention)

Λ=100, α=μ=1, initial S=500,I=7, burn-in 100 source units, dt=0.01,
horizon 1500 and saved spacing 1 retain the predecessor's documented scales.
Reset each replicate to the initial state; burn in at β=.005 with preceding
innovations, retain the terminal state and reset the clock. Fixed σS=.4,
σI=.6, βT(t)=.005+.00002t and βN(t)=.005 are conventions, not recovered
Gao parameters; dem ignores σ. Continuous crossing is t=750, βc=.02,
followed immediately by β>βc, not a second sampled exceedance.

Save I at t=1,...,1500. Both T and matched N characterization windows use
t=350,...,749 (400 values strictly before T crossing), without detrending.
The fixed N endpoint replaces unknown archived endpoints. Nominal **28 days
per source unit** is a convention: t_source=t_days/28, rates divide by 28
(the linear β slope by 28²), and white/env amplitudes by sqrt(28).
Demographic covariance uses converted rates. This source experiment lasts
longer than 11 years; the monthly profile is a separate adaptation.
Algebraic N=Λ/μ=100 gives
βfrequency=100βmass, preserving βmass SI; N is a denominator, not a census
population or a bound on S+I.

Source characterization preserves archived labels and all six median pairs,
absolute tolerance `1e-12`, including white CV(T)<CV(N). A requested archive
gate must fail if original bytes are absent. Fresh simulated medians and
valid counts are diagnostics; unknown upstream batch parameters preclude
claiming their exact reproduction.

### Monthly adaptation (implementation convention)

This profile is a separately parameterized adaptation of the equations.
The following values are design conventions, not Gao facts or estimates of
Pará's epidemiology; their scientific ratification remains pending.

| Quantity | Fixed value / semantics |
| --- | --- |
| Calendar | 2009-01-01 inclusive to 2020-01-01 exclusive; Gregorian, 132 months, leap days included |
| Training / monitoring | Months 0–59 / 60–131; single-region validation first, then 13 canonical regions |
| Population / initial state | Effective N=100000 per region; S=99993,I=7; identical initialization before each burn-in, not inferred from case counts |
| Time / rates | Day; recovery α=1/14, effective turnover μ=1/365 (not human life expectancy), Λ=μN per day |
| Burn-in | 365 days with null β, endemic hazard and seasonality; shared by each outbreak/twin pair |
| Transmission | βfrequency=R0(α+μ); single-region βmass=βfrequency/N; coupled λi=βi Σj Cij Ij/Nj |
| T / N | R0 starts at 0.8; seed ramps linearly to 1.6 from week 313 to week 365 (weeks are 7 elapsed days); N/twin remain at 0.8; other regions keep their null β |
| Seed / coupling | Seed index 0 for technical validation; ε=0 for one region; coupled values 0,.05,.20 |
| White / environmental | σS=σI=1 person/sqrt(day) for white; σS=σI=.01/sqrt(day) for env; demographic covariance has no extra σ |
| Endemic hazard | Single-region ν=1e-6/day; total infection flow f=(λ+ν(t))S transfers S to I |
| Seasonality | ν(t)=ν[1+.1 cos(2πt/365.25)], phase 0; β has no seasonal multiplier |
| Testing | θ=.5; observe integerized latent incidence once with a binomial quantile |
| Layer-1 convention | ν=0; R0 uniform[1.2,1.8]; initial Iseed=7, Inonseed=0; these values do not approve D-GT2/D-GT4 for scientific inference |

Effective turnover supplies susceptible replacement; these N/rate conventions
control incidence magnitude/depletion and do not establish geographic realism.
In epidemic-only layer 1, I=0 with zero infection pressure stays zero even
under white noise, satisfying the no-spontaneous-case control. This adaptation
does not apply to source-equation parity.

Use the union of start-anchored seven-day and month boundaries, including
burn-in at t=−365 and the final endpoint. Each adjacent pair has its actual
dt, left-endpoint coefficients and independent Gaussian innovations×sqrt(dt).
Its flow belongs entirely to its containing month; no day is dropped or
full-week innovation reused for a partial interval.

Sum nonnegative infection flow×dt, not prevalence or demographic-noise events.
Integerize once per region-month: `floor(L) + (u_round < L-floor(L))`, then
use an inverse binomial CDF with θ=.5 and `u_observe` in (0,1).
θ=0/1 yields 0/all trials. Preallocate Gaussian arrays by interval/region/channel
and uniforms by month/region/round-or-observe, with separate burn-in; twins
share arrays without conditional RNG consumption.

Seed onset is the month of continuous R0=1 followed by R0>1; remote onset is
the first observed excess over the twin >2SD (twin training SD, ddof=1).
SD=0 requires positive excess; N/missing onset is −1. Monthly diagnostics
use 12 months strictly before seed onset and matching N months; insufficient
windows are invalid.

The manifest fixes the later training-only endemic calibration: ν in [0,1/7]
per day, 128 nulls, 30 bisection iterations, tolerance `max(1,.1*target)`,
common innovations and explicit failure without widening the bracket.
Save targets/errors, parameters/hashes and seeds; ν/θ are not identifiable
separately. No calibration is executed in Task 2.

### Validation and authorization boundary

The manifest fixes seed 42, `SeedSequence.spawn` branches and PCG64: 64
replicates per noise/label for diagnostics, independent N and shared T/twin
innovations. It also fixes SD/CV/AR1 formulas and invalid-window handling.
Technical checks cover equations, covariance, calendar/flow conservation,
observation extremes, clipping and determinism. Fresh separation is diagnostic;
no tuning is authorized. Scientific ratification/G4 remain pending,
E0*/FAR failures unchanged and `interpretation_allowed=false`.

### One-step fixture reproduction

Run from the repository root in a clean checkout. This creates only the
project's generated NPZ; it uses no production simulator or external arrays.
The fixed ZIP metadata written by `numpy.savez` and explicit float64 dtype
make regeneration byte-stable in the recorded environment (NumPy 2.5.3).

```sh
uv run python - <<'PY'
from decimal import Decimal, getcontext
from hashlib import sha256
from pathlib import Path
import numpy as np

getcontext().prec = 60
D = Decimal
states, betas, drifts, diffusions, expected = [], [], [], [], []
noise_labels, labels = [], []
for noise in ("white", "env", "dem"):
    for label, beta in (("T", D("0.015")), ("N", D("0.005"))):
        s, i, dt = D(500), D(7), D("0.01")
        flow = beta * s * i
        drift = (D(100) - flow - s, flow - 2 * i)
        if noise == "white":
            diffusion = ((D("0.4"), D(0)), (D(0), D("0.6")))
        elif noise == "env":
            diffusion = ((D(200), D(0)), (D(0), D("4.2")))
        else:
            a, b, c = D(100) + flow + s, -flow, flow + 2 * i
            determinant_root = (a * c - b * b).sqrt()
            denominator = (a + c + 2 * determinant_root).sqrt()
            diffusion = (
                ((a + determinant_root) / denominator, b / denominator),
                (b / denominator, (c + determinant_root) / denominator),
            )
        output = [
            x + v * dt + (row[0] * D("0.25") - row[1] * D("0.75")) * dt.sqrt()
            for x, v, row in zip((s, i), drift, diffusion, strict=True)
        ]
        states.append([float(s), float(i)])
        betas.append(float(beta))
        drifts.append([float(v) for v in drift])
        diffusions.append([[float(v) for v in row] for row in diffusion])
        expected.append([float(max(D(0), v)) for v in output])
        noise_labels.append(noise)
        labels.append(label)

destination = Path("tests/reference/gao_single.npz")
np.savez(
    destination,
    profile_id=np.array("P5-IMPL-2026-10-19-v1"),
    noise=np.array(noise_labels), label=np.array(labels),
    state=np.array(states, dtype="<f8"), beta=np.array(betas, dtype="<f8"),
    dt=np.full(6, 0.01, dtype="<f8"), recruitment=np.full(6, 100.0, dtype="<f8"),
    recovery=np.ones(6, dtype="<f8"), mortality=np.ones(6, dtype="<f8"),
    sigma=np.tile([0.4, 0.6], (6, 1)).astype("<f8"),
    gaussian=np.tile([0.25, -0.75], (6, 1)).astype("<f8"),
    expected_drift=np.array(drifts, dtype="<f8"),
    expected_diffusion=np.array(diffusions, dtype="<f8"),
    expected_state=np.array(expected, dtype="<f8"),
    expected_incidence=np.array(betas, dtype="<f8") * 500 * 7 * 0.01,
)
print(destination, sha256(destination.read_bytes()).hexdigest())
PY
```
