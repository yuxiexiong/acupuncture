"""Bounded observer acceptance, not a neuron search. Every failure is preserved."""
import argparse
import json
import time
import traceback
from pathlib import Path
from common import HERE, REVISION, file_hash, write_json


def run(config, root):
    import numpy as np
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from backend import VLMBackend
    source = TensorSource(config['model_root'], config['aliases'])
    candidates = Candidates(source, root/'candidates', 4000000, 1000000)
    evidence = Evidence(config['evidence_root'],config['evidence_sha256'])
    for name in ('public','work','artifacts'):
        (root/name).mkdir()
    write_json(root/'public/kernel.json',dict(aliases=source.aliases,temporary_scalars=4000000,final_scalars=1000000))
    write_json(root/'public/public.json',dict(current=candidates.base_id,best=candidates.base_id))
    kernel = SandboxKernel(config,root/'work',root/'public',root/'candidates',evidence.root,root/'artifacts')
    try:
        probe = """import os, socket, importlib.util
assert not os.path.exists('/root/.codex')
assert not os.path.exists('/workspace/acupuncture/experiments')
assert not os.path.exists('/dev/nvidia0')
assert not any(importlib.util.find_spec(n) for n in ('torch','transformers','jax','tensorflow'))
assert set(os.listdir('/sys/class/net')) <= {'lo'} if os.path.exists('/sys/class/net') else True
try:
    socket.create_connection(('1.1.1.1',443),timeout=1)
    raise AssertionError('network unexpectedly available')
except OSError: pass
try:
    open('/state/forbidden','w')
    raise AssertionError('observer state writable')
except OSError: pass
probe_value=41
print('ISOLATION_OK',len(NAMES))"""
        first=kernel.call(probe,90); write_json(root/'isolation.json',first)
        assert not first['failed'],first
        second=kernel.call("assert probe_value+1==42; print('PERSISTENCE_OK')",30)
        write_json(root/'persistence.json',second);assert not second['failed'],second
    finally: kernel.close()
    checks=dict(isolation=True)
    backend=VLMBackend(config,source,evidence)
    catalog=backend.catalog();write_json(root/'runtime_catalog.json',catalog)
    assert set(source.entries).issubset(set(catalog['parameters']))
    checks['module_mapping']=True
    # Fixed first source group of each task, every prompt/wording/condition/order.
    # This engineering sample is not chosen for task improvements.
    all_evidence=[evidence]
    other=json.loads((HERE/'config-C.json').read_text())
    all_evidence.append(Evidence(other['evidence_root'],other['evidence_sha256']))
    replay=[];previous={}
    for e in all_evidence:
        backend.evidence=e
        group=next(iter(e.records.values()))['gold']['group_id']
        old={r['request_id']:r for r in e.package['previous_predictions']}
        for row in e.records.values():
            if row['gold']['group_id']!=group:continue
            rid=row['input']['request_id'];original=old[rid]
            r=backend.generate(row['input'],candidates,candidates.base_id,120)
            replay.append(r);write_json(root/'replay.json',replay)
            for key in ('text','generated_ids','input_ids_sha256','rendered_chat_sha256','image_grid_thw','processed_hw','visual_tokens'):
                assert r[key]==original[key],(rid,key,r[key],original[key])
            previous[rid]=r
    checks['input_equivalence']=True
    backend.evidence=evidence
    request=next(iter(evidence.records.values()))['input']
    edits={}
    # Three arithmetic storage checks across component families, not task-selected targets.
    predicates=[lambda n:n.startswith('model.visual.') and n.endswith('.weight'),
                lambda n:'.self_attn.' in n and n.endswith('.weight'),
                lambda n:'.mlp.' in n and 'language_model' in n and n.endswith('.weight')]
    for predicate in predicates:
        name=next(n for n in sorted(source.entries) if predicate(n))
        x=source.load(name);x.flat[0]=float(x.flat[0])+.125;edits[name]=x
    m=candidates.commit(candidates.base_id,edits,'ENGINEERING_ONLY: one scalar per component; no score optimization')
    write_json(root/'engineering_candidate.json',m);assert m['changed_scalars']==3
    torch=backend.torch
    try:
        with backend.candidate(candidates,m['id']):
            for name,x in edits.items():
                assert torch.equal(backend.parameters[name],torch.as_tensor(candidates.load(m['id'],name),device='cuda:0',dtype=torch.bfloat16))
            raise RuntimeError('ENGINEERING_EXPECTED_EXCEPTION')
    except RuntimeError as exc:
        assert str(exc)=='ENGINEERING_EXPECTED_EXCEPTION'
    for name in edits:
        assert torch.equal(backend.parameters[name],torch.as_tensor(source.load(name),device='cuda:0',dtype=torch.bfloat16))
    edited=backend.generate(request,candidates,m['id'],120)
    restored=backend.generate(request,candidates,candidates.base_id,120)
    assert restored['generated_ids']==previous[request['request_id']]['generated_ids']
    inputs,meta=backend.encode(request)
    with torch.inference_mode():reference=backend.model(**inputs,use_cache=False,return_dict=True).logits
    token_ids=reference[0,-1].topk(3).indices.tolist()
    measured=backend.measure(request,candidates,candidates.base_id,dict(score_token_ids=token_ids,
        capture=[dict(module='lm_head',flat_indices=[(meta['input_tokens']-1)*reference.shape[-1]+i for i in token_ids])]))
    for i,value in zip(token_ids,measured['captures'][0]['values']):
        assert value==float(reference[0,-1,i])==measured['next_token_logits'][str(i)]
    hooks_before=sum(len(mod._forward_hooks) for mod in backend.modules.values())
    try:
        backend.measure(request,candidates,candidates.base_id,dict(capture=[dict(module='lm_head',flat_indices=[0]),dict(module='__invalid_module__')]))
        raise AssertionError('Expected invalid-module rejection')
    except KeyError:pass
    assert sum(len(mod._forward_hooks) for mod in backend.modules.values())==hooks_before
    checks['measurement_numerics']=True
    write_json(root/'measurement.json',measured)
    del reference,inputs
    backend.modules={};backend.parameters={};backend.model=None
    import gc;gc.collect();torch.cuda.empty_cache()
    reloaded=VLMBackend(config,source,evidence)
    again=reloaded.generate(request,candidates,m['id'],120)
    assert again['generated_ids']==edited['generated_ids']
    final=reloaded.generate(request,candidates,candidates.base_id,120)
    assert final['generated_ids']==restored['generated_ids']
    write_json(root/'reload.json',dict(edited=edited,reloaded=again,restored=final))
    checks['edit_rollback_reload']=True
    return checks


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',required=True);a=p.parse_args()
    root=Path(a.out);root.mkdir(parents=True,exist_ok=False)
    write_json(root/'config.json',json.loads((HERE/'config-B.json').read_text()))
    write_json(root/'source_hashes.json',{p.name:file_hash(p) for p in HERE.glob('*.py')})
    start=time.time();checks={};status='failed'
    try:
        checks=run(json.loads((HERE/'config-B.json').read_text()),root);status='complete'
    except Exception:
        (root/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        write_json(root/'receipt.json',dict(status=status,checks=checks,revision=REVISION,
            elapsed_seconds=time.time()-start,synthetic_only=False,scope='engineering_only'))
