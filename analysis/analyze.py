from __future__ import annotations

import json
from pathlib import Path
import h5py
import numpy as np

from .contracts import AnalysisSettings, AnalyzedPotentials, FieldMap, Potential, SimulationRequest
from .statistics import (covariance, integrated_autocorrelation, jackknife_means, make_blocks,
                         plateau, response, split_rhat)


def cornell_fit(n: np.ndarray, y: np.ndarray, cov: np.ndarray) -> dict:
    if len(n) < 3:
        return dict(status="unavailable", reason="Cornell fit requires at least three available separations")
    design = np.column_stack((np.ones(len(n)), -1. / n, n))
    try:
        if np.linalg.matrix_rank(cov) < len(n) or np.linalg.cond(cov) > 1e10:
            raise ValueError("Singular or ill-conditioned potential covariance")
        inv = np.linalg.inv(cov)
        coeff_cov = np.linalg.inv(design.T @ inv @ design)
        coeff = coeff_cov @ design.T @ inv @ y
        fitted = design @ coeff
        return dict(status="fitted approximation", coefficients=dict(zip(("c", "alpha", "s"), coeff.tolist())),
                    covariance=coeff_cov.tolist(), separations=n.tolist(), values=fitted.tolist(),
                    errors=np.sqrt(np.diag(design @ coeff_cov @ design.T)).tolist(),
                    range=[int(min(n)), int(max(n))], source="this run; not an out-of-sample prediction",
                    chi2_dof=float((y - fitted) @ inv @ (y - fitted) / max(1, len(n) - 3)))
    except (ValueError, np.linalg.LinAlgError) as e:
        return dict(status="unavailable", reason=str(e))


