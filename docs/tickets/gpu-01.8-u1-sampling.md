# GPU-01.8 — Execute U(1) warm-up and sampled sweeps on the GPU

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.4](gpu-01.4-plaquette.md), [GPU-01.7](gpu-01.7-schedule-and-rng.md) |

## Story

As a researcher, I want a U(1) chain to evolve on the GPU so warm-up and gaps
between saved measurements do not require CPU link updates or field transfers.

## Implementation tasks

- [ ] Implement symmetric U(1) proposals, staples, action differences, acceptance
  tests, and accepted-link counting in `src/cuda/update.cu`.
- [ ] Wire the U(1) backend to initialize once per chain and advance the requested
  sweeps using GPU-01.7's phases and RNG state.
- [ ] Preserve existing cold/hot initialization; one initial host upload is allowed.
- [ ] Keep links/RNG/workspace resident through warm-up and measurement gaps;
  return acceptance for the last sweep, matching current stream semantics.
- [ ] Advertise only the measurements whose kernel tickets have been completed;
  fail unsupported requests rather than calling CPU measurements silently.

## Acceptance checklist

- [ ] Deterministic proposals/variates reproduce the same-schedule CPU phase
  result and local action differences within recorded tolerances.
- [ ] At beta zero, every proposal is accepted; link modulus stays within its
  documented drift bound over the long-run test.
- [ ] Same-build seeded replay gives identical histories; different chains use
  distinct stream identities.
- [ ] Transfer tracing shows no full-field copies during warm-up or gaps.
- [ ] Sampling preserves the requested warm-up count, gap, and measurement IDs.

## Verification after implementation

Add `tests/cuda/u1_update_test.cpp`; run local replay, zero-coupling, group-drift,
and residency checks. Full independent-ensemble acceptance is required by
GPU-01.12 before rollout.
