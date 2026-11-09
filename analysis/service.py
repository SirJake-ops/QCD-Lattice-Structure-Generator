from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager
from pathlib import Path

import h5py
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from .artifacts import verify
from .contracts import (AnalyzedPotentials, FieldMap, Job, MeasurementHistory,
                        Prediction, PredictionRequest, SimulationRequest)
from .jobs import JobManager, ROOT


def create_app(data: Path | None = None, simulator: Path | None = None):
    data = data or Path(os.environ.get("QCD_DATA", ROOT / "results"))
    simulator = simulator or Path(os.environ.get("QCD_SIMULATOR", ROOT / "build/local-release/qcd_simulate"))
    manager = JobManager(data, simulator)

    @asynccontextmanager
    async def lifespan(app):
        manager.start()
        yield
        manager.close()

    app = FastAPI(title="Lattice explorer", version="0.1.0", lifespan=lifespan)
    app.state.manager = manager
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"])

    @app.middleware("http")
    async def local_origin(request, call_next):
        # No cross-site job submission from arbitrary webpages to the local service.
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            from urllib.parse import urlsplit
            parsed = urlsplit(origin)
            if parsed.hostname not in ("localhost", "127.0.0.1"):
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Local browser origin required"}, status_code=403)
        return await call_next(request)

    def get_job(run_id):
        try: return manager.get(run_id)
        except KeyError as e: raise HTTPException(404, str(e)) from e

    def completed_directory(run_id):
        job = get_job(run_id)
        if job.state != "completed": raise HTTPException(409, f"Run is {job.state}; results are incomplete")
        directory = manager.data / "runs" / job.id
        try: verify(directory)
        except (ValueError, OSError) as e: raise HTTPException(409, str(e)) from e
        return directory

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok", "schema_version": 1, "simulator_available": manager.simulator.is_file()}

    @app.post("/api/v1/jobs", response_model=Job, status_code=202)
    def submit(request: SimulationRequest):
        try: return manager.submit(request)
        except ValueError as e: raise HTTPException(422, str(e)) from e

    @app.get("/api/v1/jobs", response_model=list[Job])
    def list_jobs(): return manager.list()

    @app.get("/api/v1/jobs/{run_id}", response_model=Job)
    def inspect(run_id: str): return get_job(run_id)

    @app.post("/api/v1/jobs/{run_id}/cancel", response_model=Job)
    def cancel(run_id: str):
        get_job(run_id)
        return manager.cancel(run_id)

    @app.get("/api/v1/jobs/{run_id}/analysis", response_model=AnalyzedPotentials)
    def analysis(run_id: str):
        return json.loads((completed_directory(run_id) / "analysis.json").read_text())

    @app.get("/api/v1/jobs/{run_id}/field", response_model=FieldMap)
    def field(run_id: str):
        return json.loads((completed_directory(run_id) / "field.json").read_text())

    @app.get("/api/v1/jobs/{run_id}/history", response_model=MeasurementHistory)
    def history(run_id: str, limit: int = 1000):
        limit = max(1, min(limit, 5000))
        directory = completed_directory(run_id)
        with h5py.File(directory / "measurements.h5", "r") as h:
            return MeasurementHistory(source_run=run_id,
                loop_definitions=h["loop_definitions"][:].tolist(),
                **{key: h[key][:limit].tolist() for key in ("chain", "sweep", "plaquette", "acceptance", "loops")})

    @app.get("/api/v1/jobs/{run_id}/artifacts/{name}")
    def artifact(run_id: str, name: str):
        directory = completed_directory(run_id)
        manifest = json.loads((directory / "manifest.json").read_text())
        if name not in {*manifest["sha256"], "manifest.json"}: raise HTTPException(404)
        return FileResponse(directory / name, filename=name)

    @app.get("/api/v1/models")
    def models():
        return [json.loads(p.read_text()) for p in sorted((manager.data / "models").glob("*/manifest.json"))]

    @app.post("/api/v1/predictions", response_model=Prediction)
    def predict(request: PredictionRequest):
        from .learning import predict_model
        try: return predict_model(manager.data, request)
        except (ValueError, FileNotFoundError) as e: raise HTTPException(422, str(e)) from e

    dist = ROOT / "frontend/dist"
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="browser")
    else:
        @app.get("/")
        def missing_client():
            return {"detail": "Build the client: cd frontend && npm install && npm run build", "api_docs": "/docs"}
    return app
