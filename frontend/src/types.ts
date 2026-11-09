export type Request = {
  gauge_group: "u1" | "su3";
  extents: [number, number, number, number];
  beta: number;
  separation: number;
  chains: number;
  warmup_sweeps: number;
  measurements: number;
  sweeps_between_measurements: number;
  seed: number;
  proposal_scale: number;
  start: "cold" | "hot";
  max_r: number;
  max_t: number;
  measure_field: boolean;
  field_t: number;
  probe: [number, number];
  analysis: {
    fit_min: number;
    fit_max: number;
    block_size: number | null;
    min_blocks: number;
    min_effective_samples: number;
  };
};
export type Job = {
  id: string;
  state: "queued" | "running" | "completed" | "failed" | "cancelled";
  request: Request;
  created: string;
  updated: string;
  progress: number;
  error: string | null;
};
export type Potential = {
  separation: number;
  value: number | null;
  measurement_error: number | null;
  fit_window_variation: number | null;
  status: string;
  reasons: string[];
  effective_mass: (number | null)[];
  effective_mass_error: (number | null)[];
  chi2_dof: number | null;
  fit_pvalue: number | null;
};
export type Analysis = {
  source_runs: string[];
  potentials: Potential[];
  covariance: number[][] | null;
  settings: Request["analysis"];
  diagnostics: {
    tau_int_measurements: number;
    effective_samples: number;
    block_size: number;
    blocks?: number;
    split_rhat: number | null;
    acceptance: number;
    plaquette: number;
    reasons: string[];
  };
  formula: {
    status: string;
    reason?: string;
    coefficients?: { c: number; alpha: number; s: number };
    separations?: number[];
    values?: number[];
    errors?: number[];
    source?: string;
  };
};
export type FieldMap = {
  label: string;
  status: string;
  reasons: string[];
  separation: number;
  temporal_extent: number;
  probe: [number, number];
  shape: [number, number];
  values: number[][] | null;
  errors: number[][] | null;
  temporal_stability: string;
};
export type Model = {
  id: string;
  gauge_group: string;
  status: string;
  domain: {
    extents: number[];
    beta: [number, number];
    separation: [number, number];
  }[];
};
export type Prediction = {
  model_id: string;
  status: string;
  separations: number[];
  formula: number[];
  formula_error: number[];
  mean: number[];
  model_std: number[];
  interval_95: [number, number][];
  convention: string;
  evaluation: Record<
    string,
    {
      rmse: Record<string, number>;
      latent_interval_coverage: number;
      observation_interval_coverage: number;
      observations: number;
      parameter_points: number;
    }
  >;
};
