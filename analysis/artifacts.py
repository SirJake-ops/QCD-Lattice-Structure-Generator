"""Immutable run bundles. Incomplete streams remain inspectable, never trainable."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path

import h5py
import numpy as np

from .contracts import SimulationRequest


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def provenance(root: Path, simulator: Path) -> dict:
    source = {}
    for directory in ("include", "src", "apps", "analysis", "configs"):
        for path in sorted((root / directory).rglob("*")):
            if path.is_file() and path.suffix in (".h", ".cpp", ".py", ".toml"):
                source[str(path.relative_to(root))] = checksum(path)
    revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True)
    return dict(revision=revision.stdout.strip() or "unknown", source_sha256=source,
                simulator_sha256=checksum(simulator), platform=platform.platform(),
                dependencies={p: version(p) for p in ("numpy", "scipy", "h5py", "scikit-learn", "fastapi")},
                action="S=beta sum_(x,mu<nu) (1-ReTr(U_p)/N)",
                precision="double", rng="mt19937_64; splitmix64(base_seed,chain)",
                units="lattice; spacing=1 is a convention, not scale setting")


def pack_stream(directory: Path, request: SimulationRequest, complete: bool):
    """Stream JSONL into chunked HDF5, retaining raw products and chain/sweep IDs."""
    count = 0
    trailer = False
    header = None
    with h5py.File(directory / "measurements.h5", "w") as h:
        h.attrs.update(schema_version=1, complete=False)
        datasets = {}
        with (directory / "measurements.jsonl").open() as stream:
            for line in stream:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    if complete:
                        raise ValueError("Malformed complete simulator stream")
                    break
                if row["type"] == "header":
                    if header is not None or row["schema_version"] != 1:
                        raise ValueError("Invalid measurement header")
                    header = row
                    h.create_dataset("loop_definitions", data=row["loops"])
                    h.attrs["simulator_header_json"] = json.dumps(row)
                    continue
                if row["type"] == "complete":
                    trailer = True
                    continue
                if row["type"] != "measurement" or trailer or header is None:
                    raise ValueError("Invalid measurement stream ordering")
                if not datasets:
                    for key, value in row.items():
                        if key == "type":
                            continue
                        a = np.asarray(value)
                        datasets[key] = h.create_dataset(key, shape=(0, *a.shape), maxshape=(None, *a.shape),
                            dtype="i8" if key in ("chain", "sweep") else "f8", chunks=True, compression="gzip")
                for key, dataset in datasets.items():
                    value = np.asarray(row[key])
                    if not np.all(np.isfinite(value)):
                        raise ValueError("Nonfinite measurement")
                    dataset.resize(count + 1, axis=0)
                    dataset[count] = value
                count += 1
        expected = request.chains * request.measurements
        if complete and (not trailer or count != expected):
            raise ValueError(f"Incomplete simulator stream: {count}/{expected}")
        if count:
            ids = h["chain"][:]
            sweeps = h["sweep"][:]
            for chain in range(request.chains):
                positions = ids == chain
                if complete and (positions.sum() != request.measurements or
                        not np.array_equal(sweeps[positions], request.warmup_sweeps +
                            np.arange(1, request.measurements + 1) * request.sweeps_between_measurements)):
                    raise ValueError("Chain/sweep identifiers do not match request")
        h.attrs["complete"] = complete
    return count


def seal(directory: Path, run_id: str, complete: bool):
    files = {p.name: checksum(p) for p in sorted(directory.iterdir())
             if p.is_file() and p.name != "manifest.json" and not p.name.endswith(".tmp")}
    write_json(directory / "manifest.json", dict(schema_version=1, source_run=run_id,
               complete=complete, sha256=files))


def verify(directory: Path, require_complete=True) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    if manifest["schema_version"] != 1 or (require_complete and not manifest["complete"]):
        raise ValueError("Incomplete or unsupported run artifact")
    for name, digest in manifest["sha256"].items():
        if Path(name).name != name or checksum(directory / name) != digest:
            raise ValueError(f"Artifact checksum mismatch: {name}")
    return manifest
