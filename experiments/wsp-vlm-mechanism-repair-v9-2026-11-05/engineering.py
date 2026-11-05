"""Bounded v9 real-model acceptance, not scientific localization or search."""
import argparse
import gc
import json
from pathlib import Path
import time
import traceback
import numpy as np
from common import HERE, REVISION, file_hash, write_json, digest, packed
from weights import TensorSource, Candidates, quantize, check_targeted_edit
from evidence import Evidence
from backend import VLMBackend
from kernel import SandboxKernel
from service import Service


def run(task, root):
    cfg=json.loads((HERE/f'config-{task}.json').read_text());cfg['phase']='engineering'
    source=TensorSource(cfg['model_root'],cfg['aliases'])
    c=cfg['contract']; candidates=Candidates(source,root/'candidates',c['temporary_scalars'],c['final_scalars'],targeted=True)
    evidence=Evidence(cfg['evidence_root'],cfg['evidence_sha256'])
    for name in ('public','work','artifacts'):(root/name).mkdir()
    write_json(root/'public/kernel.json',dict(aliases=source.aliases,temporary_scalars=c['temporary_scalars'],final_scalars=c['final_scalars'],targeted=True))
    write_json(root/'public/public.json',dict(current=candidates.base_id,best=candidates.base_id))
    kernel=SandboxKernel(cfg,root/'work',root/'public',root/'candidates',evidence.root,root/'artifacts')
    backend=VLMBackend(cfg,source,evidence)
    service=Service(root,candidates,evidence,backend,kernel,c,'engineering-v9')
    checks={}; counts=dict(generation_samples=0,measurement_samples=0,model_loads=0)
    try:
        result=service.dispatch(dict(id='isolation',kind='python',code="""import os,importlib.util,socket
assert not os.path.exists('/root/.codex') and not os.path.exists('/dev/nvidia0')
assert not any(importlib.util.find_spec(n) for n in ('torch','transformers','jax','tensorflow'))
try:
 open('/state/forbidden','w'); raise AssertionError('writable observer')
except OSError: pass
try:
 socket.create_connection(('1.1.1.1',443),timeout=1); raise AssertionError('network')
except OSError: pass
v9_probe=41
print('isolated',len(NAMES))"""))
        assert not result['failed'],result
        second=service.dispatch(dict(id='persistent',kind='python',code="assert v9_probe+1==42; print('persistent')"))
        assert not second['failed'],second
        checks['isolation']=True
        cat=backend.catalog(); counts['model_loads']+=1; write_json(root/'catalog.json',cat)
        assert set(source.entries)<=set(cat['parameters']);checks['module_mapping']=True
        oldroot=HERE.parents[1]/f'external/wsp-vlm-open-repair-v8-2026-11-05/{task}'
        state=json.loads((oldroot/'state.json').read_text());previous=None
        for e in state['evaluations'].values():
            data=json.loads((oldroot/e['path']).read_text())
            if data['candidate']==candidates.base_id and data['full_development']:
                previous={r['request_id']:r for r in data['predictions']};break
        assert previous is not None
        requests=[r['input'] for r in list(evidence.records.values())[:64]]
        outputs=backend.generate_batch(requests,candidates,candidates.base_id,180);counts['generation_samples']+=len(requests)
        for r in outputs:
            for key in ('generated_ids','input_ids_sha256','rendered_chat_sha256','image_grid_thw','processed_hw'):
                assert r[key]==previous[r['request_id']][key],(r['request_id'],key)
        write_json(root/'batch-replay.json',outputs);checks['input_equivalence']=True
        request=requests[0]
        measured=backend.measure(request,candidates,candidates.base_id,dict(layers=[0]));counts['measurement_samples']+=1
        torch=backend.torch; direct={};handles=[]
        def capture_output(module,args,out): direct['residual']=out.detach().float().cpu()
        def capture_input(module,args): direct['mlp']=args[0].detach().float().cpu()
        handles.append(backend.modules['model.language_model.layers.0'].register_forward_hook(capture_output))
        handles.append(backend.modules['model.language_model.layers.0.mlp.down_proj'].register_forward_pre_hook(capture_input))
        try:
            inputs,meta=backend.encode(request)
            with torch.inference_mode():backend.model(**inputs,use_cache=False,return_dict=True)
            counts['measurement_samples']+=1
        finally:
            for h in handles:h.remove()
        comparisons=[]
        for capture in measured['captures']:
            key='mlp' if capture['module'].endswith('.mlp.down_proj') else 'residual'
            expected=direct[key][:,meta['prompt_tokens']-1,:].reshape(-1).numpy()
            observed=np.asarray(capture['values'],dtype=np.float32)
            comparisons.append(dict(module=capture['module'],expected_shape=list(expected.shape),observed_shape=list(observed.shape),max_abs_error=float(np.max(np.abs(observed-expected))) if observed.shape==expected.shape else None))
            write_json(root/'capture-comparison.json',comparisons)
            assert np.array_equal(observed,expected)
        write_json(root/'capture-summary.json',dict(shapes=[x['shape'] for x in measured['captures']],selected_shapes=[x['selected_shape'] for x in measured['captures']],max_abs_error=0))
        checks['vector_capture']=checks['measurement_numerics']=True
        name='model.language_model.layers.0.mlp.down_proj.weight'
        x=source.load(name);x.flat[0]+=.125;x.flat[17]-=.25
        m=candidates.commit(candidates.base_id,{name:x},'ENGINEERING_ONLY two coordinates, not a research target')
        expected=quantize(x,source.effective_dtype)
        fresh=Candidates(source,root/'candidates',c['temporary_scalars'],c['final_scalars'],targeted=True)
        assert fresh.load(m['id'],name).tobytes()==expected.tobytes()
        assert (root/'candidates'/m['id']/m['tensors'][name]['file']).stat().st_size<2048
        checks['sparse_bitwise_reload']=True
        norm='model.language_model.layers.0.input_layernorm.weight';base=source.load(norm)
        try:candidates.commit(candidates.base_id,{norm:base*1.075},'ENGINEERING excluded tensor scale')
        except ValueError:pass
        else:raise AssertionError('whole tensor scale accepted')
        try:check_targeted_edit('model.language_model.embed_tokens.weight',np.ones(2),np.zeros(2),'BF16')
        except ValueError:pass
        else:raise AssertionError('embedding accepted')
        checks['targeted_restrictions']=True
        try:
            with backend.candidate(fresh,m['id']):
                assert torch.equal(backend.parameters[name],torch.as_tensor(expected,device='cuda:0',dtype=torch.bfloat16))
                raise RuntimeError('expected exception')
        except RuntimeError as e:assert str(e)=='expected exception'
        assert torch.equal(backend.parameters[name],torch.as_tensor(source.load(name),device='cuda:0',dtype=torch.bfloat16))
        edited=backend.generate(request,fresh,m['id'],120);counts['generation_samples']+=1
        restored=backend.generate(request,fresh,candidates.base_id,120);counts['generation_samples']+=1
        r=service.dispatch(dict(id='vector-service',kind='forward',request=dict(op='diagnose',ids=[request['request_id']],spec=dict(layers=[0]))))
        assert not r['failed'],r
        counts['measurement_samples']+=1;counts['generation_samples']+=1
        file=r['value']['results'][0]['captures'][0]['array_file']
        probe=service.dispatch(dict(id='read-array',kind='python',code="a=np.load(ARTIFACTS+"+repr('/'+file)+",allow_pickle=False); assert a.ndim==1 and a.size>8; print(a.shape)"))
        assert not probe['failed'],probe;checks['v9_service']=True
        del inputs,direct,handles
        backend.modules={};backend.parameters={};backend.model=None;gc.collect();torch.cuda.empty_cache()
        reloaded=VLMBackend(cfg,source,evidence)
        again=reloaded.generate(request,fresh,m['id'],120);counts['model_loads']+=1;counts['generation_samples']+=1
        final=reloaded.generate(request,fresh,candidates.base_id,120);counts['generation_samples']+=1
        assert again['generated_ids']==edited['generated_ids'];assert final['generated_ids']==restored['generated_ids']
        write_json(root/'reload.json',dict(edited=edited,reloaded=again,restored=final))
        checks['edit_rollback_reload']=True
        # Unchanged transport/image protocol: reuse its actual prior acceptance explicitly.
        old=HERE.parent/'wsp-vlm-open-repair-v7-2026-11-05/audit/engineering_acceptance.json'
        prior=json.loads(old.read_text());assert prior['checks']['researcher_images_and_session']
        assert file_hash(HERE/'controller.py')==file_hash(HERE.parent/'wsp-vlm-open-repair-v8-2026-11-05/controller.py')
        checks['researcher_images_and_session']=True
        return dict(checks=checks,calls=counts,reused_transport_acceptance=dict(path=str(old),sha256=file_hash(old)))
    finally:service.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--task',choices=['B','C'],required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False);started=time.time();result={};status='failed'
    try:result=run(a.task,a.out);status='complete'
    except Exception:(a.out/'failure.txt').write_text(traceback.format_exc());raise
    finally:
        receipt=dict(status=status,real_model_acceptance=status=='complete',synthetic_only=False,revision=REVISION,
            task=a.task,elapsed_seconds=time.time()-started,**result,
            code_sha256={n:file_hash(HERE/n) for n in ['common.py','weights.py','kernel.py','backend.py','service.py','controller.py','live.py','round_broker.py','run_rounds.py','RESEARCHER.md']})
        write_json(a.out/'receipt.json',receipt)
        if status=='complete':write_json(HERE/f'audit/engineering-{a.task}.json',receipt)
