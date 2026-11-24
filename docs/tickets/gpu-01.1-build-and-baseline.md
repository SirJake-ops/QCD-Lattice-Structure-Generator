# GPU-01.1 — Add a CUDA smoke-test target and record the CPU baseline

| Field | Value |
|---|---|
| Type | Engineering task |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | None — start here |

## Problem

The CUDA build currently contains empty translation units. Building it does not
prove that the application can allocate memory or execute work on a GPU.

## Implementation tasks

- [x] Add a `cuda-release` configure/build/test preset in `CMakePresets.json`.
  Allow the developer to specify the target architecture through CMake.
- [x] Register a `qcd_cuda_tests` target in `CMakeLists.txt`, only when
  `QCD_ENABLE_CUDA` and `BUILD_TESTING` are enabled.
- [x] Add `tests/cuda/runtime_test.cpp` and a small device test helper that
  allocates a buffer, writes known values in a kernel, copies them back, and
  checks the values. Report device, runtime, and driver versions.
- [x] Make unavailable hardware an explicit skipped runtime test with its CUDA
  error, distinct from a successful GPU execution.
- [x] Add reproducible CPU benchmark requests under `configs/benchmarks/` for
  both groups, using small `[4,4,4,8]` and larger `[8,8,8,16]` lattices, with
  field measurements enabled and disabled.
- [x] Record release CPU timing and machine details in
  `docs/benchmarks/gpu-baseline.md`; record a numeric acceleration target for a
  named workload to be evaluated in GPU-01.13.

## Acceptance checklist

- [x] With CUDA disabled, configure/build/test succeeds without a toolkit.
- [x] With CUDA enabled and hardware available, the smoke test verifies device
  output; a compile-only run is labeled separately.
- [x] Without an accessible GPU, runtime checks report skipped, never passed.
- [x] The baseline report contains request paths, commands, revision, hardware,
  repeated timings, and the performance target. Missing hardware is recorded.

## Verification after implementation

Run the CPU presets, then `cmake --preset cuda-release`,
`cmake --build --preset cuda-release`, and `ctest --preset cuda-release`.
Run each benchmark request against the release CPU simulator at least three
times. Attach outputs to this ticket before marking it done.
