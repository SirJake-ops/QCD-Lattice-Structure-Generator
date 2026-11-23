# GPU-01.11 — Store GPU histories and accurate execution provenance

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.4](gpu-01.4-plaquette.md), [GPU-01.10](gpu-01.10-workflow-selection.md) |

## Problem

The simulator header and `analysis/artifacts.py::provenance` hardcode the CPU RNG.
Source hashing also excludes `.cu` and `.cuh`, so GPU results would be mislabeled
and CUDA source changes would be absent from recorded source provenance.

## Implementation tasks

- [ ] Emit actual backend, GPU/architecture, driver/runtime/toolkit versions,
  precision, update schedule, initialization RNG, update RNG mapping, and seeds
  in the simulator header and finalized per-run provenance.
- [ ] Extend source hashing to `.cu`, `.cuh`, `CMakeLists.txt`, and relevant CMake
  files, retaining the existing binary snapshot and manifest checksums.
- [ ] Preserve header metadata through HDF5 packing; reject a completed stream
  whose actual backend contradicts the request.
- [ ] Keep chain/sweep IDs, ordered loops, optional joint arrays, and complete
  trailer semantics compatible with current readers.
- [ ] Check `analysis/learning.py` duplicate-stream handling across CPU/GPU data;
  retain conservative rejection of duplicate seeds at the same parameter point.

## Acceptance checklist

- [ ] A GPU run passes `analysis.cli verify`, HDF5 packing, and existing analysis
  without changing statistical formulas or inventing missing histories.
- [ ] GPU RNG metadata describes actual initialization and update generators.
- [ ] Changing CUDA source changes its provenance hash; older CPU bundles still
  verify under their original manifests.
- [ ] Backend mismatch, failed, and cancelled output cannot become complete
  training input; duplicate-stream safeguards still apply.

## Verification after implementation

Extend Python artifact tests with legacy CPU, successful GPU, mismatched backend,
and incomplete stream fixtures. Run one complete hardware job for each group;
attach its manifest and metadata. Full measurement coverage requires GPU-01.5/6.
