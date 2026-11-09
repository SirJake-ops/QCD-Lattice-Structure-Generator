import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import type { Data } from "plotly.js";
import { Lattice } from "./Lattice";
import { Plot } from "./Plot";
import type {
  Analysis,
  FieldMap,
  Job,
  Model,
  Prediction,
  Request,
} from "./types";
import "./style.css";

const defaults: Request = {
  gauge_group: "u1",
  extents: [4, 4, 4, 8],
  beta: 1.2,
  separation: 1,
  chains: 4,
  warmup_sweeps: 100,
  measurements: 128,
  sweeps_between_measurements: 2,
  seed: 1,
  proposal_scale: 0.7,
  start: "cold",
  max_r: 2,
  max_t: 4,
  measure_field: true,
  field_t: 3,
  probe: [0, 3],
  analysis: {
    fit_min: 2,
    fit_max: 3,
    block_size: null,
    min_blocks: 16,
    min_effective_samples: 32,
  },
};
const number = (n: number | null | undefined, digits = 4) =>
  n == null ? "—" : n.toFixed(digits);
async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const result = await fetch(`/api/v1${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
  });
  if (!result.ok) {
    const body = await result.json();
    throw new Error(
      typeof body.detail === "string"
        ? body.detail
        : JSON.stringify(body.detail),
    );
  }
  return result.json();
}
function App() {
  const [potentialR, setPotentialR] = useState(1);
  const [form, setForm] = useState<Request>(defaults),
    [jobs, setJobs] = useState<Job[]>([]),
    [selected, setSelected] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null),
    [field, setField] = useState<FieldMap | null>(null),
    [prediction, setPrediction] = useState<Prediction | null>(null);
  const [models, setModels] = useState<Model[]>([]),
    [model, setModel] = useState(""),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [time, setTime] = useState(0),
    [mapMode, setMapMode] = useState<"value" | "error">("value");
  const [health, setHealth] = useState(false);
  const job = jobs.find((j) => j.id === selected),
    view = job?.request ?? form;
  const update = <K extends keyof Request>(key: K, value: Request[K]) => {
    setForm((f) => ({ ...f, [key]: value }));
    setPrediction(null);
  };
  const refresh = async () => {
    const next = await api<Job[]>("/jobs");
    setJobs(next);
    return next;
  };
  useEffect(() => {
    Promise.all([
      api<{ simulator_available: boolean }>("/health"),
      api<Model[]>("/models"),
      refresh(),
    ])
      .then(([h, m]) => {
        setHealth(h.simulator_available);
        setModels(m);
        if (m.length) setModel(m[0].id);
      })
      .catch((e) => setError(String(e)));
  }, []);
  useEffect(() => {
    if (!jobs.some((j) => j.state === "running" || j.state === "queued"))
      return;
    const id = setInterval(() => {
      void refresh().catch((e) => setError(String(e)));
    }, 1000);
    return () => clearInterval(id);
  }, [jobs.map((j) => `${j.id}:${j.state}`).join(",")]);
  useEffect(() => {
    setAnalysis(null);
    setField(null);
    setTime(0);
    if (!selected || job?.state !== "completed") return;
    let current = true;
    Promise.all([
      api<Analysis>(`/jobs/${selected}/analysis`),
      api<FieldMap>(`/jobs/${selected}/field`),
    ])
      .then(([a, f]) => {
        if (current) {
          setAnalysis(a);
          setField(f);
        }
      })
      .catch((e) => {
        if (current) setError(String(e));
      });
    return () => {
      current = false;
    };
  }, [selected, job?.state]);
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    setPrediction(null);
    try {
      const next = await api<Job>("/jobs", {
        method: "POST",
        body: JSON.stringify(form),
      });
      setSelected(next.id);
      setPotentialR(form.separation);
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };
  const predict = async () => {
    setBusy(true);
    setError("");
    try {
      setPrediction(
        await api<Prediction>("/predictions", {
          method: "POST",
          body: JSON.stringify({
            model_id: model,
            gauge_group: form.gauge_group,
            beta: form.beta,
            extents: form.extents,
            separations: Array.from({ length: form.max_r }, (_, i) => i + 1),
          }),
        }),
      );
      if (
        job &&
        (job.request.beta !== form.beta ||
          job.request.gauge_group !== form.gauge_group ||
          job.request.extents.join(",") !== form.extents.join(","))
      )
        setSelected(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };
  const measured = analysis?.potentials.find(
    (p) => p.separation === potentialR,
  );
  const measuredAvailable =
    analysis?.potentials.filter((p) => p.value !== null) ?? [];
  const predictIndex = prediction?.separations.indexOf(potentialR) ?? -1;
  const traces: Data[] = [];
  const reference = prediction
    ? analysis?.potentials.find((p) => p.separation === 1)
    : null;
  const referenceIndex = measuredAvailable.findIndex((p) => p.separation === 1);
  const measuredIndex = measuredAvailable.findIndex(
    (p) => p.separation === potentialR,
  );
  const mcValue = prediction
    ? measured?.value != null && reference?.value != null
      ? measured.value - reference.value
      : null
    : measured?.value;
  const mcError =
    prediction &&
    analysis?.covariance &&
    referenceIndex >= 0 &&
    measuredIndex >= 0
      ? Math.sqrt(
          Math.max(
            0,
            analysis.covariance[measuredIndex][measuredIndex] +
              analysis.covariance[referenceIndex][referenceIndex] -
              2 * analysis.covariance[measuredIndex][referenceIndex],
          ),
        )
      : measured?.measurement_error;
  if (measuredAvailable.length && (!prediction || reference?.value != null)) {
    const values = measuredAvailable.map(
      (p) => p.value! - (reference?.value ?? 0),
    );
    const errors = measuredAvailable.map((p, i) => {
      if (!reference || !analysis?.covariance || referenceIndex < 0)
        return p.measurement_error!;
      return Math.sqrt(
        Math.max(
          0,
          analysis.covariance[i][i] +
            analysis.covariance[referenceIndex][referenceIndex] -
            2 * analysis.covariance[i][referenceIndex],
        ),
      );
    });
    traces.push({
      x: measuredAvailable.map((p) => p.separation),
      y: values,
      error_y: {
        type: "data",
        array: errors,
        visible: true,
        color: "#75d9c7",
        thickness: 1.4,
      },
      mode: "markers",
      marker: { color: "#75d9c7", size: 8 },
      name: "Monte Carlo ± 1 SE",
      type: "scatter",
    });
  }
  if (prediction) {
    traces.push(
      {
        x: prediction.separations,
        y: prediction.mean.map((v, i) => v + 1.96 * prediction.model_std[i]),
        line: { width: 0 },
        showlegend: false,
        hoverinfo: "skip",
        type: "scatter",
      },
      {
        x: prediction.separations,
        y: prediction.mean.map((v, i) => v - 1.96 * prediction.model_std[i]),
        line: { width: 0 },
        fill: "tonexty",
        fillcolor: "rgba(184,162,227,.12)",
        name: "Approx. 95% model interval",
        hoverinfo: "skip",
        type: "scatter",
      },
      {
        x: prediction.separations,
        y: prediction.mean,
        line: { color: "#b8a2e3", width: 2 },
        name: "Learned prediction",
        type: "scatter",
      },
      {
        x: prediction.separations,
        y: prediction.formula,
        error_y: {
          type: "data",
          array: prediction.formula_error,
          visible: true,
          color: "#edb680",
          thickness: 1,
        },
        line: { color: "#edb680", dash: "dash", width: 2 },
        name: "Training-only Cornell",
        type: "scatter",
      },
    );
  } else if (analysis?.formula.values) {
    traces.push({
      x: analysis.formula.separations,
      y: analysis.formula.values,
      error_y: {
        type: "data",
        array: analysis.formula.errors ?? [],
        visible: true,
        color: "#edb680",
        thickness: 1,
      },
      line: { color: "#edb680", dash: "dash" },
      name: "Cornell fit to this run",
      type: "scatter",
    });
  }
  const mapValues = field?.values,
    mapErrors = field?.errors;
  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Lattice explorer home">
          <svg
            width="30"
            height="30"
            viewBox="0 0 30 30"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="m15 2 12 7v14l-12 7L3 23V9Zm0 0v14m12-7-12 7L3 9m12 7v14M3 23l12-7 12 7"
              stroke="currentColor"
              strokeWidth="1.3"
            />
          </svg>
          <span>
            LATTICE<span className="brand-sub">GAUGE THEORY EXPLORER</span>
          </span>
        </a>
        <div className="header-right">
          <span className="version">LOCAL RESEARCH WORKBENCH · v0.1</span>
          <span className={`status-light ${health ? "online" : ""}`}>
            {health ? "CPU simulator ready" : "Simulator unavailable"}
          </span>
        </div>
      </header>
      <aside className="sidebar">
        <div className="section-index">01 / CONFIGURATION</div>
        <h2>Define the experiment</h2>
        <p className="muted">
          Pure gauge theory. Periodic boundaries.
          <br />
          All quantities in lattice units.
        </p>
        <form onSubmit={submit}>
          <label className="field-label">Gauge group</label>
          <div className="segmented" role="group" aria-label="Gauge group">
            {(["u1", "su3"] as const).map((g) => (
              <button
                type="button"
                key={g}
                className={form.gauge_group === g ? "active" : ""}
                onClick={() => {
                  setForm((f) => ({
                    ...f,
                    gauge_group: g,
                    beta: g === "u1" ? 1.2 : 5.7,
                    proposal_scale: g === "u1" ? 0.7 : 0.5,
                  }));
                  setPrediction(null);
                }}
              >
                {g === "u1" ? "U(1)" : "SU(3)"}
                <span>
                  {g === "u1" ? "Compact Abelian" : "Pure non-Abelian"}
                </span>
              </button>
            ))}
          </div>
          <label className="field-label">
            Lattice extents <span>Nx × Ny × Nz × Nt</span>
          </label>
          <div className="extent-inputs">
            {form.extents.map((n, i) => (
              <label key={i}>
                <span>{["x", "y", "z", "t"][i]}</span>
                <input
                  aria-label={`Extent ${["x", "y", "z", "t"][i]}`}
                  type="number"
                  min="4"
                  max="32"
                  value={n}
                  onChange={(e) => {
                    const ext = [...form.extents] as Request["extents"];
                    ext[i] = +e.target.value;
                    update("extents", ext);
                  }}
                  required
                />
              </label>
            ))}
          </div>
          <div className="two-inputs">
            <label>
              Coupling β
              <input
                type="number"
                value={form.beta}
                min="0.01"
                max="20"
                step="0.01"
                onChange={(e) => update("beta", +e.target.value)}
                required
              />
            </label>
            <label>
              Separation r/a
              <input
                type="number"
                value={form.separation}
                min="1"
                max={form.max_r}
                onChange={(e) => update("separation", +e.target.value)}
                required
              />
            </label>
          </div>
          <details open>
            <summary>
              Sampling controls <span>MONTE CARLO</span>
            </summary>
            <div className="two-inputs">
              <label>
                Chains
                <input
                  type="number"
                  min="1"
                  max="16"
                  value={form.chains}
                  onChange={(e) => update("chains", +e.target.value)}
                />
              </label>
              <label>
                Samples / chain
                <input
                  type="number"
                  min="8"
                  max="100000"
                  value={form.measurements}
                  onChange={(e) => update("measurements", +e.target.value)}
                />
              </label>
              <label>
                Warm-up sweeps
                <input
                  type="number"
                  min="0"
                  value={form.warmup_sweeps}
                  onChange={(e) => update("warmup_sweeps", +e.target.value)}
                />
              </label>
              <label>
                Sweeps / sample
                <input
                  type="number"
                  min="1"
                  value={form.sweeps_between_measurements}
                  onChange={(e) =>
                    update("sweeps_between_measurements", +e.target.value)
                  }
                />
              </label>
            </div>
          </details>
          <details>
            <summary>Loops & analysis</summary>
            <div className="two-inputs">
              <label>
                Maximum r
                <input
                  type="number"
                  min="1"
                  max="16"
                  value={form.max_r}
                  onChange={(e) => update("max_r", +e.target.value)}
                />
              </label>
              <label>
                Maximum T
                <input
                  type="number"
                  min="2"
                  max="16"
                  value={form.max_t}
                  onChange={(e) => update("max_t", +e.target.value)}
                />
              </label>
              <label>
                Plateau first t
                <input
                  type="number"
                  min="1"
                  value={form.analysis.fit_min}
                  onChange={(e) =>
                    update("analysis", {
                      ...form.analysis,
                      fit_min: +e.target.value,
                    })
                  }
                />
              </label>
              <label>
                Plateau last t
                <input
                  type="number"
                  min="1"
                  value={form.analysis.fit_max}
                  onChange={(e) =>
                    update("analysis", {
                      ...form.analysis,
                      fit_max: +e.target.value,
                    })
                  }
                />
              </label>
              <label>
                Seed
                <input
                  type="number"
                  min="0"
                  value={form.seed}
                  onChange={(e) => update("seed", +e.target.value)}
                />
              </label>
              <label>
                Proposal angle
                <input
                  type="number"
                  min="0.01"
                  max="3.14"
                  step=".01"
                  value={form.proposal_scale}
                  onChange={(e) => update("proposal_scale", +e.target.value)}
                />
              </label>
              <label>
                Initial field
                <select
                  value={form.start}
                  onChange={(e) =>
                    update("start", e.target.value as Request["start"])
                  }
                >
                  <option value="cold">Cold / identity</option>
                  <option value="hot">Hot / Haar</option>
                </select>
              </label>
              <label>
                Field source T
                <input
                  type="number"
                  min="1"
                  value={form.field_t}
                  onChange={(e) => update("field_t", +e.target.value)}
                />
              </label>
              <label>
                Probe direction μ
                <select
                  value={form.probe[0]}
                  onChange={(e) =>
                    update("probe", [+e.target.value, form.probe[1]])
                  }
                >
                  {["x", "y", "z", "t"].map((d, i) => (
                    <option value={i} key={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Probe direction ν
                <select
                  value={form.probe[1]}
                  onChange={(e) =>
                    update("probe", [form.probe[0], +e.target.value])
                  }
                >
                  {["x", "y", "z", "t"].map((d, i) => (
                    <option value={i} key={d}>
                      {d}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.measure_field}
                onChange={(e) => update("measure_field", e.target.checked)}
              />
              Measure source-induced field map
            </label>
          </details>
          <button type="submit" className="primary" disabled={busy || !health}>
            <span>▶</span> Run simulation <span className="button-end">↗</span>
          </button>
          <p className="control-note">
            Runs locally on your CPU. Short runs may be statistically
            unresolved.
          </p>
          <label className="field-label">Trained model</label>
          <select
            value={model}
            onChange={(e) => {
              setModel(e.target.value);
              setPrediction(null);
            }}
            disabled={!models.length}
          >
            <option value="">
              {models.length
                ? "Select a model"
                : "No validated training corpus yet"}
            </option>
            {models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.gauge_group.toUpperCase()} · {m.id.slice(0, 8)} · {m.status}
              </option>
            ))}
          </select>
          {models
            .find((m) => m.id === model)
            ?.domain.map((d) => (
              <p className="control-note" key={d.extents.join(",")}>
                Supported: {d.extents.join(" × ")}; β {d.beta.join("…")}; r/a{" "}
                {d.separation.join("…")}
              </p>
            ))}
          <button
            type="button"
            className="secondary"
            onClick={() => void predict()}
            disabled={!model || busy}
          >
            Fast prediction <span>↗</span>
          </button>
        </form>
        <div className="sidebar-foot">
          <span className="tiny-dot" /> SERIAL CPU · DOUBLE PRECISION
        </div>
      </aside>
      <main>
        <div className="page-intro">
          <div>
            <div className="section-index">
              THE VACUUM, UNDER THE MICROSCOPE
            </div>
            <h1>Explore the force between quarks.</h1>
            <p>
              Measure a lattice. Compare the physics. Inspect the uncertainty.
            </p>
          </div>
          <span className="theory-tag">
            {view.gauge_group === "u1" ? "U(1)" : "SU(3)"} / WILSON ACTION
          </span>
        </div>
        {error && (
          <div className="error" role="alert">
            <strong>Unable to complete request.</strong> {error}
            <button onClick={() => setError("")} aria-label="Dismiss error">
              ×
            </button>
          </div>
        )}
        <div className="run-strip">
          <div>
            <span className={`run-state ${job?.state ?? ""}`}>
              {job?.state ?? (prediction ? "prediction" : "ready")}
            </span>
            <span className="mono">
              {selected ? selected.slice(0, 12) : "No simulation selected"}
            </span>
          </div>
          <span>
            {job
              ? `${job.request.extents.join(" × ")} · β ${job.request.beta} · seed ${job.request.seed}`
              : "Configure an experiment to begin"}
          </span>
          {job && (job.state === "running" || job.state === "queued") && (
            <>
              <progress
                value={job.progress}
                max="1"
                aria-label="Simulation progress"
              />
              <button
                className="text-button"
                onClick={() =>
                  void api(`/jobs/${job.id}/cancel`, { method: "POST" })
                    .then(refresh)
                    .catch((e) => setError(String(e)))
                }
              >
                Cancel job
              </button>
            </>
          )}
        </div>
        {job?.error && (
          <div className="error" role="status">
            {job.error}
          </div>
        )}
        <div className="potential-focus">
          <label>
            Read potential at r/a{" "}
            <select
              aria-label="Potential separation"
              value={potentialR}
              onChange={(e) => setPotentialR(+e.target.value)}
            >
              {Array.from(
                {
                  length: prediction
                    ? Math.max(...prediction.separations)
                    : view.max_r,
                },
                (_, i) => (
                  <option key={i} value={i + 1}>
                    {i + 1}
                  </option>
                ),
              )}
            </select>
          </label>
          <span>
            {prediction
              ? "V(r) − V(1); common reference for all three results"
              : "Source geometry and field maps retain the run’s requested separation."}
          </span>
        </div>
        <div className="result-cards">
          <article className="result-card measured">
            <div className="card-label">
              <span className="legend-dot" />
              MONTE CARLO <span className="card-tag">MEASURED</span>
            </div>
            <div className="result-value">
              {number(mcValue)}
              <small>{prediction ? "ΔaV" : "aV"}</small>
            </div>
            <p>
              {mcValue != null
                ? `± ${number(mcError)} measurement SE`
                : "Awaiting a resolved plateau estimate"}
            </p>
            <span className="result-state">
              {measured?.status ?? "No measurement"}
            </span>
          </article>
          <article className="result-card formula">
            <div className="card-label">
              <span className="legend-dot" />
              CORNELL FORMULA <span className="card-tag">FITTED</span>
            </div>
            <div className="result-value">
              {prediction && predictIndex >= 0
                ? number(prediction.formula[predictIndex])
                : analysis?.formula.values
                  ? number(
                      analysis.formula.values[
                        analysis.formula.separations!.indexOf(potentialR)
                      ],
                    )
                  : "—"}
              <small>{prediction ? "ΔaV" : "aV"}</small>
            </div>
            <p>
              {prediction
                ? `± ${number(prediction.formula_error[predictIndex])} baseline SE · training only`
                : (analysis?.formula.reason ??
                  "c − α/n + s n · a range-limited approximation")}
            </p>
            <span className="result-state">
              {prediction
                ? "Reference-subtracted"
                : (analysis?.formula.status ??
                  "Requires measured training data")}
            </span>
          </article>
          <article className="result-card learned">
            <div className="card-label">
              <span className="legend-dot" />
              LEARNED PREDICTION <span className="card-tag">GP RESIDUAL</span>
            </div>
            <div className="result-value">
              {prediction && predictIndex >= 0
                ? number(prediction.mean[predictIndex])
                : "—"}
              <small>ΔaV</small>
            </div>
            <p>
              {prediction && predictIndex >= 0
                ? `± ${number(1.96 * prediction.model_std[predictIndex])} approximate 95% interval`
                : "Train on validated runs to enable prediction"}
            </p>
            <span className="result-state">
              {prediction?.status ?? "No model prediction"}
            </span>
          </article>
        </div>
        <div className="workspace-grid">
          <section className="panel potential-panel">
            <div className="panel-heading">
              <div>
                <span className="section-index">02 / STATIC POTENTIAL</span>
                <h2>Measurement meets model</h2>
              </div>
              <span className="mini-label">
                {prediction ? "V(r) − V(1)" : "LATTICE UNITS"}
              </span>
            </div>
            {traces.length ? (
              <Plot
                data={traces}
                label="Static potential comparison with measurement errors and model intervals"
                layout={{
                  yaxis: {
                    title: {
                      text: prediction ? "aV(r) − aV(1)" : "Potential aV",
                    },
                    gridcolor: "#21303b",
                    zerolinecolor: "#334550",
                  },
                }}
              />
            ) : (
              <div className="empty-chart">
                <div className="chart-grid" />
                <div className="empty-message">
                  <span className="empty-symbol">⌁</span>
                  <h3>The potential starts with a measurement.</h3>
                  <p>
                    Submit a simulation or select a completed run.
                    <br />
                    Available results and their uncertainties will appear here.
                  </p>
                </div>
                <span className="axis-y">POTENTIAL aV</span>
                <span className="axis-x">SEPARATION r/a →</span>
              </div>
            )}
            <div className="panel-caption">
              Wilson-loop ratios → correlated plateau fit → static potential.
              Energy is an output.
            </div>
          </section>
          <section className="panel geometry-panel">
            <div className="panel-heading">
              <div>
                <span className="section-index">03 / SPATIAL GEOMETRY</span>
                <h2>Inside the lattice</h2>
              </div>
              <span className="mini-label">DRAG TO ROTATE</span>
            </div>
            <Lattice
              extents={view.extents}
              separation={view.separation}
              time={time}
              sourceT={view.field_t}
            />
            <div className="geometry-legend">
              <span>
                <i className="quark" />q
              </span>
              <span>
                <i className="antiquark" />
                q̄
              </span>
              <span>r/a = {view.separation}</span>
              <span>Geometry only</span>
            </div>
            <div className="time-control">
              <label htmlFor="time">
                Euclidean time slice <b>t/a = {time}</b>
              </label>
              <input
                id="time"
                type="range"
                min="0"
                max={view.extents[3] - 1}
                value={Math.min(time, view.extents[3] - 1)}
                onChange={(e) => setTime(+e.target.value)}
              />
            </div>
            <div className="panel-caption">
              Projected source loop spans t = 0…{view.field_t}. Links represent
              geometry; periodic edges wrap.
            </div>
          </section>
        </div>
        <div className="workspace-grid lower-grid">
          <section className="panel field-panel">
            <div className="panel-heading">
              <div>
                <span className="section-index">
                  04 / SOURCE-INDUCED RESPONSE
                </span>
                <h2>The field around the sources</h2>
              </div>
              <span className="pill">{field?.status ?? "NOT MEASURED"}</span>
            </div>
            <div className="field-toolbar">
              <span>
                XY PLANE · {["x", "y", "z", "t"][view.probe[0]]}
                {["x", "y", "z", "t"][view.probe[1]]} PROBE · T = {view.field_t}
              </span>
              <div className="small-segment">
                <button
                  className={mapMode === "value" ? "active" : ""}
                  onClick={() => setMapMode("value")}
                >
                  Response
                </button>
                <button
                  className={mapMode === "error" ? "active" : ""}
                  onClick={() => setMapMode("error")}
                >
                  Uncertainty
                </button>
              </div>
            </div>
            {mapValues && mapErrors ? (
              <Plot
                label={field!.label}
                data={[
                  {
                    type: "heatmap",
                    z: mapMode === "value" ? mapValues : mapErrors,
                    colorscale: mapMode === "value" ? "RdBu" : "Viridis",
                    zmin:
                      mapMode === "value"
                        ? -Math.max(...mapValues.flat().map(Math.abs))
                        : undefined,
                    zmax:
                      mapMode === "value"
                        ? Math.max(...mapValues.flat().map(Math.abs))
                        : undefined,
                    colorbar: {
                      title: { text: mapMode === "value" ? "Δs" : "SE" },
                      thickness: 10,
                    },
                    customdata: mapErrors,
                    hovertemplate:
                      "x/a=%{x}<br>y/a=%{y}<br>value=%{z:.5f}<br>SE=%{customdata:.5f}<extra></extra>",
                  },
                  {
                    type: "scatter",
                    x: [0, field!.separation],
                    y: [0, 0],
                    mode: "text+markers",
                    text: ["q", "q̄"],
                    textposition: "top center",
                    marker: {
                      color: ["#72d6c7", "#e7ac7d"],
                      size: 11,
                      line: { color: "#0c141b", width: 2 },
                    },
                    showlegend: false,
                  },
                ]}
                layout={{
                  xaxis: {
                    title: { text: "x/a relative to source (periodic)" },
                    dtick: 1,
                  },
                  yaxis: {
                    title: { text: "y/a (periodic)" },
                    scaleanchor: "x",
                    dtick: 1,
                  },
                }}
              />
            ) : (
              <div className="field-empty">
                <div className="crosshair">⊕</div>
                <h3>
                  {field?.status === "unavailable"
                    ? "The field measurement is unresolved."
                    : "A measured response, pixel by pixel."}
                </h3>
                <p>
                  {field?.reasons.at(-1) ??
                    "A joint Wilson-loop–plaquette measurement is needed. No field map is inferred from the potential."}
                </p>
              </div>
            )}
            <div className="panel-caption">
              Δs(x) = ⟨W s(x)⟩ / ⟨W⟩ − ⟨s(x)⟩ · Source-induced action-density
              response in lattice units.
            </div>
            {field && (
              <details className="explanations">
                <summary>Field measurement limits</summary>
                <p>{field.reasons.join(" · ")}</p>
                <p>
                  {field.temporal_stability}. Errors are pointwise; isolated
                  pixels are not a global significance test.
                </p>
              </details>
            )}
          </section>
          <section className="panel diagnostics-panel">
            <div className="panel-heading">
              <div>
                <span className="section-index">05 / STATISTICAL QUALITY</span>
                <h2>Trust, with diagnostics</h2>
              </div>
            </div>
            <dl className="diagnostics">
              <div>
                <dt>Effective samples</dt>
                <dd>{number(analysis?.diagnostics.effective_samples, 1)}</dd>
              </div>
              <div>
                <dt>
                  Autocorrelation τ<sub>int</sub>
                </dt>
                <dd>{number(analysis?.diagnostics.tau_int_measurements, 2)}</dd>
              </div>
              <div>
                <dt>Split R-hat</dt>
                <dd>{number(analysis?.diagnostics.split_rhat, 3)}</dd>
              </div>
              <div>
                <dt>Acceptance</dt>
                <dd>
                  {analysis
                    ? `${number(analysis.diagnostics.acceptance * 100, 1)}%`
                    : "—"}
                </dd>
              </div>
              <div>
                <dt>Block size / measurements</dt>
                <dd>{analysis?.diagnostics.block_size ?? "—"}</dd>
              </div>
              <div>
                <dt>Plateau window</dt>
                <dd>
                  {analysis
                    ? `${analysis.settings.fit_min}…${analysis.settings.fit_max}`
                    : "—"}
                </dd>
              </div>
              <div>
                <dt>Fit-window variation</dt>
                <dd>{number(measured?.fit_window_variation)}</dd>
              </div>
            </dl>
            <div className="diagnostic-note">
              <span>ⓘ</span>
              <p>
                {measured?.reasons.join(" · ") ||
                  analysis?.diagnostics.reasons.join(" · ") ||
                  "Four independent chains and sufficient blocked statistics are required. A completed job can still yield an unavailable or unvalidated potential."}
              </p>
            </div>
            {selected && job?.state === "completed" && (
              <a
                className="artifact-link"
                href={`/api/v1/jobs/${selected}/artifacts/manifest.json`}
                download
              >
                Download artifact manifest <span>↓</span>
              </a>
            )}
          </section>
        </div>
        {analysis && (
          <details className="panel fit-details">
            <summary>
              Effective masses, fits, and residuals{" "}
              <span>REVIEW THE PLATEAU</span>
            </summary>
            <Plot
              label="Effective Wilson-loop masses with uncertainties"
              data={analysis.potentials
                .filter((p) => p.effective_mass.length)
                .map((p, i) => ({
                  type: "scatter",
                  x: p.effective_mass.map((_, i) => i + 1),
                  y: p.effective_mass,
                  error_y: {
                    type: "data",
                    array: p.effective_mass_error.map((e) => e ?? 0),
                  },
                  name: `r/a=${p.separation}`,
                  mode: "lines+markers",
                  line: { color: ["#75d9c7", "#edb680", "#b8a2e3"][i % 3] },
                }))}
              layout={{
                xaxis: {
                  title: { text: "Temporal extent t/a" },
                  dtick: 1,
                  gridcolor: "#21303b",
                },
                yaxis: {
                  title: { text: "log[W(r,t)/W(r,t+1)]" },
                  gridcolor: "#21303b",
                },
              }}
            />
            <table>
              <thead>
                <tr>
                  <th>r/a</th>
                  <th>aV</th>
                  <th>SE</th>
                  <th>Window variation</th>
                  <th>χ²/dof</th>
                  <th>p-value</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {analysis.potentials.map((p) => (
                  <tr key={p.separation}>
                    <td>{p.separation}</td>
                    <td>{number(p.value)}</td>
                    <td>{number(p.measurement_error)}</td>
                    <td>{number(p.fit_window_variation)}</td>
                    <td>{number(p.chi2_dof, 2)}</td>
                    <td>{number(p.fit_pvalue, 3)}</td>
                    <td>{p.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {analysis.formula.values && (
              <Plot
                label="Residuals between Monte Carlo and Cornell approximation"
                data={[
                  {
                    type: "scatter",
                    x: measuredAvailable.map((p) => p.separation),
                    y: measuredAvailable.map(
                      (p, i) => p.value! - analysis.formula.values![i],
                    ),
                    mode: "markers",
                    error_y: {
                      type: "data",
                      array: measuredAvailable.map((p) => p.measurement_error!),
                    },
                    marker: { color: "#75d9c7" },
                    name: "Measurement − fitted Cornell",
                  },
                ]}
                layout={{
                  yaxis: {
                    title: { text: "Residual aV" },
                    gridcolor: "#21303b",
                  },
                }}
              />
            )}
          </details>
        )}
        {prediction && (
          <section className="panel model-evaluation">
            <div className="panel-heading">
              <div>
                <span className="section-index">HELD-OUT EVIDENCE</span>
                <h2>How well does the model predict?</h2>
              </div>
              <span className="pill">EXPERIMENTAL</span>
            </div>
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Split / points</th>
                    <th>Constant RMSE</th>
                    <th>Interpolation RMSE</th>
                    <th>Cornell RMSE</th>
                    <th>GP RMSE</th>
                    <th>Latent coverage</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(prediction.evaluation).map(([split, e]) => (
                    <tr key={split}>
                      <td>
                        {split.replace("_", " ")} / {e.parameter_points}
                      </td>
                      <td>{number(e.rmse.constant, 6)}</td>
                      <td>{number(e.rmse.interpolation, 6)}</td>
                      <td>{number(e.rmse.formula, 6)}</td>
                      <td>{number(e.rmse.residual_gp, 6)}</td>
                      <td>{number(100 * e.latent_interval_coverage, 1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="panel-caption">
              Intervals are approximate. Small holdout sets do not establish
              calibrated accuracy. Region holdouts audit extrapolation, which is
              disabled for predictions. Measurement uncertainty and fit-window
              variation remain separate.
            </p>
          </section>
        )}
        <section className="panel run-history">
          <div className="panel-heading">
            <div>
              <span className="section-index">EXPERIMENT NOTEBOOK</span>
              <h2>Recent runs</h2>
            </div>
            <button
              className="text-button"
              onClick={() => void refresh().catch((e) => setError(String(e)))}
            >
              Refresh ↻
            </button>
          </div>
          {jobs.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Run / seed</th>
                    <th>Group</th>
                    <th>Lattice</th>
                    <th>β</th>
                    <th>Samples</th>
                    <th>Status</th>
                    <th />
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((j) => (
                    <tr
                      key={j.id}
                      className={selected === j.id ? "selected" : ""}
                    >
                      <td className="mono">
                        {j.id.slice(0, 10)}{" "}
                        <span className="muted">/ {j.request.seed}</span>
                      </td>
                      <td>{j.request.gauge_group.toUpperCase()}</td>
                      <td>{j.request.extents.join(" × ")}</td>
                      <td>{j.request.beta}</td>
                      <td>
                        {j.request.chains} × {j.request.measurements}
                      </td>
                      <td>
                        <span className={`run-state ${j.state}`}>
                          {j.state}
                        </span>
                      </td>
                      <td>
                        <button
                          className="text-button"
                          onClick={() => {
                            setSelected(j.id);
                            setPotentialR(j.request.separation);
                            setForm(j.request);
                            setPrediction(null);
                          }}
                        >
                          Inspect ↗
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="no-runs">
              Your local experiment history will appear here. Each run preserves
              its configuration, raw measurements, and provenance.
            </p>
          )}
        </section>
        <section className="learning-notes">
          <details>
            <summary>What does the coupling mean?</summary>
            <p>
              β multiplies the plaquette terms in the Wilson action. For these
              conventions β = 1/g² for U(1) and β = 6/g² for SU(3). The Monte
              Carlo sampler draws fields according to exp(−S).
            </p>
          </details>
          <details>
            <summary>How does a Wilson loop measure a potential?</summary>
            <p>
              A rectangular loop follows a quark–antiquark pair across Euclidean
              time. At sufficiently large temporal extent, W(r,t) is dominated
              by exp(−V(r)t). Consecutive-loop ratios estimate aV; a stable
              plateau and reliable statistics are needed.
            </p>
          </details>
          <details>
            <summary>Why lattice units?</summary>
            <p>
              Separations are r/a and potentials are aV. The spacing is a unit
              convention here. Converting to physical distances or energies
              requires scale setting; this application does not predict
              continuum QCD.
            </p>
          </details>
        </section>
        <footer>
          <span>LATTICE / LOCAL RESEARCH WORKBENCH</span>
          <span>
            Pure gauge theory · CPU reference · Scientific validation in
            progress
          </span>
        </footer>
      </main>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
