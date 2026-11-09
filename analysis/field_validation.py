"""Compare independent measured maps at different source temporal extents."""
from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from .artifacts import checksum, verify
from .contracts import FieldMap, SimulationRequest


def compare_fields(directories: list[Path]) -> dict:
    if len(directories) < 3:
        raise ValueError("Temporal stability requires at least three independent source-T runs")
    requests, maps, sources = [], [], []
    for directory in directories:
        verify(directory)
        requests.append(SimulationRequest.model_validate_json((directory / "request.json").read_text()))
        maps.append(FieldMap.model_validate_json((directory / "field.json").read_text()))
        sources.append(dict(run=directory.name, manifest_sha256=checksum(directory / "manifest.json")))
    key = lambda r: (r.gauge_group, r.beta, r.extents, r.separation, r.probe)
    if any(key(r) != key(requests[0]) for r in requests):
        raise ValueError("Field comparison requires matching group, coupling, volume, separation, and probe")
    if len({r.field_t for r in requests}) != len(requests) or len({r.seed for r in requests}) != len(requests):
        raise ValueError("Use distinct temporal extents and independent random seeds")
    if any(m.values is None or m.errors is None for m in maps):
        raise ValueError("Every compared map needs a supportable measured response and error")
    reference = max(range(len(requests)), key=lambda i: requests[i].field_t)
    comparisons = []
    for i, m in enumerate(maps):
        if i == reference: continue
        difference = np.array(m.values) - np.array(maps[reference].values)
        error = np.sqrt(np.array(m.errors)**2 + np.array(maps[reference].errors)**2)
        z = np.abs(difference) / np.maximum(error, 1e-15)
        # Conservative familywise normal threshold; includes repeated/symmetric
        # cells conservatively rather than pretending those cells are independent.
        from scipy.stats import norm
        threshold = float(norm.isf(.05 / (2 * difference.size * (len(maps) - 1))))
        comparisons.append(dict(source_T=requests[i].field_t, reference_T=requests[reference].field_t,
            max_standardized_difference=float(z.max()), familywise_threshold=threshold,
            status="unresolved temporal variation" if z.max() <= threshold else "temporal variation detected"))
    return dict(schema_version=1, source_runs=sources, comparisons=comparisons,
        status="compatible within errors" if all(c["status"] == "unresolved temporal variation" for c in comparisons) else "unstable",
        caveat="Normal approximation with Bonferroni bound; compatibility is not proof of ground-state isolation. Inspect maps, noise, and source-loop signal.")
