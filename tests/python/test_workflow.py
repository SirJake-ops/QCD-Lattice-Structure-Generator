import json
import time
from pathlib import Path

import h5py
import numpy as np
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from analysis.artifacts import verify
from analysis.contracts import SimulationRequest
from analysis.jobs import JobManager, ROOT
from analysis.learning import build_dataset
from analysis.service import create_app

SIMULATOR = ROOT / "build/local-release/qcd_simulate"


def finish(client, job_id, timeout=30):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        job = client.get(f"/api/v1/jobs/{job_id}").json()
        if job["state"] in ("completed", "failed", "cancelled"): return job
        time.sleep(.03)
    pytest.fail("Job did not reach a terminal state")


def small_request(**kwargs):
    return SimulationRequest(warmup_sweeps=10, measurements=16, chains=4,
                             **kwargs).model_dump(mode="json")


@pytest.mark.parametrize("overrides", [dict(extents=(2,4,4,8)),dict(max_r=3),dict(probe=(0,0)),dict(max_t=5),dict(analysis={"fit_min":4,"fit_max":3})])
def test_reject_invalid_scientific_geometry(overrides):
    with pytest.raises(ValidationError): SimulationRequest(**overrides)


@pytest.mark.skipif(not SIMULATOR.exists(), reason="Build C++ simulator first")
def test_submission_analysis_artifact_reproducibility_and_exclusion(tmp_path):
    app = create_app(tmp_path, SIMULATOR)
    with TestClient(app) as client:
        assert client.get('/api/v1/health').json()["simulator_available"]
        assert client.post('/api/v1/jobs', json=small_request(), headers={"Origin":"https://example.org"}).status_code == 403
        assert client.post('/api/v1/jobs', json={"beta": -1}).status_code == 422
        submitted = client.post('/api/v1/jobs', json=small_request())
        assert submitted.status_code == 202
        job_id = submitted.json()["id"]
        job = finish(client, job_id)
        assert job["state"] == "completed", job
        result = client.get(f'/api/v1/jobs/{job_id}/analysis')
        assert result.status_code == 200
        assert result.json()["source_runs"] == [job_id]
        assert all(p["status"] != "validated" for p in result.json()["potentials"])
        field = client.get(f'/api/v1/jobs/{job_id}/field').json()
        assert field["status"] in ("unresolved","unavailable")
        assert field["probe"] == [0,3]
        history = client.get(f'/api/v1/jobs/{job_id}/history?limit=4').json()
        assert len(history["chain"]) == 4
        directory = tmp_path / 'runs' / job_id
        assert verify(directory)["complete"]
        assert client.get(f'/api/v1/jobs/{job_id}/artifacts/measurements.h5').status_code == 200
        assert client.get(f'/api/v1/jobs/{job_id}/artifacts/not-a-file').status_code == 404
        duplicate = client.post('/api/v1/jobs', json=small_request()).json()
        assert finish(client, duplicate["id"])["state"] == "completed"
        with h5py.File(directory/'measurements.h5') as a, h5py.File(tmp_path/'runs'/duplicate['id']/'measurements.h5') as b:
            np.testing.assert_array_equal(a['loops'][:],b['loops'][:])
            np.testing.assert_array_equal(a['ws'][:],b['ws'][:])
        with pytest.raises(ValueError, match="No validated|validated parameter"):
            build_dataset(tmp_path, 'u1')
        (directory/'analysis.json').write_text('{}')
        assert client.get(f'/api/v1/jobs/{job_id}/analysis').status_code == 409


@pytest.mark.skipif(not SIMULATOR.exists(), reason="Build C++ simulator first")
def test_running_and_queued_cancellation_preserve_incomplete_outputs(tmp_path):
    app=create_app(tmp_path,SIMULATOR)
    with TestClient(app) as client:
        long=small_request();long['warmup_sweeps']=100000
        a=client.post('/api/v1/jobs',json=long).json()
        b=client.post('/api/v1/jobs',json=small_request()).json()
        assert client.post(f'/api/v1/jobs/{b["id"]}/cancel').json()['state']=='cancelled'
        end=time.monotonic()+5
        while client.get(f'/api/v1/jobs/{a["id"]}').json()['state']=='queued' and time.monotonic()<end: time.sleep(.02)
        assert client.post(f'/api/v1/jobs/{a["id"]}/cancel').json()['state']=='cancelled'
        assert client.get(f'/api/v1/jobs/{a["id"]}/analysis').status_code==409
        end=time.monotonic()+5
        manager=app.state.manager
        while manager.active and time.monotonic()<end: time.sleep(.02)
        for job in (a,b):
            assert not json.loads((tmp_path/'runs'/job['id']/'manifest.json').read_text())['complete']


def test_failure_recovery_and_worker_lock(tmp_path):
    manager=JobManager(tmp_path,Path('/bin/false'))
    job=manager.submit(SimulationRequest())
    manager._update(job.id,state='running')
    manager.start()
    try:
        recovered=manager.get(job.id)
        assert recovered.state=='failed' and 'interrupted' in recovered.error
        other=JobManager(tmp_path,Path('/bin/false'))
        with pytest.raises(RuntimeError,match='Another worker'): other.start()
        new=manager.submit(SimulationRequest())
        end=time.monotonic()+5
        while manager.get(new.id).state in ('queued','running') and time.monotonic()<end:time.sleep(.03)
        assert manager.get(new.id).state=='failed'
        assert not json.loads((tmp_path/'runs'/new.id/'manifest.json').read_text())['complete']
    finally:manager.close()
