# GPU-01.9 — Execute SU(3) embedded-SU(2) updates on the GPU

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.8](gpu-01.8-u1-sampling.md) |

## Story

As a researcher, I want the existing pure SU(3) theory sampled on the GPU with
the same Wilson action and symmetric embedded-SU(2) proposal distribution.

## Implementation tasks

- [ ] Add embedded-SU(2) pair selection, axis/angle generation, and SU(3) proposals
  in the CUDA update path, matching `qcd::SU3::proposal`'s distribution.
- [ ] Use normalized real traces and GPU staples for the acceptance test.
- [ ] Reuse the resident chain/sweep lifecycle from U(1), including cold and Haar
  hot starts. Host construction and one upload of the hot start are allowed.
- [ ] Add long-run monitoring tests for `U.adjoint()*U` and determinant drift.
  Justify and validate any correction before introducing it into sampling.
- [ ] Keep SU(3)'s independent-benchmark diagnostic and training restriction.

## Acceptance checklist

- [ ] Fixed-input proposals and update phases match the CPU reference within
  recorded tolerances for all three embedded pairs.
- [ ] Zero-coupling updates accept all proposals; hot/cold diagnostics and
  unitarity/determinant bounds pass the recorded long-run procedure.
- [ ] Multiple chains are reproducible within the stated hardware/build scope.
- [ ] Normal SU(3) sweeps and measurements contain no host matrix calculations
  or full-field transfers after initialization.
- [ ] CPU/GPU agreement never labels SU(3) potentials independently validated.

## Verification after implementation

Add `tests/cuda/su3_update_test.cpp` and attach drift and memory-diagnostic output.
GPU-01.12 performs the independent finite-coupling ensemble comparison.
