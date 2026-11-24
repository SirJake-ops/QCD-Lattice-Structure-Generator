# GPU-01.6 — Produce joint W, s, and Ws field-map samples on the GPU

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.5](gpu-01.5-wilson-loops.md) |

## Story

As a researcher, I want joint source/probe samples from the GPU so existing CPU
resampling can calculate the field response and its uncertainty correctly.

## Implementation tasks

- [ ] Port `qcd::field_samples` to device kernels: source rectangle in x-time,
  probe at `floor(T/2)`, and xy cells in existing flattened order.
- [ ] Reduce the joint products over translations; preserve source exchange,
  y reflection, and orientation-dependent reflected plaquette anchor shifts.
- [ ] Return `w`, `s`, and `ws` per recorded sample through the backend result.
  Keep vacuum subtraction and jackknife calculations in `analysis/`.
- [ ] Skip field kernels/workspace when field measurements are disabled.
- [ ] Add `tests/cuda/field_map_test.cpp` against the CPU `FieldSamples` result.

## Acceptance checklist

- [ ] Every returned cell agrees with CPU on fixed U(1)/SU(3) fields for six
  unordered probe planes, odd/even source T, and unequal spatial extents.
- [ ] Cold fields give zero vacuum-subtracted response; transformed hot fields
  retain joint measurements within recorded tolerances.
- [ ] A nontrivial fixed-field fixture demonstrates that `mean(Ws)` comes from
  joint products and is not replaced by `mean(W)*mean(s)`.
- [ ] Disabled field measurement returns no map arrays and launches no map work.

## Verification after implementation

Run fixed-field, gauge-invariance, and symmetry tests on hardware. After
GPU-01.11, pack these samples and run the existing Python field analysis unchanged.
