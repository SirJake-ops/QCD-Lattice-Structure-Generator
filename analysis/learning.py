"""Frozen parameter-point splits, training-only Cornell fits and residual GP.

No model is shipped with invented accuracy. Models are built only from complete,
validated run bundles and remain experimental until held-out evidence supports use.
"""
from __future__ import annotations

import json
import re
import sqlite3
import uuid
import warnings
from importlib.metadata import version
from pathlib import Path

import numpy as np
from scipy.interpolate import interp1d
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, RBF
from sklearn.preprocessing import StandardScaler

from .artifacts import checksum, verify, write_json
from .contracts import Contract, Prediction, PredictionRequest
from pydantic import Field


class DatasetManifest(Contract):
    schema_version: int = 1
    id: str
    gauge_group: str
    source_runs: list[str]
    points: list[dict]
    excluded_runs: list[dict]
    convention: str = "V(r)-V(1), lattice units"
    split_policy: str = "Per volume: middle beta is interpolation test; highest beta is region test; all other betas train"
    sha256: dict[str, str] = Field(default_factory=dict)


def build_dataset(data: Path, group: str) -> Path:
    if group not in ("u1", "su3"): raise ValueError("Unsupported gauge group")
    with sqlite3.connect(data / "jobs.sqlite3") as db:
        rows = db.execute("SELECT id,state FROM jobs ORDER BY created").fetchall()
    points, excluded, seeds = {}, [], set()
    for run_id, state in rows:
        directory = data / "runs" / run_id
        req = json.loads((directory / "request.json").read_text())
        if req["gauge_group"] != group: continue
        if state != "completed":
            excluded.append(dict(run=run_id, reason="Incomplete job: " + state)); continue
        try:
            verify(directory)
            result = json.loads((directory / "analysis.json").read_text())
            potentials = result["potentials"]
            if len(potentials) < 3 or any(p["status"] != "validated" for p in potentials):
                raise ValueError("At least three validated separations required")
            if req["chains"] < 4: raise ValueError("At least four independent chains required")
            key = (req["beta"], tuple(req["extents"]))
            seed_key = (*key, req["seed"])
            if seed_key in seeds: raise ValueError("Duplicate random streams at parameter point")
            seeds.add(seed_key)
            cov = np.asarray(result["covariance"], float)
            n = np.array([p["separation"] for p in potentials])
            if n[0] != 1 or not np.array_equal(n, np.arange(1, len(n) + 1)):
                raise ValueError("Consecutive separations beginning at reference r=1 required")
            transform = np.column_stack((-np.ones(len(n) - 1), np.eye(len(n) - 1)))
            y = transform @ np.array([p["value"] for p in potentials])
            c = transform @ cov @ transform.T
            if np.linalg.matrix_rank(c) != len(c): raise ValueError("Singular reference-subtracted covariance")
            record = dict(run=run_id, beta=req["beta"], extents=req["extents"], separations=n[1:].tolist(),
                values=y.tolist(), covariance=c.tolist(), seed=req["seed"], analysis=result["settings"],
                artifact_manifest_sha256=checksum(directory / "manifest.json"))
            points.setdefault(key, []).append(record)
        except (ValueError, OSError, KeyError) as e:
            excluded.append(dict(run=run_id, reason=str(e)))
    combined = []
    for (beta, extents), records in sorted(points.items()):
        n = min(len(r["separations"]) for r in records)
        precisions = [np.linalg.inv(np.array(r["covariance"])[:n, :n]) for r in records]
        cov = np.linalg.inv(sum(precisions))
        mean = cov @ sum(p @ np.array(r["values"])[:n] for p, r in zip(precisions, records))
        combined.append(dict(beta=beta, extents=list(extents), separations=list(range(2, n + 2)),
            values=mean.tolist(), covariance=cov.tolist(), runs=[r["run"] for r in records], records=records))
    volumes = sorted({tuple(p["extents"]) for p in combined})
    for extent in volumes:
        matches = [p for p in combined if tuple(p["extents"]) == extent]
        if len(matches) < 6:
            raise ValueError(f"Volume {extent} has {len(matches)} validated parameter points; need at least six. "
                             f"{len(excluded)} runs were excluded; run longer chains or inspect diagnostics")
        for i, point in enumerate(matches):
            point["split"] = "region_test" if i == len(matches) - 1 else "interpolation_test" if i == len(matches) // 2 else "train"
    if not combined: raise ValueError("No validated complete parameter points; no dataset was created")
    dataset_id = uuid.uuid4().hex
    directory = data / "datasets" / dataset_id
    directory.mkdir(parents=True)
    sources = [run for p in combined for run in p["runs"]]
    manifest = DatasetManifest(id=dataset_id, gauge_group=group, source_runs=sources, points=combined, excluded_runs=excluded)
    write_json(directory / "manifest.json", manifest.model_dump(mode="json"))
    return directory


