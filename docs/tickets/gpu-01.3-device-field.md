# GPU-01.3 — Implement device field buffers and periodic group primitives

| Field | Value |
|---|---|
| Type | Engineering task |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.2](gpu-01.2-backend-dispatch.md) |

## Story

As a kernel developer, I need a resident device field with tested indexing and
matrix operations so subsequent kernels can operate without downloading links.

## Implementation tasks

- [ ] Implement owned link/workspace buffers in `include/qcd/cuda/gauge_field.cuh`
  and `src/cuda/gauge_field.cu`, including cleanup after partial initialization.
- [ ] Define double-precision U(1)/SU(3) storage and explicit CPU-field packing;
  document matrix element order rather than assuming Eigen's memory layout.
- [ ] Add periodic neighbor/index helpers for x,y,z,t extents and device group
  multiplication, adjoint/conjugate, normalized trace, and staple primitives.
- [ ] Expose upload/download only for initialization and validation; preallocate
  workspace rather than allocating per site or sweep.
- [ ] Check size arithmetic and memory budgets before allocation; propagate
  allocation, transfer, and device execution errors through the backend.

## Acceptance checklist

- [ ] Cold and seeded hot U(1)/SU(3) fields survive upload/download unchanged.
- [ ] Device neighbors agree with `lattice::Lattice` for every site of
  `[4,6,4,8]`, including wrapping in both directions.
- [ ] Device products, traces, staples, and action differences match CPU
  calculations on fixed fields under recorded absolute/relative tolerances.
- [ ] Invalid/overflowing sizes fail cleanly; forced initialization failures
  release earlier allocations.

## Verification after implementation

Add `tests/cuda/gauge_field_test.cpp`; compare with `gauge_group.h`, `action.h`,
and `Lattice` on the host. Run the target under CUDA memory diagnostics on actual
hardware and attach the result.
