# CUDA decision guide

## Short answer

CUDA can be a very good fit for large, regular lattice calculations, but it
should be a later backend rather than the first implementation. A correct,
small CPU version is the reference needed to tell whether a fast GPU result is
physically and numerically correct.

The best candidates are operations performed independently over many sites or
links:

- evaluating local staples and action contributions;
- applying stencil-like field operators;
- updating independent checkerboard subsets;
- measuring plaquettes and many Wilson-loop paths;
- reductions over the lattice;
- later, iterative sparse linear algebra for fermion calculations.

Small lattices, frequent host-device transfers, serial update dependencies, or
heavy per-step allocation can eliminate the benefit.

## Decision rule

Add a CUDA prototype after all of the following are true:

1. The CPU implementation passes correctness and gauge-invariance tests.
2. A realistic dataset is large enough that simulation time matters.
3. Profiling identifies one or two kernels that dominate runtime.
4. Their work can be batched across thousands of sites or links.
5. Fields can remain on the device across many sweeps and measurements.

Before that point, compiler optimization, better memory layout, threading, and
algorithmic improvements usually provide faster development progress.

## Design now so CUDA is possible later

- Store lattice fields contiguously.
- Prefer structure-of-arrays or an explicitly benchmarked compact layout when it
  gives coalesced access.
- Separate lattice indexing, physics operations, update policy, and storage.
- Avoid embedding host-only pointers or I/O inside field operations.
- Batch measurements and copy back summaries rather than full fields when
  possible.
- Make numeric precision a deliberate type/configuration choice.

Do not force the entire design into GPU abstractions on day one. A clean boundary
between the physics interface and backend is enough.

## Correctness hazards

### Parallel updates

Updating adjacent links simultaneously may change the transition kernel because
their local actions share data. Use a proven coloring/checkerboard schedule or a
correct algorithm whose parallel transition rule is explicitly derived. Do not
parallelize a serial Metropolis loop mechanically.

### Random numbers

Each logical update needs a reproducible, non-overlapping random stream. Record
the generator, seed, stream/key derivation, and mapping from work item to stream.
Results should be statistically equivalent across backends even when they are
not bit-for-bit identical.

### Floating-point reductions

Parallel sums occur in a different order and therefore round differently. Test
with scientifically justified tolerances. Consider double-precision accumulation
for sensitive global quantities, then benchmark whether mixed precision is safe.

### Group drift

Repeated floating-point SU(3) operations can drift from exact unitarity and unit
determinant. Monitor constraints and use a documented reunitarization strategy
when the chosen algorithm requires it.

### Performance-only validation

Kernel timing alone can be misleading. Measure complete sweeps or configurations,
including synchronization, reductions, and unavoidable transfers. Always report
lattice size, precision, GPU, compiler options, and measurement method.

## Backend options

There are three reasonable strategies:

1. **Direct CUDA:** most control and NVIDIA-specific optimization, at the cost of
   maintaining a separate backend.
2. **Portable performance layer:** a framework such as Kokkos can target CPUs and
   multiple accelerator systems, but introduces concepts and dependencies.
3. **Use an established lattice package:** best if the scientific goal becomes
   producing credible QCD ensembles rather than learning by implementing the
   algorithms.

For this learning project, begin with ordinary C++ and add one small direct-CUDA
kernel only after profiling. If portability becomes a real requirement, evaluate
a portability layer with a benchmark of the actual lattice kernel rather than a
microbenchmark alone.

## First GPU experiment

Use a read-only measurement kernel before porting Markov updates:

1. Copy an already validated gauge configuration to the GPU.
2. Compute one plaquette contribution per site and plane.
3. Reduce the contributions to an average.
4. Compare with the CPU implementation over random and hand-constructed fields.
5. Benchmark a range of lattice sizes with the field kept resident on-device.

This tests indexing, memory layout, matrix operations, reduction, and numerical
tolerances without risking a subtle change to the Monte Carlo distribution.

## Practical conclusion

Your GPU is likely to become useful, especially as volumes grow. It is not needed
to answer the first scientific questions. Build the CPU reference, gather a
profile, and treat CUDA as a measured optimization milestone rather than a
foundational dependency.
