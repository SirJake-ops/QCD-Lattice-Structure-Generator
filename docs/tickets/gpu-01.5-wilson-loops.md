# GPU-01.5 — Produce the requested Wilson-loop vector on the GPU

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.4](gpu-01.4-plaquette.md) |

## Story

As a researcher, I want GPU measurements to return every requested `(r,T)` loop
so the existing potential extraction receives the same input channels.

## Implementation tasks

- [ ] Add batched loop measurement to `kernels.cu`/`kernels.cuh` and the backend
  measurement result from GPU-01.2.
- [ ] Build/reuse straight transporters or equivalent bounded workspace; average
  over all translations and the three spatial axes with current normalization.
- [ ] Preserve definition order, including a deliberately non-sorted test list.
- [ ] Reject unsupported extents before allocating or measuring.
- [ ] Add `tests/cuda/wilson_loop_test.cpp`, comparing GPU results to both
  `qcd::rectangle` sums and cached `qcd::wilson_loops`.

## Acceptance checklist

- [ ] On `[4,6,4,8]`, definitions `[(2,4),(1,1),(2,2),(1,3)]` agree with both CPU
  implementations for U(1) and SU(3), under recorded numerical tolerances.
- [ ] Cold fields return 1 for every loop; gauge transformation preserves values.
- [ ] Half-extent loops and periodic paths pass; invalid lengths fail clearly.
- [ ] Only the ordered loop vector is read back, with no full-field transfer or
  CPU rectangle calculation in the GPU measurement path.

## Verification after implementation

Run the new fixed-field tests on hardware. Include result ordering and memory
diagnostics in the ticket evidence.
