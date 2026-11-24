# GPU-01 — Run lattice sampling and measurements on the GPU

| Field | Value |
|---|---|
| Type | Epic |
| Status | Open |
| Child tickets | 13 — [open the backlog](tickets/README.md) |
| First ticket | [GPU-01.1 — CUDA smoke test and CPU baseline](tickets/gpu-01.1-build-and-baseline.md) |

## User outcome

As a researcher, I want U(1) and SU(3) lattice sampling and measurements to run
on the GPU, then pass their results to the existing CPU analysis, prediction,
artifact storage, and browser workflow.

## Child tickets

These are individual ticket documents with unchecked implementation tasks,
acceptance checklists, target files, dependencies, and verification instructions.
All tickets are open; this backlog documents future work.

- [ ] [GPU-01.1 — Add a CUDA smoke-test target and record the CPU baseline](tickets/gpu-01.1-build-and-baseline.md)
- [ ] [GPU-01.2 — Extract the CPU simulation backend and dispatch by execution.backend](tickets/gpu-01.2-backend-dispatch.md)
- [ ] [GPU-01.3 — Implement device field buffers and periodic group primitives](tickets/gpu-01.3-device-field.md)
- [ ] [GPU-01.4 — Return the mean plaquette from a GPU kernel and device reduction](tickets/gpu-01.4-plaquette.md)
- [ ] [GPU-01.5 — Produce the requested Wilson-loop vector on the GPU](tickets/gpu-01.5-wilson-loops.md)
- [ ] [GPU-01.6 — Produce joint W, s, and Ws field-map samples on the GPU](tickets/gpu-01.6-field-map.md)
- [ ] [GPU-01.7 — Implement an independent link schedule and device RNG mapping](tickets/gpu-01.7-schedule-and-rng.md)
- [ ] [GPU-01.8 — Execute U(1) warm-up and sampled sweeps on the GPU](tickets/gpu-01.8-u1-sampling.md)
- [ ] [GPU-01.9 — Execute SU(3) embedded-SU(2) updates on the GPU](tickets/gpu-01.9-su3-sampling.md)
- [ ] [GPU-01.10 — Submit and inspect explicit CUDA jobs from the CLI and browser](tickets/gpu-01.10-workflow-selection.md)
- [ ] [GPU-01.11 — Store GPU histories and accurate execution provenance](tickets/gpu-01.11-artifacts.md)
- [ ] [GPU-01.12 — Gate the backend on hardware correctness and workflow tests](tickets/gpu-01.12-validation-ci.md)
- [ ] [GPU-01.13 — Meet the measured acceleration target and publish operating steps](tickets/gpu-01.13-performance-rollout.md)

## Delivery milestones

| Milestone | Completed tickets | Demonstrable result |
|---|---|---|
| First GPU result | 1–4 | Upload a CPU field once; GPU plaquette agrees with the CPU reference. |
| All measurements | 5–6 | GPU loop and joint field arrays match fixed-field CPU results. |
| Resident sampling | 7–9 | Both gauge groups evolve on device between measurements. |
| Application integration | 10–11 | Explicit CUDA jobs produce sealed artifacts consumed by existing analysis. |
| Acceptance | 12–13 | Real-hardware correctness and measured acceleration have evidence. |

The [backlog dependency table](tickets/README.md) defines the implementation
order. Tests accompany their implementation tickets; ticket 12 consolidates
hardware and workflow acceptance rather than postponing all testing.

## Scope

Keep links, RNG state, and reusable workspace on the GPU across sweeps. Return
each saved sample's acceptance, plaquette, loops, and optional joint W/s/Ws.
Initial CPU hot-start construction and one upload per chain are allowed;
full-field downloads are restricted to explicit validation/debugging.

Retain CPU execution, double precision, the Wilson action, current observable
definitions, and the [application contract](application-contract.md). CPU code
continues to handle resampling, fits, datasets, model training/inference, and
storage. Browser rendering changes, multiple GPUs, mixed precision, dynamical
fermions, and new scientific claims are outside this epic.

## Definition of done

- [ ] All 13 child tickets have implementation and verification evidence.
- [ ] U(1)/SU(3) updates, plaquettes, Wilson loops, and joint field measurements
  execute on actual GPU hardware with resident state.
- [ ] Browser/CLI execution selection, cancellation, failures, and queue recovery
  work without silent CPU fallback.
- [ ] GPU results enter the existing workflow with accurate provenance; historical
  CPU artifacts and CPU-only builds remain usable.
- [ ] Numerical/statistical checks and CUDA memory/race checks pass on hardware.
- [ ] The numeric performance target recorded in ticket 1 is met in ticket 13.
- [ ] Scientific acceptance and independent SU(3) benchmark gates remain enforced.
