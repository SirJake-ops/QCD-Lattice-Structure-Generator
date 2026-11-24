# GPU-01.7 — Implement an independent link schedule and device RNG mapping

| Field | Value |
|---|---|
| Type | Engineering task |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.3](gpu-01.3-device-field.md) |

## Problem

Launching the current serial Metropolis loop over adjacent links would create
shared-plaquette dependencies. Reusing one host RNG would also serialize updates.

## Implementation tasks

- [ ] Specify direction/color update phases in `update.cuh`/`update.cu`; dependent
  phases execute in order, and simultaneous links share no plaquette.
- [ ] Initially support even periodic extents for CUDA sampling; reject odd
  extents explicitly while retaining CPU support.
- [ ] Add a CPU schedule helper and a test that enumerates each plaquette to
  verify that it contains at most one link from any simultaneous update set.
- [ ] Implement device RNG state/counters in `device_rng.cuh`; document generator,
  seed/chain derivation, site/direction mapping, draw allocation, and run limits.
- [ ] Add a deterministic proposal/acceptance-input path for CPU/GPU phase tests.
- [ ] Record the transition-rule justification and RNG mapping in `docs/cuda.md`.

## Acceptance checklist

- [ ] Schedule coverage updates every link exactly once per sweep and finds no
  shared plaquette within a phase, including all periodic edges.
- [ ] Repeated seed/chain inputs reproduce draws on the same supported build;
  mapped stream/counter identities are unique over tested chains/links/sweeps.
- [ ] Unsupported odd geometry fails before sampling; CPU requests still work.
- [ ] Fixed proposals and variates can be replayed without depending on identical
  random streams between serial CPU and CUDA implementations.

## Verification after implementation

Add `tests/cuda/update_schedule_test.cpp` and `device_rng_test.cpp`. Run the
schedule-enumeration checks on CPU and RNG/replay checks on actual GPU hardware.
No checkpoint/resume support is part of this ticket.