def _fit_coeff(point):
    n = np.array(point["separations"], float)
    design = np.column_stack((1. - 1. / n, n - 1.))
    precision = np.linalg.inv(np.array(point["covariance"]))
    covariance = np.linalg.inv(design.T @ precision @ design)
    coefficients = covariance @ design.T @ precision @ point["values"]
    return coefficients, covariance


def _baseline(point, baselines):
    rows = [b for b in baselines if b["extents"] == point["extents"]]
    rows.sort(key=lambda b: b["beta"])
    betas = np.array([b["beta"] for b in rows])
    beta = point["beta"]
    # Extrapolation is for the held-out region report only; public predictions reject it.
    i = int(np.clip(np.searchsorted(betas, beta) - 1, 0, len(rows) - 2))
    weight = (beta - betas[i]) / (betas[i + 1] - betas[i])
    coeff = (1 - weight) * np.array(rows[i]["coeff"]) + weight * np.array(rows[i + 1]["coeff"])
    cov = (1 - weight)**2 * np.array(rows[i]["cov"]) + weight**2 * np.array(rows[i + 1]["cov"])
    n = np.array(point["separations"], float)
    design = np.column_stack((1. - 1. / n, n - 1.))
    return design @ coeff, np.maximum(0, np.diag(design @ cov @ design.T))


def _features(point):
    return np.array([[point["beta"], *point["extents"], n] for n in point["separations"]], float)


def train_model(data: Path, dataset_directory: Path) -> Path:
    manifest = DatasetManifest.model_validate_json((dataset_directory / "manifest.json").read_text())
    # Recheck every frozen source: later tampering must never silently enter training.
    for point in manifest.points:
        for record in point["records"]:
            directory = data / "runs" / record["run"]
            verify(directory)
            if checksum(directory / "manifest.json") != record["artifact_manifest_sha256"]:
                raise ValueError("Frozen source manifest changed")
    training = [p for p in manifest.points if p["split"] == "train"]
    if not training or not any(p["split"] == "interpolation_test" for p in manifest.points):
        raise ValueError("Frozen point-level training and test splits required")
    baselines = []
    for point in training:
        coeff, cov = _fit_coeff(point)
        baselines.append(dict(beta=point["beta"], extents=point["extents"], coeff=coeff.tolist(), cov=cov.tolist()))
    x = np.concatenate([_features(p) for p in training])
    residual = np.concatenate([np.array(p["values"]) - _baseline(p, baselines)[0] for p in training])
    noise = np.concatenate([np.diag(p["covariance"]) for p in training])
    scaler = StandardScaler().fit(x)
    # Coupling and discrete geometry are the only features; no seed, chain,
    # sweep, fit quality, or held-out measurement enters optimization.
    gp = GaussianProcessRegressor(kernel=ConstantKernel(1., (1e-6, 10.)) * RBF(np.ones(x.shape[1]), (1e-2, 100.)),
        alpha=np.maximum(noise, 1e-12), normalize_y=False, random_state=19, n_restarts_optimizer=1)
    with warnings.catch_warnings(record=True) as optimizer_warnings:
        warnings.simplefilter("always")
        gp.fit(scaler.transform(x), residual)
    reports = {}
    for split in ("interpolation_test", "region_test"):
        errors = {key: [] for key in ("constant", "interpolation", "formula", "residual_gp")}
        coverage, predictive_coverage = [], []
        for point in [p for p in manifest.points if p["split"] == split]:
            formula, fvar = _baseline(point, baselines)
            correction, sigma = gp.predict(scaler.transform(_features(point)), return_std=True)
            predicted = formula + correction
            same_volume = sorted([p for p in training if p["extents"] == point["extents"]], key=lambda p: p["beta"])
            interpolated = []
            constant = []
            for n in point["separations"]:
                selected = [p for p in same_volume if n in p["separations"]]
                if len(selected) < 2: raise ValueError("Insufficient shared separation support")
                ys = [p["values"][p["separations"].index(n)] for p in selected]
                interpolated.append(float(interp1d([p["beta"] for p in selected], ys, fill_value="extrapolate")(point["beta"])))
                constant.append(float(np.mean(ys)))
            truth = np.array(point["values"])
            for key, estimate in zip(errors, (constant, interpolated, formula, predicted)):
                errors[key].extend((np.array(estimate) - truth).tolist())
            std = np.sqrt(sigma**2 + fvar)
            coverage.extend((np.abs(predicted - truth) <= 1.96 * std).tolist())
            predictive_coverage.extend((np.abs(predicted - truth) <= 1.96 * np.sqrt(std**2 + np.diag(point["covariance"]))).tolist())
        reports[split] = dict(rmse={k: float(np.sqrt(np.mean(np.square(v)))) for k, v in errors.items()},
            latent_interval_coverage=float(np.mean(coverage)), observation_interval_coverage=float(np.mean(predictive_coverage)),
            observations=len(coverage), parameter_points=sum(p["split"] == split for p in manifest.points))
    model_id = uuid.uuid4().hex
    directory = data / "models" / model_id
    directory.mkdir(parents=True)
    np.savez_compressed(directory / "gp.npz", x=x, residual=residual, noise=noise,
                        center=scaler.mean_, scale=scaler.scale_)
    domain = []
    for extent in sorted({tuple(p["extents"]) for p in training}):
        selected = [p for p in training if tuple(p["extents"]) == extent]
        domain.append(dict(extents=list(extent), beta=[min(p["beta"] for p in selected), max(p["beta"] for p in selected)],
                           separation=[1, min(max(p["separations"]) for p in selected)]))
    # Statistical observations within one point aren't independent coverage trials.
    evidence = reports["interpolation_test"]
    validated = (evidence["parameter_points"] >= 30 and evidence["latent_interval_coverage"] >= .9 and
                 evidence["rmse"]["residual_gp"] < min(evidence["rmse"][k] for k in ("constant", "formula", "interpolation")))
    metadata = dict(schema_version=1, id=model_id, gauge_group=manifest.gauge_group,
        status="evaluated" if validated else "experimental; held-out evidence insufficient to advertise accuracy",
        source_runs=manifest.source_runs, training_runs=[r for p in training for r in p["runs"]],
        dataset_id=manifest.id, dataset_manifest_sha256=checksum(dataset_directory / "manifest.json"),
        training_code_sha256=checksum(Path(__file__)), random_state=19,
        dependencies={p: version(p) for p in ("numpy", "scipy", "scikit-learn")},
        optimization_warnings=[str(w.message) for w in optimizer_warnings],
        domain=domain, baselines=baselines, evaluation=reports, kernel=dict(
            amplitude=float(gp.kernel_.k1.constant_value), length_scale=gp.kernel_.k2.length_scale.tolist()),
        convention="V(r)-V(1), in lattice units", gp_sha256=checksum(directory / "gp.npz"),
        uncertainty="Conditional residual GP plus interpolated Cornell coefficient variance in quadrature; calibration evaluated on held-out points",
        limitations=["GP uses diagonal measurement noise; reference subtraction induces correlations retained in dataset",
            "Baseline and residual uncertainties are dependent; quadrature intervals are approximate",
            "No continuous interpolation across volumes; only listed extents are supported",
            "Region test is extrapolation for auditing only; API rejects out-of-domain predictions"])
    write_json(directory / "manifest.json", metadata)
    return directory


