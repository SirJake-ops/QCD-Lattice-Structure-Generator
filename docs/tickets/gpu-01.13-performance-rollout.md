# GPU-01.13 — Meet the measured acceleration target and publish operating steps

| Field | Value |
|---|---|
| Type | Story |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | [GPU-01.12](gpu-01.12-validation-ci.md) |

## Story

As a researcher, I want measured acceleration and reproducible run instructions
so I can use GPU computation for the workloads where it improves throughput.

## Implementation tasks

- [ ] Run the GPU-01.1 benchmark requests with optimized CPU and CUDA builds on
  the same host, at least three repetitions each; record variation.
- [ ] Produce `docs/benchmarks/gpu-results.md` with initialization, update,
  measurement, result transfer, serialization, analysis, and complete-job times.
- [ ] Report sweeps/second, measurements/second, effective samples/second, and
  peak device memory for comparable runs, with maps on/off and both groups.
- [ ] Capture a device trace; remove measured avoidable allocations/copies or
  synchronization and rerun affected correctness checks after tuning.
- [ ] Update root README and `docs/cuda.md` with exact build/run examples,
  architecture selection, supported restrictions, device-error troubleshooting,
  provenance interpretation, and explicit CPU selection.

## Acceptance checklist

- [ ] The named hardware/workload meets the numeric target recorded in GPU-01.1;
  otherwise record measured remaining work and keep this ticket open.
- [ ] Report includes whole-job improvement and small-lattice regressions, where
  observed, rather than quoting only isolated kernel time.
- [ ] Traces show persistent field/RNG/workspace allocation and no normal
  full-field transfer after initialization.
- [ ] Raw per-sample histories still reach CPU analysis/storage; throughput gains
  do not come from dropping requested measurements or weakening quality gates.
- [ ] Another developer can follow the documented build and sample run commands.

## Verification after implementation

Attach benchmark requests, raw timing results, hardware/build details, trace
summary, and the matching correctness report. Close the parent epic only when
every child ticket is complete and these results meet its definition of done.
