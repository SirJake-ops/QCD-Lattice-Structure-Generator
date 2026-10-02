# QCD lattice predictor: starting guide

This directory turns the initial idea into a project that can be built and
tested in stages. The most important first decision is what **predictor** means.

## Two related projects

### 1. A lattice field simulator

A simulator samples field configurations from a discretized Euclidean action
and estimates observables from the samples. For lattice QCD, the fundamental
variables are SU(3) matrices on links; including quarks also requires expensive
linear solves involving the Dirac operator.

This is the physically direct route, but a production-quality QCD code is a
large research-software project.

### 2. A surrogate or effective-model predictor

A predictor takes inputs such as coupling constants, lattice dimensions,
boundary conditions, source geometry, and parameters of an effective potential,
then predicts observables such as energy, force, correlation length, or Wilson
loops. Its training and validation data can come from a small simulator,
published data, or established lattice packages.

This is the recommended interpretation for an initial project. It lets the
project explore how potentials and geometry affect observables without claiming
that an arbitrary potential is itself QCD.

## Recommended path

1. Implement and test a small classical lattice model on the CPU.
2. Add a compact U(1) gauge model to learn links, plaquettes, gauge invariance,
   Markov-chain Monte Carlo, and autocorrelation.
3. Implement pure SU(2), then pure SU(3), using the Wilson gauge action.
4. Measure Wilson loops and extract a static-source potential.
5. Generate a labeled dataset while varying couplings and geometry.
6. Fit a simple, uncertainty-aware surrogate and compare it with held-out Monte
   Carlo results.
7. Optimize measured bottlenecks; fill in the optional CUDA backend only when
   CPU results are correct and reproducible.

Do not begin with dynamical fermions. Fermion determinants, Dirac-operator
solves, and algorithms such as Hybrid Monte Carlo multiply the mathematical and
engineering difficulty.

## Reading order

- [Defining the project](project-scope.md) narrows the scientific question and
  specifies inputs, outputs, and success criteria.
- [Physics and numerical foundations](physics-and-numerics.md) introduces the
  lattice formulation, common observables, Monte Carlo, and validation.
- [Lattice calculation flow](lattice-calculation-flow.md) gives a Mermaid-based
  visual reference from lattice construction through sampling and potential
  extraction.
- [Common lattice-QCD challenges](common-challenges.md) maps the main physical
  and computational problems to standard mitigation strategies.
- [Implementation roadmap](implementation-roadmap.md) proposes modules,
  milestones, tests, and data formats.
- [Training-data sources](training-data-sources.md) compares public ensemble
  archives, independent generators, and a staged ingestion strategy.
- [CUDA decision guide](cuda.md) explains when GPU acceleration is worthwhile
  and how to add it without losing a reliable CPU reference.

## A good first scientific question

> For pure gauge theory on a small periodic lattice, can the program estimate
> rectangular Wilson loops and recover a stable effective static potential as
> lattice size, coupling, and source separation change?

This question is limited enough to test, contains real lattice-gauge concepts,
and creates exactly the kind of data later needed by a surrogate predictor.

## Useful books

- C. Gattringer and C. B. Lang, *Quantum Chromodynamics on the Lattice*.
- H. J. Rothe, *Lattice Gauge Theories: An Introduction*.
- T. DeGrand and C. DeTar, *Lattice Methods for Quantum Chromodynamics*.
- M. E. J. Newman and G. T. Barkema, *Monte Carlo Methods in Statistical
  Physics* (useful for Markov chains and error analysis).

These notes are a project map, not a replacement for a lattice-field-theory
course or a verification against established software and published results.
