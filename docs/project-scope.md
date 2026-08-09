# Defining the project

## Start from an observable, not an algorithm

"Combine traits from potentials and lattice geometries" is a useful intuition,
but it is not yet a mathematical model. First state what the code should predict
and which theory generates the answer.

For an initial version, use the following contract.

### Inputs

- Spatial and temporal extents: `Nx`, `Ny`, `Nz`, `Nt`.
- Lattice spacing `a`, or dimensionless quantities when no physical scale has
  yet been set.
- Boundary conditions, initially periodic.
- Gauge group/model: begin with U(1), progress through SU(2) to pure SU(3).
- Bare coupling, commonly represented by `beta`.
- Source geometry: separation, orientation, and Wilson-loop dimensions.
- Random seed, warm-up length, sample count, and sampling interval.

### Direct simulator outputs

- Mean plaquette.
- Wilson loops `W(r, t)`.
- Autocorrelation estimates and effective sample count.
- Optional Polyakov loops and two-point correlation functions.

### Predictor outputs

- An observable with an uncertainty, not only a point estimate.
- For the static-source example: `V(r)` or dimensionless `a V(r)` at requested
  separations.
- A warning or rejection when an input is outside the training domain.

## Where potentials enter

There are three conceptually different uses of a potential:

1. **A measured effective potential.** In gauge theory, the static quark
   potential is inferred from Wilson loops; it is an output of the simulation.
2. **A fit ansatz.** A form such as a constant plus Coulomb-like and linear terms
   can summarize measured data over a stated range. It does not replace the
   underlying gauge action.
3. **A model Hamiltonian.** A chosen potential can define a nonrelativistic or
   toy lattice model. This can be worthwhile, but it should be labeled an
   effective model rather than lattice QCD.

Keep these roles separate in code, configuration files, plots, and reports.

## Geometry representation

Represent geometry explicitly instead of hiding it in a generic feature vector.
Useful fields include:

- lattice extents and anisotropy;
- periodic, open, or fixed boundaries;
- displacement vectors between sources;
- path/link orientation;
- loop dimensions and symmetry class;
- distance in lattice units and, after scale setting, physical units.

On a cubic periodic lattice, rotations, reflections, translations, and periodic
images create equivalent cases. A predictor should encode or augment these
symmetries so that equivalent inputs produce equivalent outputs. Gauge-dependent
raw link values are not suitable ordinary features unless the model is designed
to be gauge equivariant; gauge-invariant observables are the safer first input.

## Baseline predictor

Do not start with a neural network. Establish these baselines first:

1. interpolation within a table of simulated measurements;
2. a physics-motivated regression in `r`, lattice size, and coupling;
3. Gaussian-process regression for a small dataset, including predictive
   uncertainty;
4. only then, a larger learned surrogate if data volume and accuracy require it.

Split training and validation data by entire parameter regions, not randomly by
neighboring Monte Carlo samples. Neighboring samples from one chain are
correlated and can make validation look much better than it is.

## Definition of success for version 0.1

- The same seed produces the same CPU result.
- Local action changes agree with a slow full-action calculation.
- Gauge-invariant observables remain unchanged under random gauge
  transformations, within floating-point tolerance.
- A tiny-lattice calculation agrees with brute-force or independently written
  reference calculations where feasible.
- Estimated uncertainties grow when the number of independent samples falls.
- Results are stable under longer warm-up and changed sampling intervals.
- The predictor beats a constant-mean baseline on held-out parameter regions.
- Every result records model, lattice, algorithm, precision, seed, and code
  revision.

## Claims to avoid

- A visually plausible potential curve is not evidence of QCD accuracy.
- More lattice sites do not automatically mean a continuum result; continuum
  extrapolation requires multiple lattice spacings and controlled scale setting.
- More saved configurations do not imply independent data.
- Agreement between a GPU kernel and itself is not validation; compare against a
  simple CPU reference and analytic invariants.
