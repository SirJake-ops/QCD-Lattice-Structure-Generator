# Implementation ticket backlog

Parent epic: [GPU-01 — GPU lattice computation](../gpu-computation-epic.md).

Each linked file is an individual ticket. Open a ticket to see its exact target
files, implementation tasks, acceptance checklist, and verification work.
These are repository tickets; they have not been published to an external issue
tracker. No implementation or test targets described here have been added yet.

## Ready to start

[GPU-01.1 — Add a CUDA smoke-test target and record the CPU baseline](gpu-01.1-build-and-baseline.md).
Its first deliverables are a `cuda-release` preset, a `qcd_cuda_tests` target,
an actual device-output check, and reproducible CPU benchmark requests.

## All tickets

| Ticket | Title | Status | Depends on |
|---|---|---|---|
| [GPU-01.1](gpu-01.1-build-and-baseline.md) | Add CUDA build/smoke-test coverage and CPU baseline | Open | None |
| [GPU-01.2](gpu-01.2-backend-dispatch.md) | Extract CPU backend and add execution dispatch | Open | 1 |
| [GPU-01.3](gpu-01.3-device-field.md) | Implement resident field storage and device primitives | Open | 2 |
| [GPU-01.4](gpu-01.4-plaquette.md) | Implement GPU plaquette kernel and reduction | Open | 3 |
| [GPU-01.5](gpu-01.5-wilson-loops.md) | Implement batched GPU Wilson loops | Open | 4 |
| [GPU-01.6](gpu-01.6-field-map.md) | Implement GPU joint W/s/Ws measurements | Open | 5 |
| [GPU-01.7](gpu-01.7-schedule-and-rng.md) | Implement update phases and device RNG mapping | Open | 3 |
| [GPU-01.8](gpu-01.8-u1-sampling.md) | Implement resident U(1) sampling | Open | 4, 7 |
| [GPU-01.9](gpu-01.9-su3-sampling.md) | Implement resident SU(3) sampling | Open | 8 |
| [GPU-01.10](gpu-01.10-workflow-selection.md) | Add CLI/browser selection and worker capability checks | Open | 2; kernel stories for successful GPU jobs |
| [GPU-01.11](gpu-01.11-artifacts.md) | Preserve GPU histories, hashes, and execution provenance | Open | 4, 10 |
| [GPU-01.12](gpu-01.12-validation-ci.md) | Add hardware/CI and full-workflow acceptance gates | Open | 5–11 |
| [GPU-01.13](gpu-01.13-performance-rollout.md) | Demonstrate acceleration and document operation | Open | 12 |

Numbers in the dependency column refer to the child suffix under GPU-01.
Tickets 5–6 and 7–9 form separate measurement and sampling workstreams after
ticket 4. Ticket 10 can begin with dispatch/capability work before all kernels
are delivered; unsupported capabilities must remain unavailable.

## Working a ticket

1. Mark its status In progress and follow its implementation checklist.
2. Run its verification and attach commands, results, revision, and hardware
   details where applicable. A skipped GPU run is not hardware acceptance.
3. Mark acceptance items complete only when verified, then update ticket status
   here and the parent epic's child checklist.

Local kernel tests belong with each implementation. The final validation ticket
checks the assembled backend and application; it does not replace those tests.
