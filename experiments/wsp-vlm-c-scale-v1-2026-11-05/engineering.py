"""Reuse v7 acceptance operations on this checkpoint; no score-based selection."""
import gc
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
    candidates = Candidates(source, root/'candidates', 4000000, 1000000)
    evidence = Evidence(config['evidence_root'], config['evidence_sha256'])
    for name in ('public', 'work', 'artifacts'):
        (root/name).mkdir()
    write_json(root/'public/kernel.json', dict(aliases=source.aliases, temporary_scalars=4000000, final_scalars=1000000))
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
    requests = [r['input'] for r in evidence.select()[:64]]
    first = backend.generate_batch(requests, candidates, candidates.base_id, 900)
    second = backend.generate_batch(requests, candidates, candidates.base_id, 900)
    assert first == second
    write_json(root/'batch64-repeat.json', dict(first=first, second=second))
    request = requests[0]
    single = backend.generate(request, candidates, candidates.base_id, 120)
    for a,b in zip(first,second):
        for k in ('input_ids_sha256','rendered_chat_sha256','image_grid_thw','processed_hw','visual_tokens'):
            assert a[k] == b[k]
    for k in ('input_ids_sha256','rendered_chat_sha256','image_grid_thw','processed_hw','visual_tokens'):
        assert first[0][k] == single[k]
    write_json(root/'single.json', single)
    edits = {}
    predicates = [lambda n:n.startswith('model.visual.') and n.endswith('.weight'),
                  lambda n:'.self_attn.' in n and n.endswith('.weight'),
                  lambda n:'.mlp.' in n and 'language_model' in n and n.endswith('.weight')]
    for predicate in predicates:
        name = next(n for n in sorted(source.entries) if predicate(n))
        x = source.load(name); x.flat[0] += .125; edits[name] = x
    m = candidates.commit(candidates.base_id, edits, 'ENGINEERING_ONLY: three fixed arithmetic storage probes')
    assert m['changed_scalars'] == 3
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
        checks={k:True for k in ('isolation','module_mapping','input_equivalence','measurement_numerics','edit_rollback_reload','batch64_repeat')},
        target_forward_samples=134, generation_samples=132,
        scope='engineering only; not repair rounds',
        engine_hashes={n:file_hash(HERE/n) for n in ('common.py','backend.py','weights.py','kernel.py','service.py','evidence.py','live.py','engineering.py')})
    write_json(root/'acceptance.json',receipt)
    reloaded.modules={};reloaded.parameters={};reloaded.model=None
    gc.collect();torch.cuda.empty_cache()
    return receipt
