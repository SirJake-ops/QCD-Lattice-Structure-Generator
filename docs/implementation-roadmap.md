# Implementation and scientific acceptance

Successful execution and scientific validation are separate milestones. See the
[application contract](application-contract.md) for units, artifacts, and interfaces.

## Delivered software

- C++23 serial double CPU U(1) and SU(3), Wilson action, symmetric Metropolis
  updates, embedded SU(2) rotations, Haar hot starts, identity cold starts.
- Plaquettes, consecutive rectangular Wilson loops, and joint source-conditioned
  plaquette measurements in a spatial plane at the source temporal midpoint.
- Cached straight transporters checked against direct loop products.
- Group, action-difference, gauge-invariance, analytic U(1), zero-coupling SU(3),
  vacuum subtraction, symmetry averaging, and reproducibility tests.
- Autocorrelation, contiguous chain blocking, nested jackknife ratio/GLS plateau
  fits, covariance, window variation, split R-hat, explicit quality statuses.
- Versioned JSON/JSONL/HDF5 bundles with source/binary hashes and checksums.
- SQLite catalogue, cancellable single worker, restart recovery, loopback API.
- Dataset acceptance gates, whole-point/region splits, training-only Cornell
  baseline, residual GP, domain rejection, baseline/coverage reports.
- React/TypeScript, Three.js rotatable geometry, Plotly curves and measured maps,
  diagnostics, history, artifact downloads, browser workflow tests.
- Costed pilots, bounded corpus generation, verification, immutable reanalysis.

## Acceptance gates

| Milestone | Evidence and remaining scientific work |
|---|---|
| Contract | Implemented and documented. Energy is an output, spacing is a unit convention. |
| U(1) | Structural and 2D analytic tests pass. Later-time 4D pilot passes internal chain/plateau gates. Larger-volume and start-systematic studies remain. |
| SU(3) | Structural and zero-coupling tests pass. Short finite-coupling pilot reveals poor equilibration. Matched independent finite-coupling benchmarks and start studies remain required. All SU(3) potentials retain an unvalidated benchmark diagnostic. |
| Dataset/model | Costed U(1) generation and strict training pipeline exist. Generated manifests report accepted points, frozen splits, baseline errors, and interval coverage. Small evaluation sets stay experimental. |
| Browser | Real-browser workflow exercises submission, results, rotation, cancellation, and mobile layout. API tests exercise recovery and integrity. |
| Flux | Joint measurements, translation/reflection/source-exchange averaging, gauge invariance, vacuum subtraction, and propagated uncertainty are implemented. Temporal/volume stability remains required for scientific acceptance. |
| Performance | CPU is the reference. Straight-path caching follows pilot timing. CUDA remains deferred. |

## Next scientific work

Compare finite-coupling hot/cold starts and choose later-time windows before a
larger corpus is frozen. Match SU(3) plaquettes and loops against
[SIMULATeQCD](https://github.com/LatticeQCD/SIMULATeQCD), recording generator
revision, action, normalization, geometry, and independent uncertainties. Do not
use this simulator's own output as an independent benchmark. The current SU(3)
training gate remains closed until that validation is integrated.

Increase supported volumes and independently chosen holdout regions. Increase
held-out parameter-point counts before making prediction-accuracy or interval
calibration claims. Retain every raw history and analysis setting. Optimize
further only when timing identifies a bottleneck.
