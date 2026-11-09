# Local implementation and validation report

Date: 2026-11-09. These are development-run results, not a claim of precision QCD.

## Software checks

- Release: 30/30 C++ tests pass.
- Address/undefined-behavior sanitizer Debug build: 30/30 tests pass.
- Python: 15/15 tests pass, covering statistical estimators, field comparison,
  model isolation, and API/worker integration.
- React/TypeScript production build passes. Plotly produces a large local bundle
  (about 5.64 MB uncompressed); there are no external runtime assets.
- Chromium: both workflow tests pass, including a real simulation, cancellation,
  rotation/time selection, mobile overflow, an actual trained-model comparison,
  and an actual measured response/error map. No page errors were observed.

The local C++ build used GCC 16.2.1 and existing cached Eigen/toml++/GoogleTest
source trees via FetchContent overrides. The cached Eigen tree identifies itself
as 5.0.0-dev+c9ecd262. A network-clean checkout build was not performed here;
CI now specifies C++ Debug/Release/sanitizer and full application jobs. Python
versions are frozen in `requirements.lock`, npm versions in `package-lock.json`.

## Pilots and performance

The initial 4×4×4×8 U(1) pilot took 1.64 seconds for 256 measurements and returned
unvalidated potentials, correctly exposing insufficient effective statistics and
plateau problems. A comparable short SU(3) pilot exposed poor chain agreement
and effective statistics; SU(3) remains independently unbenchmarked.

A 6×6×6×12 U(1) run at beta=1.3, four chains, 1000 warm-up sweeps, 512
measurements/chain, gap=4, loops through T=6, took 25.59 seconds. Chain diagnostics
passed but all three potential plateaus failed stability/fit checks. It is excluded
from training. Its field map was measured rather than synthesized.

An 8×8×8×24 U(1) run with loops through r=4,T=12 and fit t=8..10 took 170.98
seconds before caching. Subsequent runs with matching sampling settings and cached
straight transporters took approximately 37 seconds (different couplings/seeds;
this is an end-to-end cost comparison, not a controlled speedup benchmark).
Cached and direct loop estimators agree in U(1)/SU(3) structural tests.

At beta=1.3, seed=1, four cold-start chains, 800 warm-up sweeps, 256
measurements/chain and gap=4, internal diagnostics were R-hat=1.0773,
effective samples=88.0, block size=12. The accepted internal estimates were:

| r/a | aV | Measurement SE |
|---|---:|---:|
| 1 | 0.170736 | 0.000390 |
| 2 | 0.216431 | 0.000758 |
| 3 | 0.231201 | 0.001156 |
| 4 | 0.238394 | 0.001591 |

Run `9508f524d2d24d02b1dafff92f61d30e` retains raw histories, fit settings,
covariance, and source hashes in `results/plateau-corpus/runs/`. Passing these
internal gates does not establish infinite-volume or continuum accuracy.

## Frozen dataset and experimental model

The primary bounded grid used beta=1.30,1.35,1.40,1.45,1.50,1.55,1.60; a fixed
follow-up added beta=1.65 and independent temporal field-map runs. Beta=1.35
failed a plateau check at r=2 and the original beta=1.60 run failed at r=1.
They were excluded without changing the declared window to make them pass.

Dataset `efccede305ba4b439362fc558ddf13ca` freezes six accepted beta points:
1.30,1.40,1.45,1.50,1.55,1.65, all on 8×8×8×24 with four independent chains.
Training uses 1.30,1.40,1.45,1.55; interpolation holdout is the whole beta=1.50
point; region holdout is the whole beta=1.65 point. Follow-up field studies do not
alter this split. Source IDs and artifact checksums are in the dataset manifest.

Model `41786346dbd84565b15bd10bfd53d6ba` predicts V(r)-V(1), r/a=1..4,
only at this exact volume and beta in [1.30,1.55]. It rejects other volumes,
groups, and extrapolation. GP hyperparameters approached kernel bounds; model
estimates are experimental. Measurements, same-run fitted formulas, and model
predictions use compatible additive conventions when overlaid in the browser.

| Held-out split | Constant RMSE | Interpolation RMSE | Cornell RMSE | GP RMSE |
|---|---:|---:|---:|---:|
| Interpolation beta=1.50 | 0.004024 | 0.000535 | 0.000959 | 0.000870 |
| Region beta=1.65 | 0.010456 | 0.001732 | 0.001943 | 0.001931 |

Each split has only one parameter point and three nonreference separations.
Approximate 95% latent intervals cover 2/3 measured interpolation targets and
3/3 region targets. Including held-out measurement errors gives 3/3 in both.
The GP improves on Cornell alone here but does not beat ordinary interpolation.
There is insufficient evidence to advertise calibrated accuracy. The region
evaluation is an extrapolation audit; the public API still rejects that beta.
Baseline/residual uncertainty dependence and diagonal GP noise are explicit
limitations in [the contract](application-contract.md).

## Measured flux response and temporal check

Independent beta=1.60, 8×8×8×24, separation=2, xt plaquette probes in the xy
plane were measured at source T=7,9,11 with seeds 26,25,27 respectively. Each
uses four chains, 800 warm-up sweeps, 256 measurements/chain and gap=4. Joint
products, vacuum subtraction, translations, reflected plaquette anchors, and
source exchange are included. All three maps have pointwise resolved responses.

Runs are `b4b874fa49104b28a3fda524f32d8409` (T=7),
`e2f0bdf9fa024f3b81514548c90146c4` (T=9), and
`ddf5fa2799934631960d2f5b726a84b5` (T=11). Compared with T=11, maximum
standardized differences are 2.661 and 2.085. Both are below the conservative
familywise normal threshold 3.546. The report is
`results/plateau-corpus/field-validation/temporal-pilot/report.json`.

The maps are compatible within these uncertainties. This is not proof of
ground-state isolation or physical energy-density normalization. Full volume,
orientation, and finite-coupling start-systematic studies remain scientific work.
Original sealed maps retain their original temporal-stability caveat; the
separate comparison report records the later independent evidence.

## Remaining scientific acceptance

Matched independent finite-coupling SU(3) validation has not been performed.
The benchmark training gate remains closed. A larger multi-volume corpus,
more held-out parameter regions, finite-coupling hot/cold agreement, and broader
field-map stability studies are required before broader scientific claims.
No public dynamical ensemble was mixed into pure-gauge training. No physical
scale, continuum prediction, or learned field map was produced.
