# Application contract v1

```mermaid
flowchart LR
    Browser[React browser] --> API[Loopback FastAPI]
    API --> Queue[SQLite jobs]
    Queue --> Worker[Single worker]
    Worker --> Core[C++ subprocess]
    Core --> Raw[JSONL and HDF5 artifacts]
    Raw --> Analysis[Correlated analysis]
    Analysis --> Browser
    Analysis --> Dataset[Frozen validated points]
    Dataset --> Model[Cornell plus residual GP]
    Model --> API
```

## Theory, geometry, and units

Four-dimensional isotropic spacing, periodic extents in x,y,z,t order. The action
is `beta sum_(x,mu<nu) [1-ReTr(U_mu_nu(x))/N]`, N=1 or 3. SU(3) uses normalized
real fundamental traces. The weight is exp(-S). Cornell `c-alpha/n+s*n` summarizes
extracted potentials over a declared range; it never defines the gauge action.

Distances are r/a and potentials aV. Spacing is a unit convention. Model targets
are V(r)-V(1). Same-run Cornell summaries retain the raw additive convention and
are labeled as fits to that run. When a model is overlaid, the browser subtracts
the measured reference and propagates its covariance. No physical-energy or
continuum interpretation is available.

Wilson loops average translations and spatial axes. The field map uses the fixed
x-time source rectangle and an xy plane near its temporal midpoint. Translation,
y reflection, and source-exchange averages are applied to joint products. Face
anchors shift by one along reflected plaquette directions. Maps plot anchors,
not interpolated face centers. r <= half every spatial extent and T <= Nt/2;
these limits reduce wraparound problems but do not remove volume effects.

## Typed contracts and endpoints

`analysis/contracts.py` defines strict Pydantic requests, jobs, histories, potentials,
field maps, and predictions. `DatasetManifest` lives in `analysis/learning.py`.
`frontend/src/types.ts` mirrors client fields; `/openapi.json` exposes API schemas.
Unknown fields, nonfinite values, invalid geometry, and oversized requests fail.
Requests include group/beta, extents, separation, sample/warm-up counts, chain
count, seed, proposal scale, start, max r/T, field T, probe, field switch, and
analysis settings. Consecutive loops cover r=1..max_r, T=1..max_t. The legacy TOML
`measurement_sweeps` means recorded measurements, each separated by the gap.

| Method | Path under `/api/v1` | Result |
|---|---|---|
| GET | `/health` | Schema and simulator availability |
| POST | `/jobs` | Validate and submit, return 202 |
| GET | `/jobs` | Latest 100 jobs |
| GET | `/jobs/{id}` | State, request, progress, timestamps, error |
| POST | `/jobs/{id}/cancel` | Cancel queued/running job; terminal jobs unchanged |
| GET | `/jobs/{id}/analysis` | Potentials, covariance, diagnostics, same-run formula fit |
| GET | `/jobs/{id}/field` | Joint response and pointwise errors |
| GET | `/jobs/{id}/history?limit=1000` | Raw preview, capped at 5000 records |
| GET | `/jobs/{id}/artifacts/{name}` | Download a sealed file |
| GET | `/models` | Models, domains, and evaluation |
| POST | `/predictions` | Domain-checked formula and learned predictions |

404 means unknown ID; 422 invalid or unsupported request; 409 incomplete or
checksum-invalid results. States: queued, running, completed, failed, cancelled.
Cancellation terminates the subprocess and retains incomplete output. Restart
marks interrupted jobs failed; it never silently resumes chains. Queued jobs
remain queued. A process lock prevents concurrent workers. Bind only to loopback;
this is a single-user workstation service, not a multi-user deployment.

## Artifacts and reproducibility

`DATA/runs/ID/` contains request.json, resolved.toml, provenance.json,
measurements.jsonl, measurements.h5, analysis.json, field.json, simulator.bin, simulator.log,
timing.json, and manifest.json. Provenance includes revision, per-source hashes
(including uncommitted code), binary hash, dependency versions, platform,
precision, RNG, action, and units. A per-run executable snapshot prevents a later
workspace build from changing a queued run. It retains its local dynamically
linked runtime requirements. The manifest hashes all other files and records
schema version, source ID, and completeness. JSONL has header/measurement/trailer
records. HDF5 stores schema/complete attributes, loop definitions, chain and sweep
IDs, plaquette, acceptance, loops, and optional joint W/s/Ws arrays. Exact sample
counts and sweep sequences are checked before completion.

Failed/cancelled output never enters training. Each rerun gets a new ID. Reanalysis
writes a new directory under DATA/reanalyses with source checksum and new settings.
Sealed sources are never rewritten. Integrity is enforced by convention and hashes,
not filesystem ACLs. Optional configuration checkpoints are not implemented and
requests for them fail explicitly.

## Correlated estimates

Integrated autocorrelation uses initial positive paired autocovariances and the
slowest measured channel/chain, including source/probe products. Contiguous equal
blocks are formed within chains; tails are recorded and discarded. Automatic
blocks are >=ceil(2 tau), merged further to cap nested resampling at 512 blocks.
Defaults require two blocks per chain, 16 total blocks, 32 effective samples,
four independent chains, split R-hat <=1.1, and minimum warm-up. These internal
diagnostics do not prove equilibration.

Effective masses are log(mean W(r,t)/mean W(r,t+1)). Reject nonpositive central
or resampled loops. Correlated constant GLS plateau fits use the recorded inclusive
window. Each outer delete-block replicate recomputes ratios, an inner jackknife
covariance, and its own GLS fit. Singular or ill-conditioned covariances fail.
Common outer replicates give covariance across separations. Require fit p>=.01
and stability within two reported errors against an earlier-start alternative
window. A window without an alternative is unavailable. All SU(3) estimates
remain unvalidated pending independent finite-coupling benchmarks.

Field ratios recompute mean(Ws)/mean(W)-mean(s) within delete-block resampling.
Require positive W estimates and central W >3 standard errors. A resolved map
means a pointwise 3-sigma response with passing chain/statistics diagnostics,
not a global discovery or accepted temporal plateau. Temporal stability requires
independent source-T variation. Unresolved maps retain estimates and errors when
the ratio is supportable; no synthetic field map is substituted.

## Datasets, models, and limitations

Dataset manifests freeze whole parameter points and source checksums. Compatible
independent accepted runs are combined with full reference-subtracted covariance.
The middle beta per volume is interpolation holdout; the highest is region
holdout; all others train. At least six accepted betas per volume are required.
No chain contributes to more than one split.

Fit Cornell coefficients only on training points; interpolate them linearly in
beta at each explicitly supported extent tuple. The GP models residuals with
diagonal measurement noise. Full covariance remains in the dataset and Cornell
fits. Reference subtraction induces correlations absent from diagonal GP noise;
baseline and residual uncertainties are also dependent. Quadrature intervals are
approximate. Reports include held-out RMSE for constant/interpolation/formula/GP,
coverage against measured means, and coverage including held-out measurement error.

Models stay experimental without >=30 interpolation holdout parameter points,
>=90% latent-interval coverage, and improvement over all baselines. Region holdouts
audit extrapolation only; public predictions reject unsupported beta, separation,
and volumes. Group identities are strict. GP persistence uses checked numeric NPZ
arrays and reconstructed kernel parameters, never executable pickle files.

Sources: [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/),
[scikit-learn Gaussian processes](https://scikit-learn.org/stable/modules/gaussian_process.html),
[scientific project background](physics-and-numerics.md), and
[training-data references](training-data-sources.md).
