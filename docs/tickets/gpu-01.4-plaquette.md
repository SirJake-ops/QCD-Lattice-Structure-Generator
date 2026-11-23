# GPU-01.4 — Return the mean plaquette from a GPU kernel and device reduction

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.3](gpu-01.3-device-field.md) |

## Story

As a researcher, I want to measure the plaquette on an uploaded reference field
so I can check the first GPU result against the CPU before migrating sampling.

## Implementation tasks

- [ ] Implement site/plane contributions in `src/cuda/kernels.cu` and declare the
  host entry point in `include/qcd/cuda/kernels.cuh`.
- [ ] Cover all six `mu < nu` planes and reduce on device to the mean used by
  `1 - action(field, 1)/(6*volume)`.
- [ ] Reuse reduction buffers; synchronize/check errors at result readback.
- [ ] Add `tests/cuda/plaquette_test.cpp` for both groups, with fixed CPU fields
  uploaded once and measured repeatedly.

## Acceptance checklist

- [ ] An identity field returns plaquette 1 within the recorded numerical bound.
- [ ] Hot, constructed, and gauge-transformed fields agree with the CPU mean;
  test tolerances are explicit constants with a recorded justification.
- [ ] `[4,6,4,8]` and an intentionally partial final work block pass bounds tests.
- [ ] The normal result transfer is one mean per field, not a full link field or
  array of site contributions.
- [ ] Repeating measurement without updating the field performs no new field
  upload and no new workspace allocation.

## Verification after implementation

Run the plaquette tests on hardware and record CPU/GPU values and maximum
observed discrepancy. This ticket completes the first GPU computation milestone.
