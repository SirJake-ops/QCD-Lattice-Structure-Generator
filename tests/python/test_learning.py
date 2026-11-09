"""Synthetic fixtures test data separation; they are never scientific run artifacts."""
import json
from pathlib import Path

import numpy as np
import pytest

from analysis.artifacts import seal, write_json
from analysis.contracts import PredictionRequest, SimulationRequest
from analysis.jobs import JobManager
from analysis.learning import build_dataset, predict_model, train_model


def synthetic_test_catalogue(path: Path):
    manager = JobManager(path, Path('/bin/true'))
    for i, beta in enumerate([1., 1.1, 1.2, 1.3, 1.4, 1.5]):
        request = SimulationRequest(beta=beta, extents=(8,8,8,12), max_r=4, max_t=6, seed=91+i)
        job=manager.submit(request)
        directory=path/'runs'/job.id
        n=np.arange(1.,5.)
        values=.7-(.2+.05*beta)/n+(.13+.02*beta)*n+.003*np.sin(8*beta)*np.sqrt(n)
        write_json(directory/'analysis.json',dict(potentials=[dict(separation=int(r),value=float(y),status='validated')
            for r,y in zip(n,values)], covariance=(np.eye(4)*1e-5+np.ones((4,4))*2e-6).tolist(),settings=request.analysis.model_dump()))
        write_json(directory/'SYNTHETIC_TEST_FIXTURE.json',{'purpose':'Software tests only. Not simulator measurements.'})
        seal(directory,job.id,True)
        manager._update(job.id,state='completed')
    return manager


def test_frozen_parameter_splits_and_supported_predictions(tmp_path):
    synthetic_test_catalogue(tmp_path)
    dataset=build_dataset(tmp_path,'u1')
    frozen=json.loads((dataset/'manifest.json').read_text())
    assert [p['split'] for p in frozen['points']]==['train','train','train','interpolation_test','train','region_test']
    model=train_model(tmp_path,dataset)
    metadata=json.loads((model/'manifest.json').read_text())
    train_runs={r for p in frozen['points'] if p['split']=='train' for r in p['runs']}
    test_runs={r for p in frozen['points'] if p['split']!='train' for r in p['runs']}
    assert train_runs.isdisjoint(test_runs)
    assert set(metadata['training_runs'])==train_runs
    assert all(b['beta'] not in (1.3,1.5) for b in metadata['baselines'])
    req=PredictionRequest(model_id=model.name,gauge_group='u1',beta=1.3,extents=(8,8,8,12),separations=[1,2,3,4])
    prediction=predict_model(tmp_path,req)
    assert prediction.mean[0]==prediction.model_std[0]==0
    assert all(s>=0 for s in prediction.model_std)
    assert 'experimental' in prediction.status
    assert set(prediction.evaluation['interpolation_test']['rmse'])=={'constant','interpolation','formula','residual_gp'}
    for change in [dict(beta=1.5),dict(extents=(6,6,6,12)),dict(gauge_group='su3'),dict(separations=[5]),dict(model_id='../outside')]:
        with pytest.raises(ValueError): predict_model(tmp_path,req.model_copy(update=change))
    # Perturb only held-out values: the learned GP and baseline must remain unchanged.
    for point in frozen['points']:
        if point['split']!='train': point['values']=[v+100 for v in point['values']]
    write_json(dataset/'manifest.json',frozen)
    other=train_model(tmp_path,dataset)
    with np.load(model/'gp.npz') as a,np.load(other/'gp.npz') as b:
        np.testing.assert_array_equal(a['x'],b['x'])
        np.testing.assert_array_equal(a['residual'],b['residual'])
    assert json.loads((other/'manifest.json').read_text())['baselines']==metadata['baselines']
    (model/'gp.npz').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='checksum'):predict_model(tmp_path,req)


def test_dataset_rejects_changed_source_and_incomplete_jobs(tmp_path):
    manager=synthetic_test_catalogue(tmp_path)
    dataset=build_dataset(tmp_path,'u1')
    first=manager.list()[0]
    (tmp_path/'runs'/first.id/'analysis.json').write_text('{}')
    with pytest.raises(ValueError,match='checksum'):train_model(tmp_path,dataset)
    manager._update(first.id,state='cancelled')
    with pytest.raises(ValueError,match='validated parameter points'):build_dataset(tmp_path,'u1')
