# Lattice gauge explorer

A local browser workbench for compact U(1) and pure SU(3) Wilson-action theory.
Supply four periodic lattice extents, coupling, source separation, and sampling
controls. Compare a measured static potential, a Cornell approximation, and a
residual Gaussian-process prediction when a compatible trained model exists.
Inspect the rotatable spatial lattice and a **measured source-induced action-density
response in lattice units**.

The serial C++23 simulator, correlated Python analysis, SQLite worker queue,
HDF5 artifacts, training pipeline, and React/Three.js/Plotly client are implemented.
Scientific acceptance is tracked in [the roadmap](docs/implementation-roadmap.md).
SU(3) training remains gated on independent benchmarks. A completed simulation
can legitimately yield unavailable or unvalidated potentials.

## Run locally

Requires CMake >=3.25, a C++23 compiler, Ninja, Python >=3.11 with venv, and Node
>=20.19 with npm. First setup downloads the C++ and application dependencies.

```sh
cmake -S . -B build/local-release -G Ninja -DCMAKE_BUILD_TYPE=Release -DQCD_ENABLE_CUDA=OFF
cmake --build build/local-release --parallel 4
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
cd frontend
npm ci
npm run build
cd ..
.venv/bin/python -m analysis.cli serve
```

Open **http://127.0.0.1:8000**. Interactive API contracts are at `/docs`. The service
binds to loopback and uses one worker. Do not run multiple server processes against
the same catalogue. `--data PATH` selects another data root; `--simulator PATH`
selects a binary, for example one built using a CMake preset. These global options
precede the subcommand. `QCD_DATA` and `QCD_SIMULATOR` are supported by the app factory.

The default browser experiment is intentionally small. Increase temporal loop
lengths and samples when diagnostics reject a plateau. A Cornell fit needs at
least three available separations; a nontrivial residual model benefits from four
or more. Fit windows need two consecutive effective masses and an alternative
window for stability checks. Energy is an output.

For development, run the API and `cd frontend && npm run dev` separately. Vite
proxies `/api` to port 8000. The built application has no external runtime assets.

## Simulation and learning

```sh
.venv/bin/python -m analysis.cli pilot --group u1
.venv/bin/python -m analysis.cli --data results/su3-pilot pilot --group su3
.venv/bin/python -m analysis.cli run configs/browser-example.json
.venv/bin/python -m analysis.cli --data results/corpus corpus configs/corpus-u1.json
.venv/bin/python -m analysis.cli --data results/corpus corpus configs/corpus-followup.json
.venv/bin/python -m analysis.cli --data results/corpus dataset --group u1
.venv/bin/python -m analysis.cli --data results/corpus train results/corpus/datasets/DATASET_ID
.venv/bin/python -m analysis.cli verify results/corpus/runs/RUN_ID
.venv/bin/python -m analysis.cli reanalyze results/corpus/runs/RUN_ID --fit-min 8 --fit-max 10
.venv/bin/python -m analysis.cli compare-fields RUN_AT_T7 RUN_AT_T9 RUN_AT_T11
```

Corpus generation is explicit and bounded, with four independent chains per point.
Dataset building excludes incomplete runs, unvalidated estimates, duplicate random
streams, and incompatible theory. It requires six accepted couplings per supported
volume. The middle coupling is held out for interpolation and the highest for a
region test. Splits contain entire parameter points and all associated chains.

Training-only Cornell coefficients are interpolated over coupling at each listed
volume. A GP fits residuals using measurement variances. Targets are `V(r)-V(1)`.
Reports compare constant, interpolation, formula-only, and GP predictions on frozen
holdouts, including interval coverage. Small evaluations remain experimental.
Unsupported coupling, separation, and volume requests fail. U(1) and SU(3) cannot
be mixed. See model metadata for uncertainty approximations.

Start the server with `--data results/corpus serve` to inspect that corpus and its
models. Training runs through the CLI; the browser lists available models.

The original `qcd_prediction CONFIG.toml` remains a configuration inspector.
The new `qcd_simulate CONFIG.toml` emits a versioned JSONL stream; use the Python
runner for HDF5 storage and provenance. Run the binary without arguments for
optional source/probe/start arguments. Unsupported algorithms, checkpoints,
Polyakov loops, nonperiodic boundaries, and lower-dimensional requests fail.

## Verify

```sh
ctest --test-dir build/local-release --output-on-failure
.venv/bin/pytest -q
cd frontend
npm run build
npx playwright test
```

The browser test needs a server already on port 8000 and system Chromium, or
`npx playwright install chromium`; `QCD_BROWSER` can override its executable.
It exercises submission, results, rotation, cancellation, browser errors, and
mobile overflow. Statistical and training tests use explicitly synthetic fixtures
that never become scientific data or shipped models.

C++ tests cover indexing, group constraints, action differences, gauge invariance,
cached vs direct loops, vacuum subtraction, symmetry averaging, an analytic 2D
U(1) plaquette, and SU(3) hot/cold agreement at zero coupling. Python tests cover
correlated statistics, nested jackknife fits, joint field ratios, artifacts,
reproducibility, failure recovery, cancellation, frozen splits, and model support.

Existing CMake Debug, Release, sanitizer, and coverage options remain available.
Use `cmake --preset cpu-sanitize`, build and test with that preset for sanitizers.
Configure `-DENABLE_COVERAGE=ON` and build the `coverage` target for coverage.
CUDA is scaffolding and is disabled by default. `requirements.lock` records the
Python environment used for verification; `frontend/package-lock.json` locks npm.

## Scientific scope

The action is `S=beta sum_p (1-ReTr(U_p)/N)`. The Cornell expression
`aV(n)=c-alpha/n+s*n` is a range-limited approximation, never the sampling action.
Separations are `r/a`, potentials are `aV`, and spacing is a unit convention until
scale setting exists. Field responses have no physical energy-density normalization.

Measurement error, fit-window variation, and model uncertainty are separate.
Field maps preserve joint `W`, `s(x)`, and `W*s(x)` histories and recompute the
vacuum-subtracted ratio during resampling. No map is inferred from a potential
curve. Significance is pointwise; temporal stability needs independent T variation.

Read [application contracts](docs/application-contract.md),
[validation evidence](docs/validation-report.md), and the
[scientific background](docs/README.md). Large outputs are ignored under `results/`.
Dynamical quarks, continuum predictions, physical scale setting, field-map ML,
and cloud deployment are later extensions.
