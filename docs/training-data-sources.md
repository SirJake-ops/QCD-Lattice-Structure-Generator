# Training-data sources

## Recommendation

Use a hybrid data strategy:

1. Generate the primary training grid with a controlled simulator whose action,
   conventions, update history, and observable definitions are recorded.
2. Use public gauge configurations to validate the import and measurement
   pipeline and to check selected compatible parameter points independently.
3. Add dynamical-QCD ensembles only after the dataset schema represents fermion
   content, improved actions, anisotropy, boundary conditions, and scale setting.

This matters because a gauge configuration is not already a labeled training
row. Plaquettes, Wilson loops, effective potentials, autocorrelation estimates,
and uncertainties must still be measured consistently. Configurations from one
Markov chain are correlated and must not be randomly split across training and
validation sets.

## Configuration archives

### International Lattice Data Grid (ILDG)

- [ILDG overview](https://hpc.desy.de/ildg/) describes a federation of regional
  repositories containing gauge-field ensembles, searchable XML metadata, and
  standardized binary formats.
- [ILDG services](https://hpc.desy.de/ildg/services/) documents the current IAM
  membership route and the metadata, file-catalogue, and storage services.
- [ILDG specifications](https://hpc.desy.de/ildg/specifications/) provides the
  QCDml 2.0 schemas and gauge-configuration file-format specification.
- [ILDG metadata indices](https://hpc.desy.de/ildg/metadata_indices/) links the
  available catalogues, including JLDG and the DOE Data Explorer.

ILDG is the broadest place to search, but access conditions vary by ensemble and
regional grid. Preserve the logical file name, ensemble identifier, checksums,
QCDml metadata, citation, and usage policy with every imported configuration.

### DOE Data Explorer and USQCD/MILC

- [DOE's Lattice QCD dataset search](https://www.osti.gov/dataexplorer/search/product-type%3ADataset/semantic%3ALattice%20QCD)
  exposes DOI-indexed public records, including many MILC `Nf=2+1` asqtad SU(3)
  gauge ensembles at several lattice spacings, volumes, and quark masses.
- [DOE Data Explorer API](https://www.osti.gov/dataexplorer/api/v1/docs) can
  return searchable record metadata as JSON, XML, or BibTeX.

These records are useful for a reproducible catalogue-ingestion prototype and
later dynamical-QCD work. They are not a drop-in match for an initial pure-gauge
Wilson-action model.

### Japan Lattice Data Grid (JLDG)

- [JLDG](https://www.jldg.org/) is an ILDG regional grid and lists publicly
  released PACS, PACS-CS, and JLQCD ensembles.
- Its [DOI index](https://www.jldg.org/DOI/) provides stable identifiers for
  public PACS-CS ensembles.
- Its [faceted QCDml navigator](https://www.jldg.org/facetnavi/) is designed to
  filter metadata such as lattice size, flavour count, action, beta, and mass.

JLDG is a strong alternative discovery interface to the general ILDG services,
especially when stable DOI attribution is important.

### OpenLat

- [OpenLat](https://openlat1.gitlab.io/) produces and shares `Nf=2+1`
  stabilized-Wilson ensembles and states an open-science goal of freely and
  quickly granting access.
- Its configurations use an improved gauge action and may use periodic or open
  temporal boundaries, so those fields must be explicit model inputs rather
  than silently combined with Wilson-action data.

OpenLat is most relevant after the project progresses beyond pure gauge theory.

### FASTSUM on Zenodo/Storj

- [FASTSUM Generation 2](https://zenodo.org/records/8403827) provides freely
  usable anisotropic thermal `Nf=2+1` ensembles, clear citation requirements,
  direct HTTP/S3 access, and configurations in ILDG and openQCD formats.

Because access and metadata are unusually clear, FASTSUM is a practical small
external-ingestion pilot. Its anisotropy, improved action, finite temperature,
and dynamical fermions make it unsuitable for direct mixing with a pure-Wilson
training grid.

### Zenodo and paper supplements

- The [ILDG Zenodo community](https://zenodo.org/communities/ildg/) is a useful
  discovery point for ensemble records and supporting material.
- Paper-specific deposits sometimes provide analysis-ready arrays rather than
  gauge fields. For example, this [SU(3) deconfinement dataset](https://zenodo.org/records/15256813)
  includes Polyakov-loop and derived data with plotting code.
- Search each relevant paper's DOI, INSPIRE record, and Zenodo attachments for
  correlators, observable tables, covariance information, and scripts.

These deposits can be easier to prototype with than raw configurations, but
their schemas and usage terms are heterogeneous and require record-by-record
review.

## Independent generators for matched data

For the initial pure SU(3) Wilson-action problem, an established generator may
be more useful than an unmatched public ensemble:

- [SIMULATeQCD](https://github.com/LatticeQCD/SIMULATeQCD) is an actively
  maintained multi-GPU C++ lattice code. Its `generateQuenched` application uses
  heat-bath and over-relaxation updates for pure Wilson-action configurations.
- [Chroma](https://usqcd-software.github.io/) provides a mature USQCD
  application ecosystem; its `purgaug` workflow can generate quenched SU(3)
  configurations.
- [CL2QCD](https://zenodo.org/record/5121917) includes an OpenCL
  `su3heatbath` application for pure SU(3) gauge theory.

Use one of these to generate a small independent comparison ensemble at exactly
matching `beta`, volume, action, boundary conditions, and measurement
conventions. Do not treat agreement between two configurations with the same
random seed as the goal; compare ensemble observables and uncertainties.

## Proposed ingestion spike

Before downloading a large ensemble:

1. Select 5-20 configurations with complete metadata and permissive access.
2. Record the source URL, DOI, ensemble ID, configuration ID, checksum, action,
   dimensions, boundary conditions, flavour content, and trajectory/sweep.
3. Convert into one internal format without discarding the original metadata.
4. Verify checksums and SU(3) unitarity/determinant tolerances after conversion.
5. Measure the plaquette and compare its ensemble mean with a published or
   provider-supplied value.
6. Measure Wilson loops using the same orientation, normalization, and smearing
   convention planned for generated data.
7. Split evaluation data by entire ensemble or parameter region, never by
   neighboring configurations from the same chain.

Only scale up after this round trip is reproducible and storage estimates are
known.
