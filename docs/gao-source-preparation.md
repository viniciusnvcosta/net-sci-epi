# Gao single-region source preparation (29/09/2026)

This source record addresses graph/simulation Task 2, Step 1. It is not an
approved simulator profile, one-step fixture or scientific gate. The [Gao et al.
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
`median(CV_T)>median(CV_N)` gate. The gate is preserved pending a dated
scientific decision in [protocol-decisions.md](protocol-decisions.md).
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

## Decision prerequisites

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
The planned machine-readable `gao_manifest.json` is still pending.
