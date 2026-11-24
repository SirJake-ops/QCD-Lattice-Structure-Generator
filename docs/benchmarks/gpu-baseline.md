# GPU-01 CPU baseline

Release-build CPU timings for the GPU-01.1 benchmark requests. GPU-01.13 reruns
the same requests on the CUDA build and compares against these numbers.

| Field | Value |
|---|---|
| Date | 2026-11-24 |
| Revision | `83da01440f1b173b40948183286654ab08533998` (clean working tree) |
| Build | `cpu-release` preset, `CMAKE_BUILD_TYPE=Release`, `-O3 -DNDEBUG` |
| Simulator | `build/cpu-release/qcd_simulate` |
| Repetitions | 3 per request, run back to back |

## Machine

| Component | Value |
|---|---|
| CPU | AMD Ryzen 9 7900X, 12 cores / 24 threads, max 5.74 GHz |
| CPU governor | `performance` |
| Memory | 61 GiB |
| OS / kernel | Linux 7.2.15-4-omarchy x86_64 |
| Compiler | GCC 16.2.1 (20260810) |
| CMake | 4.4.4 |
| Python | 3.14.8 (project `.venv`) |
| GPU (present, not used for this baseline) | NVIDIA GeForce RTX 4080 SUPER, 16 GiB, driver 615.78.08 |
| CUDA toolkit | 13.4 (V13.4.92) |

## Requests

All files are in `configs/benchmarks/`. They differ only in `gauge_group`,
`extents` and `measure_field`. Shared settings:

| Setting | Value |
|---|---|
| `beta` | 1.0 |
| `chains` | 4 |
| `warmup_sweeps` | 100 |
| `measurements` | 128 per chain (512 total) |
| `sweeps_between_measurements` | 4 |
| `seed` | 1 |
| `start` | cold |
| `proposal_scale` | 0.7 |
| `max_r` / `max_t` | 2 / 4 |

Each request performs 100 + 128 × 4 = 612 sweeps per chain, 2,448 sweeps total.

## Commands

```
cmake --preset cpu-release
cmake --build --preset cpu-release
.venv/bin/python -m analysis.cli --simulator build/cpu-release/qcd_simulate \
    run configs/benchmarks/<request>.json
```

Each request was run three times. Times are `elapsed_seconds` from each run's
`results/runs/<id>/timing.json`: the complete job, measured from the job
manager starting the simulator to the end of analysis and serialization.

## Results

| Request | Run 1 (s) | Run 2 (s) | Run 3 (s) | Mean (s) | Std dev (s) | CV | ms / measurement | Sweeps / s |
|---|---|---|---|---|---|---|---|---|
| `u1-4x4x4x8-field` | 1.912 | 1.886 | 1.908 | 1.902 | 0.014 | 0.7% | 3.71 | 1,287 |
| `u1-4x4x4x8-nofield` | 1.869 | 1.805 | 1.842 | 1.839 | 0.032 | 1.7% | 3.59 | 1,331 |
| `u1-8x8x8x16-field` | 8.826 | 8.894 | 8.847 | 8.856 | 0.035 | 0.4% | 17.30 | 276 |
| `u1-8x8x8x16-nofield` | 7.352 | 7.401 | 7.357 | 7.370 | 0.027 | 0.4% | 14.39 | 332 |
| `su3-4x4x4x8-field` | 2.180 | 2.190 | 2.147 | 2.172 | 0.023 | 1.0% | 4.24 | 1,127 |
| `su3-4x4x4x8-nofield` | 2.009 | 1.992 | 1.997 | 1.999 | 0.009 | 0.4% | 3.90 | 1,224 |
| `su3-8x8x8x16-field` | 30.867 | 31.365 | 31.010 | 31.081 | 0.256 | 0.8% | 60.70 | 79 |
| `su3-8x8x8x16-nofield` | 28.981 | 28.991 | 29.545 | 29.172 | 0.323 | 1.1% | 56.98 | 84 |

"Sweeps / s" is 2,448 total sweeps divided by the mean complete-job time, so it
includes fixed overhead.

Run IDs (under `results/runs/`, which is not committed):

| Request | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| `u1-4x4x4x8-field` | `52d476238c1f4d81a75cdc29f2821255` | `d935fd6002d54ff79150718ec4d04b55` | `b21f27fb24684d6987e9c659eb5ad0c2` |
| `u1-4x4x4x8-nofield` | `8471cd67c5544976a999255f87c1b6ce` | `3d0913926bf442bf8ec4358c00c5781c` | `517152502ab14db2b43a283736299708` |
| `u1-8x8x8x16-field` | `bbd874085f1e41f1bae2409c166ce1bd` | `a9f74bb0807949d0ab73e2b8a358015c` | `e2214f46f5a744768b890e9dc6112776` |
| `u1-8x8x8x16-nofield` | `2785df3072d44c92a733453741cf2546` | `b6d07aa5f3e04f89b9fbc99540d042e1` | `afab36f247c447acafa5bc1fe133d458` |
| `su3-4x4x4x8-field` | `db333a58fddc4f608bc2ada60a50c092` | `2800e15d395146bd98ffaf7dc7902865` | `ea5299ce771f4fa3ae73453ab8fb75ef` |
| `su3-4x4x4x8-nofield` | `de934eccb52b4c7f8f82afdf993ff2a4` | `350e06ac136347acb7432cdcca1734cd` | `bb0f6fa5bd8d4b40a8b0b0f4cbecec84` |
| `su3-8x8x8x16-field` | `a171bcb78d31458280380fedbda6c61f` | `5c5693309f0b4b4b955020a9c20332be` | `794b90cd5b2b41f7a3c5900d2bc6a915` |
| `su3-8x8x8x16-nofield` | `5b6abaf6c5d34140955dbc787b740c5b` | `70886689a2a94e21a700afe5c6ab7922` | `b99a5a7bc7b7485ea08a4edbdf0d12ac` |

## Observations

- Variation between repetitions is under 2% for every request, so the numbers
  are stable enough to compare against.
- The small `[4,4,4,8]` jobs take about 1.8–2.2 s regardless of group. That
  suggests a fixed per-job cost (process start, binary snapshot, analysis,
  HDF5 and JSON writing) dominates at this size. `timing.json` doesn't split
  that cost from the sampling time, so GPU speedups on the small lattice will
  be limited by that overhead rather than by the kernels.
- Field measurement adds about 20% to the large U(1) job and about 7% to the
  large SU(3) job.
- The large SU(3) lattice is the most compute-bound workload: 16× the sites of
  the small lattice and about 15× the time.

## Performance target for GPU-01.13

**Workload:** `configs/benchmarks/su3-8x8x8x16-nofield.json`, same host,
complete-job `elapsed_seconds`, mean of at least three repetitions.

**Target:** the CUDA build completes it at least **5× faster** than the CPU
baseline, a mean of **≤ 5.83 s** against 29.17 s.

This is measured on complete-job time, so it includes the fixed per-job
overhead noted above. Treat 5× as the proposed target: confirm or adjust it
before GPU-01.13 starts, and record any change here.
