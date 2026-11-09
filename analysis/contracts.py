"""API and artifact schema. All physical quantities use lattice units."""
from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = 1


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class AnalysisSettings(Contract):
    fit_min: int = Field(2, ge=1)
    fit_max: int = Field(3, ge=1)
    block_size: int | None = Field(None, ge=1)
    min_blocks: int = Field(16, ge=8)
    min_effective_samples: int = Field(32, ge=16)

    @model_validator(mode="after")
    def ordered(self):
        if self.fit_min > self.fit_max:
            raise ValueError("fit_min must not exceed fit_max")
        return self


class SimulationRequest(Contract):
    gauge_group: Literal["u1", "su3"] = "u1"
    extents: tuple[int, int, int, int] = (4, 4, 4, 8)
    beta: float = Field(1.0, gt=0, le=20)
    separation: int = Field(1, ge=1)
    chains: int = Field(4, ge=1, le=16)
    warmup_sweeps: int = Field(100, ge=0, le=100000)
    measurements: int = Field(128, ge=8, le=100000)
    sweeps_between_measurements: int = Field(2, ge=1, le=1000)
    seed: int = Field(1, ge=0, le=2**63 - 1)
    proposal_scale: float = Field(.7, gt=0, le=3.141592653589793)
    start: Literal["cold", "hot"] = "cold"
    max_r: int = Field(2, ge=1, le=16)
    max_t: int = Field(4, ge=2, le=16)
    measure_field: bool = True
    field_t: int = Field(3, ge=1)
    probe: tuple[int, int] = (0, 3)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)

    @model_validator(mode="after")
    def geometry(self):
        import math
        if any(n < 4 or n > 32 for n in self.extents) or math.prod(self.extents) > 131072:
            raise ValueError("Four periodic extents in [4,32], volume <=131072 required")
        if self.max_r > min(self.extents[:3]) // 2 or self.separation > self.max_r:
            raise ValueError("separation <= max_r <= half of every spatial extent required")
        if self.max_t > self.extents[3] // 2 or self.field_t > self.max_t:
            raise ValueError("field_t <= max_t <= half the temporal extent required")
        if self.analysis.fit_max >= self.max_t:
            raise ValueError("fit_max needs a following temporal loop (fit_max < max_t)")
        if len(set(self.probe)) != 2 or any(p < 0 or p > 3 for p in self.probe):
            raise ValueError("probe needs two distinct directions in [0,3]")
        if self.chains * self.measurements > 200000:
            raise ValueError("Local jobs are bounded to 200000 measurements")
        return self

    def toml(self) -> str:
        loops = [[r, t] for r in range(1, self.max_r + 1) for t in range(1, self.max_t + 1)]
        return f'''schema_version = 1
[model]
gauge_group = "{self.gauge_group}"
action = "wilson"
beta = {self.beta}
[lattice]
extents = {list(self.extents)}
boundary = "periodic"
spacing = 1.0
[sampling]
chains = {self.chains}
warmup_sweeps = {self.warmup_sweeps}
measurement_sweeps = {self.measurements}
sweeps_between_measurements = {self.sweeps_between_measurements}
seed = {self.seed}
[update]
algorithm = "metropolis"
proposal_scale = {self.proposal_scale}
[observables]
plaquette = true
polyakov_loop = false
wilson_loops = {loops}
[execution]
backend = "cpu"
precision = "double"
threads = 1
[output]
directory = "results"
format = "jsonl"
save_configurations = false
configuration_interval = 100
'''


class Job(Contract):
    id: str
    state: Literal["queued", "running", "completed", "failed", "cancelled"]
    request: SimulationRequest
    created: str
    updated: str
    progress: float = 0
    error: str | None = None


class MeasurementHistory(Contract):
    schema_version: int = SCHEMA_VERSION
    source_run: str
    chain: list[int]
    sweep: list[int]
    plaquette: list[float]
    acceptance: list[float]
    loops: list[list[float]]
    loop_definitions: list[tuple[int, int]]


class Potential(Contract):
    separation: int
    value: float | None = None
    measurement_error: float | None = None
    fit_window_variation: float | None = None
    status: Literal["validated", "unvalidated", "unavailable"]
    reasons: list[str] = Field(default_factory=list)
    effective_mass: list[float | None] = Field(default_factory=list)
    effective_mass_error: list[float | None] = Field(default_factory=list)
    chi2_dof: float | None = None
    fit_pvalue: float | None = None


class AnalyzedPotentials(Contract):
    schema_version: int = SCHEMA_VERSION
    source_runs: list[str]
    settings: AnalysisSettings
    units: str = "r/a, aV"
    potentials: list[Potential]
    covariance: list[list[float]] | None = None
    diagnostics: dict
    formula: dict


class FieldMap(Contract):
    schema_version: int = SCHEMA_VERSION
    source_runs: list[str]
    label: str = "Source-induced action-density response in lattice units"
    status: Literal["resolved", "unresolved", "unavailable"]
    reasons: list[str]
    separation: int
    temporal_extent: int
    probe: tuple[int, int]
    plane: str = "xy; sources along x; translation average; t=floor(T/2)"
    symmetry_averaging: str = "Translations, transverse y reflection, source exchange; reflected plaquette anchors shifted by their orientation"
    shape: tuple[int, int]
    values: list[list[float]] | None = None
    errors: list[list[float]] | None = None
    temporal_stability: str = "Not tested: compare independent runs with other source temporal extents"
    analysis_settings: AnalysisSettings


class PredictionRequest(Contract):
    model_id: str
    gauge_group: Literal["u1", "su3"]
    beta: float
    extents: tuple[int, int, int, int]
    separations: list[int] = Field(min_length=1, max_length=32)


class Prediction(Contract):
    schema_version: int = SCHEMA_VERSION
    model_id: str
    source_runs: list[str]
    status: str
    separations: list[int]
    formula: list[float]
    formula_error: list[float]
    mean: list[float]
    model_std: list[float]
    interval_95: list[tuple[float, float]]
    convention: str = "V(r)-V(1), in lattice units"
    evaluation: dict