def predict_model(data: Path, request: PredictionRequest) -> Prediction:
    if not re.fullmatch(r"[a-f0-9]{32}", request.model_id): raise ValueError("Invalid model ID")
    directory = data / "models" / request.model_id
    m = json.loads((directory / "manifest.json").read_text())
    if m["gauge_group"] != request.gauge_group: raise ValueError("Gauge-group mismatch")
    domains = [d for d in m["domain"] if d["extents"] == list(request.extents)]
    if not domains: raise ValueError("Unsupported volume; choose an explicitly supported extent tuple")
    d = domains[0]
    if not d["beta"][0] <= request.beta <= d["beta"][1] or any(n < d["separation"][0] or n > d["separation"][1] for n in request.separations):
        raise ValueError("Unsupported coupling or separation; extrapolation is disabled")
    if checksum(directory / "gp.npz") != m["gp_sha256"]: raise ValueError("Model checksum mismatch")
    p = dict(beta=request.beta, extents=list(request.extents), separations=request.separations)
    formula, fvar = _baseline(p, m["baselines"])
    with np.load(directory / "gp.npz", allow_pickle=False) as z:
        kernel = ConstantKernel(m["kernel"]["amplitude"], "fixed") * RBF(m["kernel"]["length_scale"], "fixed")
        gp = GaussianProcessRegressor(kernel=kernel, alpha=np.maximum(z["noise"], 1e-12), optimizer=None)
        gp.fit((z["x"] - z["center"]) / z["scale"], z["residual"])
        correction, sigma = gp.predict((_features(p) - z["center"]) / z["scale"], return_std=True)
    mean = formula + correction
    std = np.sqrt(sigma**2 + fvar)
    for i, n in enumerate(request.separations):
        if n == 1: formula[i] = mean[i] = std[i] = fvar[i] = 0.
    return Prediction(model_id=request.model_id, source_runs=m["source_runs"], status=m["status"],
        separations=request.separations, formula=formula.tolist(), formula_error=np.sqrt(fvar).tolist(),
        mean=mean.tolist(), model_std=std.tolist(), interval_95=np.column_stack((mean - 1.96 * std, mean + 1.96 * std)).tolist(),
        evaluation=m["evaluation"])
