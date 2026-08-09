# Common lattice-QCD challenges

There is no single numerical trick that "solves QCD." Lattice work combines a
field-theory discretization, importance sampling, linear algebra, statistical
analysis, and extrapolation. The table below is a map of recurring problems and
the standard families of responses.

| Problem | Why it matters | Common responses |
| --- | --- | --- |
| Finite lattice spacing | Results contain discretization artifacts. | Use an improved action where justified, simulate several spacings, and extrapolate toward `a = 0`. |
| Finite volume | Periodic images and limited long-distance modes shift observables. | Repeat at multiple volumes and keep physical correlation lengths small relative to the box. |
| Autocorrelation and critical slowing down | Stored configurations are not independent; topology may evolve very slowly at fine spacing. | Measure autocorrelation, bin data, lengthen chains, use improved update algorithms, and compare independent chains. |
| Expensive fermions | The fermion determinant and repeated Dirac solves dominate realistic QCD costs. | Use Hybrid Monte Carlo variants, preconditioned Krylov solvers, multigrid/deflation, and established libraries. |
| Chiral symmetry and fermion doubling | A naive lattice Dirac operator produces unwanted species; discretizations trade cost against symmetry/artifacts. | Choose Wilson, staggered, domain-wall, or overlap fermions based on the observable and document the tradeoff. |
| Noisy long-distance observables | Correlator signal often decays faster than its noise. | Improve operators, use smearing, average symmetry-related measurements, increase independent statistics, and use correlated fits. |
| Scale setting and renormalization | Bare lattice numbers are not automatically physical predictions. | Determine a scale from a reference observable and compute/match renormalization factors in a declared scheme. |
| Excited-state contamination | A finite-time correlator or Wilson-loop ratio may not isolate the desired ground state. | Use multiple operators, larger time separations where signal permits, variational methods, and fit-window stability studies. |
| Sign problem | At real baryon chemical potential, the weight is generally not a positive probability. | Restricted regimes use reweighting, Taylor expansion, imaginary chemical potential, or specialized methods; no general solution is known. |
| Large data and bandwidth cost | Gauge fields and solver vectors consume substantial memory and traffic. | Use local/streaming measurements, compression only when validated, checkpoint policies, and layouts designed for the target hardware. |

## What applies to this project first

For the proposed pure-gauge starting point, prioritize:

1. correct boundary/index handling;
2. equilibration and autocorrelation;
3. gauge invariance;
4. finite-volume checks;
5. Wilson-loop noise and fit stability;
6. lattice-spacing studies only after a physical scale can be set.

Fermion discretization, Dirac solvers, and the sign problem belong on the longer
term map, but they should not drive version 0.1.

## A pattern for numerical studies

Change one source of uncertainty at a time and keep the rest of the setup
recorded:

```text
reference run
  -> longer warm-up and chain       (equilibration/statistics)
  -> larger spatial volume          (finite-volume effect)
  -> finer lattice at matched scale (discretization effect)
  -> alternate fit windows          (analysis systematic)
  -> alternate validated algorithm  (algorithm dependence)
```

The result is not just a number. A defensible result includes its statistical
uncertainty, known systematic effects, action and parameter conventions, and the
range in which any fitted predictor has been tested.

## When to use established software

Writing small models is excellent for learning and for developing a novel
surrogate. Producing research-grade dynamical-QCD ensembles is different: it is
usually safer to use and validate against mature community lattice software.
That lets this project focus its originality on geometry representations,
observable extraction, or surrogate modeling instead of reimplementing every
low-level solver and update algorithm.
