# Physics and numerical foundations

## Why a lattice is used

Lattice field theory replaces continuous Euclidean spacetime by sites separated
by lattice spacing `a`. A finite lattice gives ultraviolet and finite-volume
cutoffs, turning the path integral into a very large but finite-dimensional
statistical-mechanics problem. Physical predictions require controlling both
cutoffs, usually by studying several spacings and volumes.

For gauge theories, storing a gauge potential directly at sites is inconvenient.
Instead, a link from site `x` in direction `mu` carries a group element
`U_mu(x)`. In QCD this is a 3-by-3 special unitary matrix in SU(3).

## The smallest gauge-invariant loop

The oriented plaquette is

```text
U_mu_nu(x) = U_mu(x)
             U_nu(x + mu)
             U_mu(x + nu)^dagger
             U_nu(x)^dagger.
```

For pure SU(3), a common starting point is the Wilson gauge action

```text
S_g = beta * sum_plaquettes [1 - (1/3) Re Tr(U_plaquette)].
```

Conventions differ, so document normalization and orientation in the code. A
local gauge transformation changes individual links but leaves traced closed
loops invariant. That invariance is one of the strongest implementation tests.

## From the action to estimates

Euclidean expectation values have the schematic form

```text
<O> = integral D[U] O[U] exp(-S[U]) / integral D[U] exp(-S[U]).
```

The integral cannot generally be evaluated by enumerating configurations. A
Markov chain instead produces configurations with the desired distribution.
For learning purposes, local Metropolis updates are easy to understand. More
specialized heat-bath/over-relaxation methods are often better for pure gauge
theories, while dynamical-fermion simulations commonly use global algorithms
such as Hybrid Monte Carlo.

A minimal sampling run is:

```text
initialize links
repeat warm_up_sweeps:
    update every link
repeat measurement_blocks:
    repeat sweeps_between_measurements:
        update every link
    measure observables
estimate means, autocorrelation, and uncertainty
```

Discarding warm-up does not prove equilibration. Compare hot and cold starts,
inspect histories, and repeat with longer warm-up.

## Observables relevant to the proposed predictor

### Plaquette

The average traced plaquette is inexpensive and is the first sanity check for a
gauge simulation. It is useful for testing thermalization and comparing known
parameter points, but it does not alone describe confinement or a potential.

### Wilson loops and a static potential

For a rectangular loop of spatial width `r` and Euclidean time extent `t`, the
large-`t` behavior is schematically

```text
W(r, t) proportional to exp[-V(r) t].
```

An effective estimate can be formed from neighboring time extents:

```text
a V_eff(r, t) = log[W(r, t) / W(r, t + 1)].
```

One looks for a stable region in `t`, while accounting for noise, excited-state
contamination, and correlations. Smearing can improve signal quality later, but
an unsmeared implementation is easier to validate first.

### Correlators and masses

For an operator with the desired quantum numbers, a Euclidean two-point
correlator can yield an energy or mass from its exponential decay. Operator
choice, finite temporal extent, correlated fitting, and excited states all
matter. This is a later milestone, not the first output.

## Error analysis is part of the physics

Successive configurations in a Markov chain are correlated. Reporting the
ordinary standard error as though every measurement were independent will
usually underestimate uncertainty.

Implement at least one of these approaches:

- blocking/binning until the uncertainty stabilizes;
- integrated autocorrelation-time estimation;
- block jackknife or block bootstrap for derived quantities and fits.

Run multiple independent chains when practical. Store chain identity and sweep
number with measurements.

There are also systematic errors: finite volume, nonzero lattice spacing,
thermalization, fit-window choice, imperfect operators, and surrogate-model
extrapolation. A small statistical error does not remove them.

## A learning ladder

Each stage should retain the same lattice-indexing, boundary, random-number,
measurement, and testing ideas where possible.

1. **Two-dimensional Ising model:** local Metropolis updates, thermalization,
   autocorrelation, finite-volume effects.
2. **Scalar field or compact U(1):** continuous/group-valued fields and local
   action changes.
3. **Pure SU(2):** non-Abelian group operations with a simpler matrix structure.
4. **Pure SU(3):** Wilson action, gauge tests, plaquettes, and Wilson loops.
5. **Dynamical fermions:** only after the pure-gauge code is mature, because this
   adds Dirac discretization, sparse solves, determinants, and much higher cost.

The Ising and U(1) stages are not throwaway exercises: they validate the
statistical and software machinery before SU(3) makes debugging harder.

## Validation hierarchy

Validate from cheapest to most physical:

1. group identities: unitarity and determinant constraints;
2. periodic indexing and path closure;
3. local action difference versus recomputed global action;
4. exact invariance of closed-loop observables under gauge transformations;
5. limiting behavior and tiny-lattice calculations;
6. independent CPU implementations for selected configurations;
7. published benchmark values with identical conventions and parameters;
8. volume, lattice-spacing, and algorithmic studies.

Never tune a surrogate on data whose simulator has not passed the lower levels.
