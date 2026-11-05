"""Reuse v7 acceptance operations on this checkpoint; no score-based selection."""
import gc
import json
import traceback
import numpy as np
import time
from pathlib import Path
from common import HERE, write_json, file_hash


def run(config, root):
    from weights import TensorSource, Candidates
    from evidence import Evidence
    from kernel import SandboxKernel
    from backend import VLMBackend
    root = Path(root); root.mkdir(exist_ok=False)
    start = time.time()
    source = TensorSource(config['model_root'], config['aliases'])
    targeted=config['contract'].get('targeted',False)
    candidates = Candidates(source, root/'candidates', 4000000, 1000000, targeted=targeted)
    evidence = Evidence(config['evidence_root'], config['evidence_sha256'])
    for name in ('public', 'work', 'artifacts'):
        (root/name).mkdir()
    write_json(root/'public/kernel.json', dict(aliases=source.aliases, temporary_scalars=4000000, final_scalars=1000000, targeted=targeted))
    write_json(root/'public/public.json', dict(current=candidates.base_id, best=candidates.base_id))
    kernel = SandboxKernel(config, root/'work', root/'public', root/'candidates', evidence.root, root/'artifacts')
    try:
        result = kernel.call("""import os, socket, importlib.util
assert not os.path.exists('/root/.codex')
assert not os.path.exists('/workspace/acupuncture/experiments')
assert not os.path.exists('/dev/nvidia0')
assert not any(importlib.util.find_spec(n) for n in ('torch','transformers','jax','tensorflow'))
try:
    socket.create_connection(('1.1.1.1',443),timeout=1)
    raise AssertionError('network available')
except OSError: pass
try:
    open('/state/forbidden','w')
    raise AssertionError('observer state writable')
except OSError: pass
probe=41
print('ISOLATION_OK',len(NAMES))""", 90)
        write_json(root/'isolation.json', result); assert not result['failed']
        assert not kernel.call("assert probe+1==42", 30)['failed']
    finally:
        kernel.close()
    backend = VLMBackend(config, source, evidence)
    catalog = backend.catalog(); write_json(root/'runtime_catalog.json', catalog)
    assert set(source.entries).issubset(catalog['parameters'])
    calibration_samples=0
    if not targeted:
        from batch_calibration import calibrate
        calibration=calibrate(backend,candidates,evidence,root/'batch-calibration')
        config['execution_batch_size']=calibration['chosen_batch_size'];calibration_samples=calibration['generation_samples']
    else:
        prior_path=HERE.parents[1]/f"external/wsp-vlm-gemma3-v8-2026-11-05-r02/{config['task']}/engineering/acceptance.json"
        prior=json.loads(prior_path.read_text());assert prior['real_model_acceptance']
        config['execution_batch_size']=prior['execution_batch_size']
        write_json(root/'batch-reuse.json',dict(path=str(prior_path),sha256=file_hash(prior_path),execution_batch_size=config['execution_batch_size']))
    write_json(root/'selected-config.json',config)
    requests = [r['input'] for r in evidence.select()[:max(64,config['execution_batch_size'])]]
    # CPU/processor checks, not extra target-model forward calls.
    native_checks=[backend.verify_native_inputs(next(r['input'] for r in evidence.records.values() if bool(r['input']['image'])==has_image))
                   for has_image in sorted({bool(r['input']['image']) for r in evidence.records.values()})]
    write_json(root/'native-inputs.json',native_checks)
    first = backend.generate_batch(requests, candidates, candidates.base_id, 900)
    second = backend.generate_batch(requests, candidates, candidates.base_id, 900)
    assert first == second
    if targeted:
        prior_batch=json.loads((prior_path.parent/'batch-repeat.json').read_text())
        assert first==prior_batch['first'],'Gemma v8/v9 W0 input/output mismatch'
    write_json(root/'batch-repeat.json', dict(first=first, second=second))
    request = requests[0]
    single = backend.generate(request, candidates, candidates.base_id, 120)
    for a,b in zip(first,second):
        for k in ('input_ids_sha256','rendered_chat_sha256','image_grid_thw','processed_hw','visual_tokens'):
            assert a[k] == b[k]
    for k in ('input_ids_sha256','rendered_chat_sha256','image_grid_thw','processed_hw','visual_tokens'):
        assert first[0][k] == single[k]
    write_json(root/'single.json', single)
    edits = {}
    predicates = [lambda n:n.startswith('vision_tower.') and n.endswith('.weight'),
                  lambda n:'.self_attn.' in n and n.startswith('language_model.') and n.endswith('.weight'),
                  lambda n:'.mlp.' in n and 'language_model' in n and n.endswith('.weight')]
    for predicate in predicates:
        name = next(n for n in sorted(source.entries) if predicate(n))
        x = source.load(name); x.flat[0] += .125; edits[name] = x
    m = candidates.commit(candidates.base_id, edits, 'ENGINEERING_ONLY: three fixed arithmetic storage probes')
    assert m['changed_scalars'] == 3
    fresh=Candidates(source,root/'candidates',4000000,1000000,targeted=targeted)
    from weights import quantize,check_targeted_edit
    for name,x in edits.items():
        assert fresh.load(m['id'],name).tobytes()==quantize(x,source.effective_dtype).tobytes()
        canonical=source.canonical(name)
        assert (root/'candidates'/m['id']/m['tensors'][canonical]['file']).stat().st_size<2048
    extra_checks={'sparse_bitwise_reload':True}
    if targeted:
        norm='language_model.model.layers.0.input_layernorm.weight'
        try:candidates.commit(candidates.base_id,{norm:source.load(norm)*1.075},'ENGINEERING forbidden scalar scale')
        except ValueError:pass
        else:raise AssertionError('Whole tensor scale accepted')
        for forbidden in ('language_model.model.embed_tokens.weight','language_model.model.norm.weight','language_model.lm_head.weight'):
            try:check_targeted_edit(forbidden,np.ones(2),np.zeros(2),'BF16')
            except ValueError:pass
            else:raise AssertionError('Forbidden Gemma parameter accepted')
        extra_checks['targeted_restrictions']=True
    torch = backend.torch
    try:
        with backend.candidate(candidates, m['id']):
            for name in edits:
                assert torch.equal(backend.parameters[name], torch.as_tensor(candidates.load(m['id'],name),device='cuda:0',dtype=torch.bfloat16))
            raise RuntimeError('EXPECTED_EXCEPTION')
    except RuntimeError as exc:
        assert str(exc) == 'EXPECTED_EXCEPTION'
    for name in edits:
        assert torch.equal(backend.parameters[name], torch.as_tensor(source.load(name),device='cuda:0',dtype=torch.bfloat16))
    edited = backend.generate(request,candidates,m['id'],120)
    inputs,meta = backend.encode(request)
    with torch.inference_mode():
        logits = backend.model(**inputs,use_cache=False,return_dict=True).logits
    tokens = logits[0,-1].topk(3).indices.tolist()
    measured = backend.measure(request,candidates,candidates.base_id,dict(score_token_ids=tokens,
        capture=[dict(module='lm_head',flat_indices=[(meta['input_tokens']-1)*logits.shape[-1]+i for i in tokens])]))
    for i,v in zip(tokens,measured['captures'][0]['values']):
        assert v == float(logits[0,-1,i]) == measured['next_token_logits'][str(i)]
    write_json(root/'measurement.json',measured)
    # Same individual forwards, one immutable candidate load for the whole diagnostic action.
    probe=requests[:2];spec=dict(score_token_ids=tokens)
    individual=[backend.measure(q,candidates,m['id'],spec) for q in probe]
    with backend.candidate(candidates,m['id']):
        grouped=[backend.measure(q,candidates,m['id'],spec) for q in probe]
    assert individual==grouped
    for name in m['tensors']:
        assert torch.equal(backend.parameters[name],torch.as_tensor(source.load(name),device='cuda:0',dtype=torch.bfloat16))
    write_json(root/'grouped-measure-check.json',dict(equal=True,samples=2,forwards=4,candidate=m['id']))
    extra_checks['grouped_measure_equivalence']=True
    if targeted:
        measured_vectors=backend.measure(request,candidates,candidates.base_id,dict(layers=[0]))
        direct={}
        h1=backend.modules['model.language_model.layers.0'].register_forward_hook(lambda m,a,o: direct.update(residual=o.detach().float().cpu()))
        h2=backend.modules['model.language_model.layers.0.mlp.down_proj'].register_forward_pre_hook(lambda m,a: direct.update(mlp=a[0].detach().float().cpu()))
        try:
            with torch.inference_mode():backend.model(**inputs,use_cache=False,return_dict=True)
        finally:h1.remove();h2.remove()
        for capture in measured_vectors['captures']:
            key='mlp' if capture['module'].endswith('.mlp.down_proj') else 'residual'
            expected=direct[key][:,meta['prompt_tokens']-1,:].reshape(-1).numpy()
            assert np.array_equal(expected,np.asarray(capture['values'],dtype=np.float32))
        write_json(root/'vector-check.json',dict(max_abs_error=0,modules=[x['module'] for x in measured_vectors['captures']]))
        extra_checks['vector_capture']=True
        from service import Service
        service=Service(root,candidates,evidence,backend,kernel,config['contract'],'gemma-engineering')
        try:
            result=service.dispatch(dict(id='vector-service',kind='forward',request=dict(op='diagnose',ids=[request['request_id']],spec=dict(layers=[0]))))
            assert not result['failed'],result
            filename=result['value']['results'][0]['captures'][0]['array_file']
            probe=service.dispatch(dict(id='read-array',kind='python',code="a=np.load(ARTIFACTS+"+repr('/'+filename)+",allow_pickle=False); assert a.ndim==1 and a.size>8; print(a.shape)"))
            assert not probe['failed'],probe
        finally:service.close()
        extra_checks['v9_service']=True
        del direct,expected,measured_vectors
    old=HERE.parent/'wsp-vlm-open-repair-v7-2026-11-05/audit/engineering_acceptance.json'
    assert json.loads(old.read_text())['checks']['researcher_images_and_session']
    assert file_hash(HERE/'controller.py')==file_hash(HERE.parent/'wsp-vlm-open-repair-v8-2026-11-05/controller.py')
    extra_checks['researcher_images_and_session']=True
    del inputs,logits,edits
    backend.modules={};backend.parameters={};backend.model=None
    gc.collect();torch.cuda.empty_cache()
    reloaded = VLMBackend(config,source,evidence)
    again = reloaded.generate(request,candidates,m['id'],120)
    restored = reloaded.generate(request,candidates,candidates.base_id,120)
    assert again['generated_ids'] == edited['generated_ids']
    assert restored['generated_ids'] == single['generated_ids']
    write_json(root/'reload.json',dict(edited=edited,reloaded=again,restored=restored))
    receipt = dict(real_model_acceptance=True,synthetic_only=False,revision=config['model_revision'],
        model_files=config['model_file_sha256'], elapsed_seconds=time.time()-start,
        task=config['task'],contract_sha256=config['contract_sha256'],evidence_sha256=config['evidence_sha256'],
        checks=dict({k:True for k in ('isolation','module_mapping','input_equivalence','native_processor_equivalence','measurement_numerics','edit_rollback_reload','batch_repeat')},**extra_checks),
        reused_transport_acceptance=dict(path=str(old),sha256=file_hash(old)),
        target_forward_samples=2*len(requests)+(14 if targeted else 10)+calibration_samples,
        generation_samples=2*len(requests)+(5 if targeted else 4)+calibration_samples, model_loads=2,
        execution_batch_size=config['execution_batch_size'],calibration_generation_samples=calibration_samples,
        scope='engineering only; not repair rounds',
        engine_hashes={n:file_hash(HERE/n) for n in ('common.py','backend.py','weights.py','kernel.py','service.py','evidence.py','live.py','engineering.py','controller.py','RESEARCHER.md','queue_run.py','prepare.py','batch_calibration.py')})
    write_json(root/'acceptance.json',receipt)
    reloaded.modules={};reloaded.parameters={};reloaded.model=None
    gc.collect();torch.cuda.empty_cache()
    return receipt

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    try:run(json.loads(a.config.read_text()),a.out)
    except BaseException:
        a.out.mkdir(parents=True,exist_ok=True)
        (a.out/'failure.txt').write_text(traceback.format_exc())
        write_json(a.out/'failure.json',dict(status='failed',time_unix=time.time(),real_model_acceptance=False))
        raise