def analyze_run(directory: Path, settings: AnalysisSettings | None = None) -> tuple[AnalyzedPotentials, FieldMap]:
    request = SimulationRequest.model_validate_json((directory / "request.json").read_text())
    settings = settings or request.analysis
    run_id = directory.name
    with h5py.File(directory / "measurements.h5", "r") as h:
        if not h.attrs["complete"]:
            raise ValueError("Incomplete measurements cannot be analyzed as a completed run")
        chain_ids = h["chain"][:]
        columns = [h["plaquette"][:][:, None], h["loops"][:]]
        if request.measure_field:
            columns += [h["w"][:][:, None], h["s"][:], h["ws"][:]]
        raw = np.concatenate(columns, axis=1)
        chains = np.stack([raw[chain_ids == c] for c in range(request.chains)])
        acceptance = float(h["acceptance"][:].mean())
    # Slowest measured channel, including source-loop and probe correlations.
    tau = max(integrated_autocorrelation(chains[c, :, j]) for c in range(request.chains)
              for j in range(chains.shape[-1]))
    recommended = max(1, int(np.ceil(2 * tau)))
    # Bound the quadratic nested jackknife cost; merge adjacent samples only
    # within each chain. Larger blocks remove at least the estimated correlation.
    block_size = settings.block_size or max(recommended, int(np.ceil(request.measurements / max(2, 512 // request.chains))))
    neff = float(request.chains * request.measurements / (2 * tau))
    rhats = [split_rhat(chains[:, :, j]) for j in range(1 + request.max_r * request.max_t)]
    rhat = max(rhats)
    reasons = []
    if request.chains < 4: reasons.append("At least four independent chains required")
    if rhat > 1.1: reasons.append("Split R-hat exceeds 1.1; equilibration or chain agreement unresolved")
    if neff < settings.min_effective_samples: reasons.append("Insufficient effective statistics")
    if block_size < recommended: reasons.append("Requested blocks shorter than estimated correlation length")
    if request.warmup_sweeps < 10: reasons.append("Warm-up too short for validation")
    if request.gauge_group == "su3": reasons.append("Matched independent SU(3) benchmark has not been supplied")
    diagnostics = dict(tau_int_measurements=tau, effective_samples=neff,
        block_size=block_size, recommended_block_size=recommended,
        split_rhat=rhat if np.isfinite(rhat) else None,
        acceptance=acceptance, plaquette=float(chains[:, :, 0].mean()),
        measurements_per_chain=request.measurements, chains=request.chains,
        discarded_tail_per_chain=request.measurements % block_size,
        caveat="Autocorrelation and convergence estimates are themselves uncertain for short histories",
        reasons=reasons.copy())
    blocks = None
    try:
        blocks = make_blocks(chains, block_size)
        if len(blocks) < settings.min_blocks: raise ValueError("Insufficient complete blocks")
        if len(blocks) > 512: raise ValueError("More than 512 blocks: increase block_size for nested resampling")
        if block_size < recommended: raise ValueError("Blocks shorter than correlation length")
        diagnostics["blocks"] = len(blocks)
    except ValueError as e:
        blocks = None
        reasons.append(str(e))
    potentials, replicas, available = [], [], []
    for separation in range(1, request.max_r + 1):
        local_reasons = reasons.copy()
        try:
            if blocks is None: raise ValueError("Insufficient blocked statistics for potential extraction")
            offset = 1 + (separation - 1) * request.max_t
            loop_blocks = blocks[:, offset:offset + request.max_t]
            fit = plateau(loop_blocks, settings.fit_min, settings.fit_max)
            # Record window variation separately from the measurement uncertainty.
            alt_min = settings.fit_min - 1 if settings.fit_min > 1 else settings.fit_min + 1
            alt_max = settings.fit_max
            if alt_max - alt_min < 1:
                raise ValueError("No alternative plateau window; measure more consecutive temporal extents")
            alternative = plateau(loop_blocks, alt_min, alt_max)
            variation = abs(fit["value"] - alternative["value"])
            if variation > 2 * max(fit["error"], alternative["error"]):
                local_reasons.append("Plateau fit is unstable under fit-window variation")
            if fit["pvalue"] < .01: local_reasons.append("Correlated constant plateau fit rejected (p<0.01)")
            potentials.append(Potential(separation=separation, value=fit["value"],
                measurement_error=fit["error"], fit_window_variation=variation,
                status="unvalidated" if local_reasons else "validated", reasons=local_reasons,
                effective_mass=fit["effective_mass"], effective_mass_error=fit["effective_mass_error"],
                chi2_dof=fit["chi2_dof"], fit_pvalue=fit["pvalue"]))
            available.append(separation)
            replicas.append(fit["replicas"])
        except (ValueError, np.linalg.LinAlgError, FloatingPointError) as e:
            potentials.append(Potential(separation=separation, status="unavailable", reasons=local_reasons + [str(e)]))
    cov = covariance(np.array(replicas).T) if replicas else None
    formula = cornell_fit(np.asarray(available), np.asarray([p.value for p in potentials if p.value is not None]), cov) if replicas else dict(status="unavailable", reason="No available potentials")
    result = AnalyzedPotentials(source_runs=[run_id], settings=settings, potentials=potentials,
        covariance=cov.tolist() if cov is not None else None, diagnostics=diagnostics, formula=formula)
    map_reasons = reasons.copy()
    values = errors = None
    status = "unavailable"
    try:
        if not request.measure_field: raise ValueError("Field-map measurements were disabled")
        if blocks is None: raise ValueError("Insufficient blocked statistics for field map")
        offset = 1 + request.max_r * request.max_t
        cells = request.extents[0] * request.extents[1]
        v, e = response(blocks[:, offset:], cells)
        values = v.reshape(request.extents[1], request.extents[0]).tolist()
        errors = e.reshape(request.extents[1], request.extents[0]).tolist()
        # Resolution is descriptive, not a multiple-comparison discovery claim.
        status = "resolved" if np.max(np.abs(v) / np.maximum(e, 1e-15)) >= 3 and not reasons else "unresolved"
        if status == "unresolved": map_reasons.append("No validated resolved response; inspect pointwise uncertainties")
        map_reasons.append("Temporal stability remains to be checked; significance is pointwise")
    except ValueError as e:
        map_reasons.append(str(e))
    field = FieldMap(source_runs=[run_id], status=status, reasons=map_reasons,
        separation=request.separation, temporal_extent=request.field_t, probe=request.probe,
        shape=(request.extents[1], request.extents[0]), values=values, errors=errors, analysis_settings=settings)
    return result, field
