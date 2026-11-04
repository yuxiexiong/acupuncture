"""Offline acceptance only. All answer fixtures below are synthetic."""
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

from prepare_inputs import HERE,ROOT,all_pairs,read_jsonl,sha
from statistics_b import report
from test_ready import fixture
import runner


def main():
    suite=unittest.defaultTestLoader.discover(str(HERE),pattern='test_ready.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise SystemExit(1)
    validation={}
    for task,stage in [('B','P0'),('B','D'),('B','H'),('C','D'),('C','H')]:
        validation[f'{task}:{stage}']=runner.validate_queue(runner.queue(task,stage))
        validation[f'{task}:{stage}'].pop('original_sizes')
    files=json.loads((HERE/'audit/input_receipt.json').read_text())['files']
    for name,meta in files.items():
        data=(HERE/'prepared'/name).read_bytes()
        assert sha(data)==meta['sha256'] and len(data.splitlines())==meta['records']
    pairs=all_pairs('B')
    assert [i for i,g in pairs]==read_jsonl(HERE/'prepared/B_inputs.jsonl')
    assert [g for i,g in pairs]==read_jsonl(HERE/'prepared/B_gold.jsonl')
    # Actual C source data and all original question texts must still match v1 preparation.
    cp=all_pairs('C')
    assert [i for i,g in cp]==read_jsonl(ROOT/'external/wsp-vlm-screen-data-v1-2026-11-05/prepared_C/inputs.jsonl')
    assert [g for i,g in cp]==read_jsonl(ROOT/'external/wsp-vlm-screen-data-v1-2026-11-05/prepared_C/gold.jsonl')
    synthetic={}
    for kind in ('perfect','gap'):
        pred,gold=fixture(kind);stats=report(pred,gold)
        synthetic[kind]=dict(SYNTHETIC_NOT_MODEL_RESULTS=True,decision=stats['decision'],
            H=stats['splits']['H']['cells']['B0:T0'],holm=stats['holm'])
    assert synthetic['perfect']['decision']=='not_priority_on_current_distribution'
    assert synthetic['gap']['decision']=='behavior_gap_priority_not_WSP_repairability'
    assert not any(name in sys.modules for name in ('torch','transformers','huggingface_hub'))
    receipt=dict(status='OFFLINE_ACCEPTED_NOT_MODEL_VALIDATED',unit_tests=result.testsRun,
        rewrites_reviewed=292,reviewer='same assistant semantic review; not independent human review',
        queues=validation,files=files,C_original_inputs_and_gold_unchanged=True,
        bootstrap_resamples=10000,synthetic_statistics=synthetic,
        forbidden_modules_loaded=[],model_loads=0,model_calls=0,GPU_seconds=0,
        code_sha256={p.name:sha(p.read_bytes()) for p in sorted(HERE.glob('*.py'))})
    (HERE/'audit/offline_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('files','synthetic_statistics','code_sha256')},indent=2))


if __name__=='__main__':main()
