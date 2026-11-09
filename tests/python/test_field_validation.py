"""Synthetic map fixtures verify comparison metadata and uncertainty handling."""
import pytest
from analysis.artifacts import seal, write_json
from analysis.contracts import FieldMap, SimulationRequest
from analysis.field_validation import compare_fields


def test_temporal_comparison_rejects_mismatch_and_detects_variation(tmp_path):
    paths=[]
    for i,t in enumerate((1,2,3)):
        path=tmp_path/str(i);path.mkdir();paths.append(path)
        request=SimulationRequest(seed=i+1,field_t=t)
        write_json(path/'request.json',request.model_dump(mode='json'))
        field=FieldMap(source_runs=[str(i)],status='unresolved',reasons=[],separation=1,
            temporal_extent=t,probe=(0,3),shape=(4,4),values=[[.01]*4 for _ in range(4)],
            errors=[[.001]*4 for _ in range(4)],analysis_settings=request.analysis)
        write_json(path/'field.json',field.model_dump(mode='json'));seal(path,str(i),True)
    assert compare_fields(paths)['status']=='compatible within errors'
    with pytest.raises(ValueError,match='at least three'):compare_fields(paths[:2])
    import json
    field=json.loads((paths[-1]/'field.json').read_text());field['values'][0][0]=1.
    write_json(paths[-1]/'field.json',field);seal(paths[-1],'2',True)
    assert compare_fields(paths)['status']=='unstable'
    request=SimulationRequest(seed=3,beta=2.,field_t=3)
    write_json(paths[-1]/'request.json',request.model_dump(mode='json'));seal(paths[-1],'2',True)
    with pytest.raises(ValueError,match='matching'):compare_fields(paths)
