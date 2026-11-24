# GPU-01.2 — Extract the CPU simulation backend and dispatch by execution.backend

| Field | Value |
|---|---|
| Type | Engineering task |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.1](gpu-01.1-build-and-baseline.md) |

## Problem

`apps/simulator.cpp::run<G>` directly owns `Field<G>` and calls CPU algorithms.
`main` rejects every backend except `cpu`. There is no insertion point for CUDA.

## Implementation tasks

- [ ] Add a host-facing simulation interface in `include/qcd/simulation.h` with
  chain initialization, sweep advancement, measurement, and capability methods.
- [ ] Define a measurement result containing acceptance, plaquette, ordered loop
  values, and optional joint `w/s/ws`; keep CUDA pointers out of this type.
- [ ] Move existing CPU computation behind an implementation under `src/core/`.
  Keep JSONL formatting and sampling/chain bookkeeping in the driver.
- [ ] Dispatch using `RunConfig.execution_config.backend`; recognize `cpu` and
  `cuda` and give specific errors for unknown/unavailable backends.
- [ ] Link `qcd_simulate` to `qcd_cuda` only for CUDA-enabled builds. Until kernel
  stories are complete, CUDA dispatch must report unsupported capabilities.

## Acceptance checklist

- [ ] Existing CPU requests produce the same seeded measurement histories as
  before extraction, excluding intentionally added header metadata.
- [ ] CPU-only builds do not include/link CUDA headers or runtime libraries.
- [ ] CUDA requests in CPU-only builds fail with a build-option instruction.
- [ ] CUDA failures never fall back silently to CPU or emit a complete trailer.
- [ ] JSONL meanings and downstream analysis remain unchanged.

## Verification after implementation

Capture a CPU fixture before extraction; compare parsed measurement records
after extraction. Extend `tests/python/test_workflow.py` with backend dispatch
failure cases and run the existing C++ and Python suites.
