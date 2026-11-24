# GPU-01.10 — Submit and inspect explicit CUDA jobs from the CLI and browser

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.2](gpu-01.2-backend-dispatch.md); successful GPU submissions also require their kernel stories |

## Story

As a user, I want to select CUDA for an experiment and see actionable availability
errors so I know where my computation will run.

## Implementation tasks

- [ ] Add `backend` with allowed values `cpu`/`cuda` and default `cpu` to
  `analysis/contracts.py::SimulationRequest`; serialize it into `[execution]`.
- [ ] Add simulator capability output and use it in `analysis/jobs.py` and
  `analysis/service.py` to report build/device support and reject unsupported
  group, geometry, or measurement combinations before starting long work.
- [ ] Preserve `analysis.cli run` JSON submission; add backend selection to the
  pilot command and a CUDA example request under `configs/`.
- [ ] Update `frontend/src/types.ts` and `main.tsx` with a compute-backend control,
  availability explanation, and selected/actual backend in run details.
- [ ] Keep worker executable snapshots, cancellation, and queue ownership intact.
  Recheck runtime availability when the subprocess starts.

## Acceptance checklist

- [ ] An old request without `backend` resolves to CPU and remains executable.
- [ ] `backend: cuda` reaches CUDA dispatch from CLI and browser; unavailable
  hardware/builds produce an actionable failure and no silent CPU fallback.
- [ ] Unsupported CUDA geometry is rejected while equivalent CPU geometry works.
- [ ] Cancel a running GPU job: it becomes incomplete/cancelled, releases GPU
  resources, and the next queued job can run.
- [ ] The browser shows the actual execution backend, rather than a hardcoded
  "CPU simulator ready" message for every simulator.

## Verification after implementation

Extend `tests/python/test_workflow.py` and `frontend/tests/workflow.spec.ts` for
selection, unavailable-device errors, history display, cancellation, and recovery.
Use actual hardware for successful CUDA submissions and resource-release checks.
