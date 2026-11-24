# GPU-01.12 — Gate the backend on hardware correctness and workflow tests

| Field | Value |
|---|---|
| Type | Engineering task |
| Status | Open |
| Parent | [GPU-01](../gpu-computation-epic.md) |
| Depends on | GPU-01.5 through GPU-01.11; see [backlog](README.md) |

## Implementation tasks

- [ ] Register earlier CUDA test cases with CTest; retain the existing CPU debug,
  release, sanitizer, and application checks in `.github/workflows/ci.yml`.
- [ ] Add CUDA compile coverage with a pinned supported toolkit; document a GPU
  runner or workstation procedure for actual runtime tests.
- [ ] Add independent-seed CPU/GPU ensemble checks for both groups and hot/cold
  starts. Fix workloads, warm-up, observable comparisons, uncertainty treatment,
  minimum effective samples, and multiple-comparison policy before evaluating.
- [ ] Run full browser/worker jobs with field measurements both on and off;
  verify artifact integrity and analysis statuses, including unavailable fits.
- [ ] Run CUDA memory/race diagnostics and record outcomes in
  `docs/validation-report.md` or a linked GPU-specific report.

## Acceptance checklist

- [ ] Fixed-field observables, same-schedule update replay, RNG mapping, group
  constraints, and boundary cases pass on an identified GPU.
- [ ] CPU/GPU ensembles pass the recorded autocorrelation-aware statistical rule;
  matching raw serial trajectories is not required or used as the criterion.
- [ ] Cancellation, device failure, and subsequent queue execution pass without
  completed artifacts from interrupted runs.
- [ ] Missing hardware is explicitly skipped/blocked; compile success is never
  reported as GPU runtime validation.
- [ ] No unresolved CUDA memory/race errors remain; CPU regression suites pass.
- [ ] SU(3)'s independent benchmark and all training acceptance gates remain active.

## Verification after implementation

Attach the GPU model, revision, build settings, commands, test output, numerical
tolerances, statistical comparison report, and diagnostic logs. A ticket with
only compile evidence remains open for hardware acceptance.
