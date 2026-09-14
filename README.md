# QCD Prediction

> **Work in progress:** this repository is an early project skeleton. It builds,
> loads example configurations, and runs infrastructure tests, but it does not
> yet perform a lattice-gauge simulation or produce scientifically meaningful
> QCD predictions.

QCD Prediction is a C++/CUDA research and learning project aimed at building a
small, verifiable lattice-gauge simulator and using its measurements to train an
uncertainty-aware surrogate model. The intended scientific target is to measure
gauge-invariant observables such as plaquettes and Wilson loops, extract a
static-source potential, and eventually predict compatible observables across
lattice geometries and coupling parameters.

The project is deliberately staged. Correctness, reproducibility, and a simple
CPU reference come before performance or large learned models.

## Project direction

The planned development path is:

1. Implement tested lattice indexing, periodic boundaries, random-number
   streams, and statistical error estimates.
2. Validate the Monte Carlo machinery on a small classical or toy model.
3. Implement compact U(1), followed by pure SU(2) and pure SU(3) gauge theory.
4. Measure plaquettes and Wilson loops and extract an effective static
   potential with autocorrelation-aware uncertainties.
5. Generate a controlled dataset over coupling, volume, geometry, and
   independently seeded chains.
6. Validate selected parameter points against compatible public ensembles or
   established lattice software.
7. Train and evaluate an uncertainty-aware surrogate, clearly separating
   interpolation from extrapolation.
8. Optimize measured bottlenecks with CUDA while retaining comparisons against
   the CPU reference.

This is not intended to begin as a production lattice-QCD package. Dynamical
fermions, continuum extrapolation, and precision phenomenology are outside the
initial scope.

## Current status

Available now:

- CMake targets for a host `lattice` library, a CUDA `qcd_cuda` library, and the
  `qcd_prediction` executable.
- C++23 host and CUDA C++20 project configuration.
- TOML configuration loading through
  [toml++](https://github.com/marzer/tomlplusplus).
- Example U(1), small-test, and forward-looking SU(3) configuration files.
- GoogleTest integration through CTest, including configuration parsing and a
  framework sanity test.
- Optional GCC/gcov coverage instrumentation and gcovr report generation.
- Empty interfaces and source files defining the intended module layout.

Not implemented yet:

- lattice indexing and boundary operations;
- gauge-group and gauge-field representations;
- actions, update algorithms, and observables;
- CPU or CUDA simulation kernels;
- statistical analysis and output serialization;
- dataset ingestion or generation; and
- a trained prediction model.

## Requirements

- CMake 3.25 or newer;
- a C++ compiler with C++23 support;
- the CUDA toolkit and an `nvcc` toolchain supporting CUDA C++20; and
- Git and network access during the first configuration so CMake can fetch
  Eigen, toml++ and GoogleTest.

Coverage builds currently require GCC and gcov. Installing `gcovr` additionally
enables HTML, XML, and text coverage reports.

## Matrix operations

CMake fetches Eigen 5.0.0 automatically. `gauge_field::Su3Matrix` is an alias
for `Eigen::Matrix3cd`, a fixed-size 3×3 complex matrix:

```cpp
#include <qcd/gauge_field.h>

using gauge_field::Su3Matrix;
Su3Matrix u = Su3Matrix::Identity();
Su3Matrix v = Su3Matrix::Zero();
v(0, 1) = {0.0, 1.0};
Su3Matrix product = u * v;
Su3Matrix dagger = v.adjoint();
```

Use `Identity()` or `Zero()` explicitly: default construction does not initialize
Eigen matrix entries. Element access uses `(row, column)`. These are general
complex matrices; the alias does not enforce unitarity or determinant one.
Assign expressions to `Su3Matrix` when you want to store an evaluated result.

## Build and test

Configure and build a Debug version:

```sh
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug -DBUILD_TESTING=ON
cmake --build build --parallel
```

Run the test suite:

```sh
ctest --test-dir build --output-on-failure
```

Run the executable with the copied default configuration:

```sh
./build/qcd_prediction
```

Alternatively, pass a configuration explicitly:

```sh
./build/qcd_prediction configs/small-test.toml
```

At this stage the executable only verifies configuration loading and prints a
small amount of resolved information. It does not start a simulation.

## Test coverage

Configure a separate instrumented build and run the coverage target:

```sh
cmake -S . -B build-coverage \
  -DCMAKE_BUILD_TYPE=Debug \
  -DBUILD_TESTING=ON \
  -DENABLE_COVERAGE=ON
cmake --build build-coverage --target coverage
```

When gcovr is available, reports are written under
`build-coverage/coverage/`. Otherwise, the target still runs the tests and
collects raw gcov data.

## Configuration

Example run configurations live in [`configs/`](configs/):

- `default.toml` — the current default U(1) development configuration;
- `small-test.toml` — a small, fast configuration intended for testing; and
- `example-su3.toml` — a forward-looking pure SU(3) configuration for a later
  milestone.

The configuration schema records the model, lattice, sampling procedure,
update algorithm, requested observables, execution backend, and output policy.
As the simulator develops, resolved run metadata and reproducibility details
will be stored alongside generated results.

## Repository layout

```text
apps/          Executable entry points
configs/       Example TOML run configurations
docs/          Scientific scope, numerical notes, roadmap, and data research
include/qcd/   Backend-neutral interfaces and CUDA-specific headers
src/           Host configuration code and CUDA implementation scaffolding
tests/         GoogleTest unit and infrastructure tests
cmake/         Supporting CMake scripts
analysis/      Future analysis and model experiments
```

## Documentation

- [Starting guide](docs/README.md)
- [Project scope and success criteria](docs/project-scope.md)
- [Physics and numerical foundations](docs/physics-and-numerics.md)
- [Common lattice-QCD challenges](docs/common-challenges.md)
- [Implementation roadmap](docs/implementation-roadmap.md)
- [Training-data sources](docs/training-data-sources.md)
- [CUDA decision guide](docs/cuda.md)

The documentation describes the intended research direction, not completed
scientific capabilities. Any future numerical result should be treated as
provisional until it passes the validation hierarchy documented in the project.
