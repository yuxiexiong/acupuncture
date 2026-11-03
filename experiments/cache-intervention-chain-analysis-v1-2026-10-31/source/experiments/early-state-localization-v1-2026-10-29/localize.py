"""Early-layer localization, stage 1 (CONTRACT.zh-CN.md r01). Imports never load a model.

python localize.py freeze PATH
python localize.py run --stage preflight|development|confirmation --gpu G --authorization AUTH --output DIR
python localize.py verify WORKER_DIR
python localize.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SOURCE = HERE.parent / 'early-input-control-v1-2026-10-29'
_spec = importlib.util.spec_from_file_location('loc_source_experiment', SOURCE / 'experiment.py')
exp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(exp)

COMPONENTS = ('kv', 'recurrent', 'conv')
ARMS = {'A0': (), 'A1': ('kv', 'recurrent', 'conv'), 'A2': ('kv',), 'A3': ('recurrent',),
        'A4': ('conv',), 'A5': ('recurrent', 'conv')}
ANCHORS = ('N_L00_C4146_D+1', 'N_L02_C5251_D-1', 'N_L02_C5063_D+1')
CONTROL = 'N_L25_C2747_D+1'
STAGES = ('preflight', 'development', 'confirmation')
DEV_BAND = (0.897, 1.045)
MIN_FREE_MIB = 20 * 1024


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def tensor_hash(tensor):
    import torch
    raw = tensor.detach().contiguous().cpu().reshape(-1).view(dtype=torch.uint8)
    return sha_bytes(raw.numpy().tobytes())


# ---------------------------------------------------------------- cache primitives (model only)

def layer_types(model):
    config = model.config
    config = getattr(config, 'text_config', config)
    return list(config.layer_types)


def forward(model, tokens, start, cache, attentions=False):
    """One explicit-position forward over `tokens` beginning at absolute position `start`.

    attentions=True reads, via temporary read-only hooks (never `output_attentions`, which installs
    persistent transformers hooks), the last-query attention mass on position 0 at each full-attention layer.
    """
    import torch
    device = next(model.parameters()).device
    ids = torch.tensor([tokens], device=device)
    positions = torch.arange(start, start + len(tokens), device=device).view(1, -1)
    mask = torch.ones((1, start + len(tokens)), device=device, dtype=torch.long)
    handles, mass = [], {}
    if attentions:
        layers = model_layers(model)
        for i, kind in enumerate(layer_types(model)):
            if kind == 'full_attention':
                def read(_module, _args, output, i=i):
                    weights = output[1]
                    assert weights is not None, 'eager attention weights unavailable'
                    mass[str(i)] = float(weights[0, :, -1, 0].float().mean())
                handles.append(layers[i].self_attn.register_forward_hook(read))
    try:
        out = model(input_ids=ids, position_ids=positions, attention_mask=mask, past_key_values=cache,
                    use_cache=True, logits_to_keep=1)
    finally:
        for h in handles:
            h.remove()
    assert out.past_key_values is not None
    out.first_token_attention = mass if attentions else None
    return out


def build_cache(model, prefix):
    """Cache after reading prompt positions 0..n-2 (no injection logic here; callers hold hooks)."""
    out = forward(model, prefix, 0, None)
    return out.past_key_values


def component_tensors(cache, types):
    """Yield (layer, component, getter, setter) for every cache tensor of the three classes."""
    rows = []
    for i, kind in enumerate(types):
        layer = cache.layers[i]
        if kind == 'full_attention':
            rows.append((i, 'kv', 'keys'))
            rows.append((i, 'kv', 'values'))
        else:
            assert kind == 'linear_attention', kind
            rows.append((i, 'recurrent', 'recurrent_states'))
            rows.append((i, 'conv', 'conv_states'))
    return rows


def _get(layer, field):
    value = getattr(layer, field)
    return value[0] if isinstance(value, dict) else value


def _set(layer, field, tensor):
    value = getattr(layer, field)
    if isinstance(value, dict):
        value[0] = tensor
    else:
        setattr(layer, field, tensor)


def compose(cache_t, cache_c, types, clean):
    """Deep copy of T with the named component classes replaced by clones from C."""
    assert set(clean) <= set(COMPONENTS)
    new = copy.deepcopy(cache_t)
    for i, comp, field in component_tensors(new, types):
        if comp in clean:
            source = _get(cache_c.layers[i], field)
            assert source is not None, (i, field)
            _set(new.layers[i], field, source.clone())
    return new


def randomize(cache, types, component, seed):
    """Readability control: replace one component class by same-norm Gaussian tensors."""
    import torch
    new = copy.deepcopy(cache)
    gen = torch.Generator(device='cpu').manual_seed(seed)
    for i, comp, field in component_tensors(new, types):
        if comp == component:
            old = _get(new.layers[i], field)
            noise = torch.randn(old.shape, generator=gen, dtype=torch.float32).to(old.device)
            noise = noise * (old.float().norm() / noise.norm().clamp_min(1e-12))
            _set(new.layers[i], field, noise.to(old.dtype))
    return new


def audit(cache, cache_t, cache_c, types):
    """Per tensor: hash and whether it equals T and/or C (source audit for every record)."""
    rows = []
    for i, comp, field in component_tensors(cache, types):
        h = tensor_hash(_get(cache.layers[i], field))
        rows.append({'layer': i, 'component': comp, 'field': field, 'sha256': h,
                     'equals_T': h == tensor_hash(_get(cache_t.layers[i], field)),
                     'equals_C': h == tensor_hash(_get(cache_c.layers[i], field))})
    return rows


def check_audit(rows, clean):
    for r in rows:
        want_c = r['component'] in clean
        assert (r['equals_C'] if want_c else r['equals_T']), r
    return True


def decode(model, cache, last_token, n_prompt, stop_ids, max_new_tokens=128, attentions=True, hash_all=False):
    """Greedy, explicit incremental decode from a composed cache; reads the last prompt token first."""
    import torch
    cache = copy.deepcopy(cache)
    tokens, readouts, attention = [], [], None
    current, position = last_token, n_prompt - 1
    started = time.monotonic()
    with torch.inference_mode():
        for step in range(max_new_tokens):
            out = forward(model, [current], position, cache, attentions=attentions and step == 0)
            if step == 0 and attentions:
                attention = out.first_token_attention
            cache = out.past_key_values
            logits = out.logits[0, -1].float()
            assert torch.isfinite(logits).all()
            token = int(logits.argmax())
            non_stop = logits.clone()
            non_stop[stop_ids] = -float('inf')
            row = {'step': step, 'token': token, 'stop_advantage': float(logits[stop_ids].max() - non_stop.max())}
            if step == 0 or hash_all:
                row['logits_sha256'] = tensor_hash(logits)
            if step == 0:
                lp = torch.log_softmax(logits, -1)
                top = lp.topk(5)
                row['top5'] = [{'token_id': int(t), 'logprob': float(v)} for v, t in zip(top.values, top.indices)]
            readouts.append(row)
            tokens.append(token)
            if token in stop_ids:
                break
            current, position = token, position + 1
    end = 'eos_token' if tokens[-1] in stop_ids else 'length_limit'
    return {'token_ids': tokens, 'end_reason': end, 'readouts': readouts, 'first_token_attention': attention,
            'seconds': time.monotonic() - started}


def score(model, cache, last_token, n_prompt, candidate):
    """Forced candidate continuation from the same composed cache."""
    import torch
    cache = copy.deepcopy(cache)
    current, position, logprobs, hashes = last_token, n_prompt - 1, [], []
    with torch.inference_mode():
        for target in candidate:
            out = forward(model, [current], position, cache)
            cache = out.past_key_values
            logits = out.logits[0, -1].float()
            logprobs.append(float(torch.log_softmax(logits, -1)[target]))
            hashes.append(tensor_hash(logits))
            current, position = target, position + 1
    return {'token_ids': list(candidate), 'token_logprobs': logprobs, 'loglikelihood': sum(logprobs), 'logits_sha256': hashes}


@contextmanager
def masked_injection(engine, condition, reference, mask):
    """Same write arithmetic as ControlEngine._control_hooks, applied on an explicit position mask."""
    import math
    torch = engine.torch
    engine._validate_condition(condition, reference)
    handles, audit_rows = [], []
    layer = condition['layer']
    weight = engine.modules[layer].weight
    scale, dose = reference['residual_scales'][str(layer)], condition['dose']

    def tensor_mask(width, device):
        assert width == len(mask)
        return torch.tensor(mask, dtype=torch.bool, device=device).reshape(1, -1)

    if condition['kind'] == 'native':
        channel = condition['channel']
        column_norm = float(engine.column_norms[str(layer)][channel])
        assert math.isfinite(column_norm) and column_norm > 0
        amount = weight.new_tensor(dose * scale / column_norm)

        def add_channel(_module, args):
            original = args[0]
            m = tensor_mask(original.shape[1], original.device)
            changed = original.clone()
            changed[..., channel] += amount * m.to(original.dtype)
            audit_rows.append({'positions': int(m.sum()), 'width': original.shape[1]})
            return (changed, *args[1:])
        handles.append(engine.modules[layer].register_forward_pre_hook(add_channel))
    else:
        vector = torch.tensor(condition['vector'], device=engine.device, dtype=torch.float32)
        addition = (vector * (dose * scale)).to(weight.dtype)

        def add_direction(_module, _args, output):
            original = output[0] if isinstance(output, tuple) else output
            m = tensor_mask(original.shape[1], original.device)
            changed = original + m[..., None].to(original.dtype) * addition
            audit_rows.append({'positions': int(m.sum()), 'width': original.shape[1]})
            return (changed, *output[1:]) if isinstance(output, tuple) else changed
        handles.append(engine.layers[layer].mlp.register_forward_hook(add_direction))
    try:
        yield audit_rows
    finally:
        for h in reversed(handles):
            h.remove()


@contextmanager
def gate_decay(model, types):
    """Record per linear layer the surviving fraction exp(sum_{t>p} g_t) for p = 0 and p = mid."""
    import torch
    out, handles = {}, []
    for i, kind in enumerate(types):
        if kind != 'linear_attention':
            continue
        attn = model_layers(model)[i].linear_attn

        def hook(module, _args, output, i=i, attn=attn):
            a = output[0].float()  # (seq, heads)
            g = -attn.A_log.float().exp() * torch.nn.functional.softplus(a + attn.dt_bias.float())
            n = g.shape[0]
            mid = max(n // 2 - 1, 0)
            # log of the fraction exp(sum_{t>p} g_t) surviving to the last prefix position, mean over heads
            log_tail = lambda p: float(g[p + 1:].sum(0).mean()) if p + 1 < n else 0.0
            out[str(i)] = {'positions': n, 'log_survive_from_0': log_tail(0), 'log_survive_from_mid': log_tail(mid)}
        handles.append(attn.in_proj_a.register_forward_hook(hook))
    try:
        yield out
    finally:
        for h in handles:
            h.remove()


def model_layers(model):
    for path in ('model.language_model.layers', 'model.layers'):
        obj = model
        try:
            for part in path.split('.'):
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            continue
    raise AttributeError('decoder layers not found')


# ---------------------------------------------------------------- experiment plumbing

def conditions():
    available = {c['id']: c for c in exp.conditions('development')}
    early = [c for c in available.values() if c['kind'] != 'clean' and c['layer'] < 4 and abs(c['dose']) == 1.0]
    assert len(early) == 24, len(early)
    extra = {'id': 'N_L02_C5063_D+1', 'kind': 'native', 'layer': 2, 'channel': 5063, 'dose': 1.0}
    rows = sorted(early, key=lambda c: c['id']) + [extra, available[CONTROL]]
    assert len({c['id'] for c in rows}) == 26
    return rows


def frozen_paths():
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md']
    deps = [SOURCE / n for n in ('control_engine.py', 'experiment.py', 'contract.json', 'selection.json',
            'data/development.json', 'data/confirmation.json', 'data/anchors.json', 'data/directions.json')]
    deps += [REPO / 'experiments' / n for n in exp.DEPENDENCIES]
    deps += [HERE.parent / 'early-stop-knowledge-readout-v1-2026-10-29/analyze.py']
    return own + deps


def freeze(path):
    value = {'experiment': HERE.name, 'created_at': exp.utc(),
             'files': {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}}
    exp.write(path, value, immutable=True)
    return {'path': str(path), 'sha256': exp.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = exp.read(path)
    actual = {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}
    assert value['files'] == actual, 'Frozen source changed'
    return exp.sha(path)


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['user_instruction']
    assert stage in auth['allowed_stages'] and auth['maximum_workers'] == 2
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    if stage != 'preflight':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256']
        assert auth['preflight_verification_path'] in auth['required_evidence']
    if stage == 'confirmation':
        lock = exp.read(HERE / auth['development_lock_path'])
        assert lock['status'] == 'locked' and lock['confirmation_outputs_previously_unseen'] is True
        assert auth['development_lock_path'] in auth['required_evidence']
    return auth


def rows_for(stage, gpu):
    split = 'development' if stage in ('preflight', 'development') else 'confirmation'
    rows = exp.items(split)
    mine = exp.assigned(rows, gpu)
    if stage == 'preflight':
        mine = mine[:2]
    return split, rows, mine


def plan(stage, gpu):
    split, rows, mine = rows_for(stage, gpu)
    conds = conditions()
    if stage == 'preflight':
        conds = [c for c in conds if c['id'] in ('N_L00_C4146_D+1', 'N_L02_C5251_D-1', 'V0_L00_D+1')]
    specs = []
    for item in mine:
        specs.append({'key': f'{item["id"]}__clean__A1', 'item_id': item['id'], 'condition_id': 'clean', 'arm': 'A1'})
        for c in conds:
            for arm in ('A0', 'A2', 'A3', 'A4', 'A5'):
                specs.append({'key': f'{item["id"]}__{c["id"]}__{arm}', 'item_id': item['id'], 'condition_id': c['id'], 'arm': arm})
            if c['id'] in ANCHORS:
                for arm in ('B1', 'B2'):
                    specs.append({'key': f'{item["id"]}__{c["id"]}__{arm}', 'item_id': item['id'], 'condition_id': c['id'], 'arm': arm})
    assert len({s['key'] for s in specs}) == len(specs)
    return specs


def _store(output, receipt, rel, value):
    exp.write(output / rel, value, immutable=True)
    receipt['record_hashes'][rel] = exp.sha(output / rel)
    receipt['last_record_at'] = exp.utc()
    exp.write(output / 'receipt.json', receipt)


def run(stage, gpu, output, authorization):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{gpu}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-layer-survey-gpu{gpu}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    # User-authorized co-residency (2026-10-29): require free memory instead of an empty GPU; record neighbours.
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    neighbours = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    assert free_mib >= MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'gpu': gpu, 'pid': os.getpid(), 'started_at': exp.utc(),
               'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {},
               'gpu_free_mib_at_start': free_mib, 'coresident_processes_at_start': neighbours.splitlines()}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started, engine = time.monotonic(), None
    sys.path.insert(0, str(SOURCE))
    from control_engine import ControlEngine
    try:
        source = exp.read(SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        receipt['load_seconds'] = time.monotonic() - started
        specs = plan(stage, gpu)
        exp.write(output / 'plan.json', specs, immutable=True)
        receipt['plan_sha256'] = exp.sha(output / 'plan.json')
        result = execute(engine, stage, gpu, output, receipt, specs)
        receipt['summary'] = result
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        receipt.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'receipt.json', receipt)
    return receipt


def _engine_condition(cid):
    if cid == 'clean':
        return {'id': 'clean', 'kind': 'clean', 'dose': 0.0}
    c = next(c for c in conditions() if c['id'] == cid)
    return exp.engine_condition(c)


def _build_T(engine, condition, reference, prefix, mask=None):
    """Treated cache over the prefix; A arms via _control_hooks('prefill'), B arms via masked hook."""
    model, types = engine.model, layer_types(engine.model)
    with gate_decay(model, types) as decay:
        if mask is None:
            state = {'step': -1, 'write_audit': [], 'patch_audit': [], 'cache_fingerprints': {}, 'history': []}
            with engine.torch.inference_mode(), engine._control_hooks(condition, reference, 'prefill', len(prefix), state,
                                                                       0, 'continue', set(), None, None):
                cache = build_cache(model, prefix)
            writes = state['write_audit']
        else:
            with engine.torch.inference_mode(), masked_injection(engine, condition, reference, mask) as writes:
                cache = build_cache(model, prefix)
    return cache, writes, dict(decay)


def _clean_cache(engine, prefix):
    model, types = engine.model, layer_types(engine.model)
    with gate_decay(model, types) as decay, engine.torch.inference_mode():
        cache = build_cache(model, prefix)
    return cache, dict(decay)


def execute(engine, stage, gpu, output, receipt, specs):
    from control_engine import exact_pair, encode_text
    split, rows, mine = rows_for(stage, gpu)
    by_id = {r['id']: r for r in rows}
    contexts = exp.contexts_for(engine.tokenizer, rows)
    types = layer_types(engine.model)
    references = {}
    for rid in sorted({by_id[s['item_id']]['reference_id'] for s in specs}):
        references[rid] = engine.calibrate([contexts[rid]])[0]
        exp.write(output / f'calibrations/{rid}.json', references[rid], immutable=True)
    counts = {'records': 0, 'generations': 0, 'candidate_reads': 0}
    preflight_checks = []
    for item in mine:
        context = contexts[item['id']]
        reference = references[item['reference_id']]
        prompt = encode_text(engine.tokenizer, context)
        prefix, last = prompt[:-1], prompt[-1]
        cands = [exact_pair(engine.tokenizer, context, choice)[1] for choice in item['choices']]
        cache_c, decay_c = _clean_cache(engine, prefix)
        item_specs = [s for s in specs if s['item_id'] == item['id']]
        built = {}
        for spec in item_specs:
            cid, arm = spec['condition_id'], spec['arm']
            condition = _engine_condition(cid)
            if arm == 'A1':
                cache_t, writes, decay_t, mask = cache_c, [], decay_c, None
            elif arm in ARMS:
                if cid not in built:
                    built[cid] = _build_T(engine, condition, reference, prefix)
                cache_t, writes, decay_t = built[cid]
                mask = None
            else:
                m = len(prefix) // 2
                mask = [i < m for i in range(len(prefix))] if arm == 'B1' else [i >= m for i in range(len(prefix))]
                cache_t, writes, decay_t = _build_T(engine, condition, reference, prefix, mask)
            clean = ARMS.get(arm, ())
            cache = compose(cache_t, cache_c, types, clean) if arm in ARMS else copy.deepcopy(cache_t)
            rows_audit = audit(cache, cache_t, cache_c, types) if arm in ARMS else None
            if rows_audit is not None:
                check_audit(rows_audit, clean if arm != 'A1' else COMPONENTS)
            gen = decode(engine.model, cache, last, len(prompt), engine.stop_ids, hash_all=(stage == 'preflight'))
            scores = [score(engine.model, cache, last, len(prompt), c) for c in cands]
            counts['generations'] += 1
            counts['candidate_reads'] += len(scores)
            record = {'schema': 1, 'stage': stage, 'panel': split, 'spec': spec, 'item': item, 'context': context,
                      'reference_sha256': exp.digest(reference), 'condition': {k: v for k, v in condition.items() if k != 'vector'},
                      'clean_components': list(clean), 'injection_mask': mask, 'write_audit': writes,
                      'component_audit': rows_audit, 'gate_decay': {'T': decay_t, 'C': decay_c},
                      'prompt_token_count': len(prompt), 'generation': {**gen,
                          'answer_text': engine.tokenizer.decode(gen['token_ids'], skip_special_tokens=True),
                          'raw_text': engine.tokenizer.decode(gen['token_ids'], skip_special_tokens=False)},
                      'candidates': [{'text': t, **s} for t, s in zip(item['choices'], scores)], 'created_at': exp.utc()}
            _store(output, receipt, f'records/{spec["key"]}.json', record)
            counts['records'] += 1
        if stage == 'preflight':
            preflight_checks.append(preflight_gates(engine, item, context, reference, prompt, cache_c, built, types))
            exp.write(output / f'preflight/{item["id"]}.json', preflight_checks[-1], immutable=True)
        del built
    if stage == 'preflight':
        exp.write(output / 'preflight.json', summarize_preflight(preflight_checks, len(mine)), immutable=True)
    return counts


def summarize_preflight(checks, expected_items):
    assert len(checks) == expected_items and all(isinstance(c, dict) for c in checks), 'preflight checks malformed'
    assert all(c['status'] == 'passed' for c in checks)
    return {'status': 'passed', 'items': expected_items, 'checks': checks}


def preflight_gates(engine, item, context, reference, prompt, cache_c, built, types):
    """Contract §6 gates on real data; any assertion failure stops the worker."""
    torch, model, stop = engine.torch, engine.model, engine.stop_ids
    prefix, last = prompt[:-1], prompt[-1]
    out = {'item_id': item['id'], 'gates': {}}
    cid = 'N_L00_C4146_D+1'
    cache_t = built[cid][0]
    # 1 same-path identity
    for name, base, clean in (('A0', cache_t, ()), ('A1', cache_c, COMPONENTS)):
        direct = decode(model, base, last, len(prompt), stop, hash_all=True, attentions=False)
        composed = decode(model, compose(cache_t, cache_c, types, clean), last, len(prompt), stop, hash_all=True, attentions=False)
        assert direct['token_ids'] == composed['token_ids']
        assert [r['logits_sha256'] for r in direct['readouts']] == [r['logits_sha256'] for r in composed['readouts']]
    out['gates']['same_path_identity'] = 'passed'
    # 2 readability: randomizing each class must change last-position logits
    base = decode(model, cache_t, last, len(prompt), stop, max_new_tokens=1, attentions=False)['readouts'][0]['logits_sha256']
    deltas = {}
    for comp in COMPONENTS:
        rnd = decode(model, randomize(cache_t, types, comp, 7), last, len(prompt), stop, max_new_tokens=1, attentions=False)
        deltas[comp] = rnd['readouts'][0]['logits_sha256'] != base
    assert all(deltas.values()), deltas
    out['gates']['readability'] = deltas
    # 4 incremental path equals the engine generation path on the same (full-prompt) shape
    condition = _engine_condition('clean')
    eng = engine.generate_one(context, reference, condition, mode='full', capture_steps=tuple(range(128)))
    cache0 = None
    with torch.inference_mode():
        first = forward(model, prompt, 0, None)
    logits0 = first.logits[0, -1].float()
    assert tensor_hash(logits0) == eng['step_readouts'][0]['logits_sha256'], 'step-0 logits differ from engine path'
    tok = int(logits0.argmax())
    tail = decode(model, first.past_key_values, tok, len(prompt) + 1, stop, max_new_tokens=len(eng['token_ids']) - 1, attentions=False, hash_all=True) if tok not in stop else {'token_ids': [], 'readouts': []}
    manual_tokens = [tok] + tail['token_ids']
    assert manual_tokens == eng['token_ids'], 'manual incremental decode differs from engine generation'
    assert [r['logits_sha256'] for r in tail['readouts']] == [r['logits_sha256'] for r in eng['step_readouts'][1:]]
    out['gates']['incremental_equals_engine'] = 'passed'
    del cache0
    # 6 masked hook equals _control_hooks('prefill') with an all-true mask
    cond = _engine_condition(cid)
    masked, _, _ = _build_T(engine, cond, reference, prefix, mask=[True] * len(prefix))
    ra = audit(masked, cache_t, cache_c, types)
    assert all(r['equals_T'] for r in ra), 'masked hook differs from _control_hooks prefill'
    out['gates']['masked_hook_equivalence'] = 'passed'
    # 7 the read-only attention hooks do not change logits
    a = decode(model, cache_t, last, len(prompt), stop, max_new_tokens=1, attentions=True)
    b = decode(model, cache_t, last, len(prompt), stop, max_new_tokens=1, attentions=False)
    assert a['readouts'][0]['logits_sha256'] == b['readouts'][0]['logits_sha256']
    out['gates']['attention_readout_inert'] = 'passed'
    out['status'] = 'passed'
    return out


def verify_worker(path):
    path = Path(path)
    r = exp.read(path / 'receipt.json')
    assert r['status'] == 'completed'
    assert r['freeze_sha256'] == exp.sha(HERE / r['freeze_path'])
    check_freeze(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == exp.sha(path / 'authorization.json')
    execution = exp.read(path / 'execution.json')
    for key in ('stage', 'gpu', 'pid', 'started_at', 'freeze_sha256', 'authorization_sha256'):
        assert execution[key] == r[key], key
    specs = exp.read(path / 'plan.json')
    assert specs == plan(r['stage'], r['gpu'])
    expected = {f'records/{s["key"]}.json' for s in specs}
    assert set(r['record_hashes']) == expected
    assert {str(p.relative_to(path)) for p in (path / 'records').glob('*.json')} == expected
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
        rec = exp.read(path / rel)
        g = rec['generation']
        assert 1 <= len(g['token_ids']) <= 128 and len(g['readouts']) == len(g['token_ids'])
        assert (g['end_reason'] == 'eos_token') == (g['token_ids'][-1] in (248044, 248046))
        assert not any(t in (248044, 248046) for t in g['token_ids'][:-1])
        if rec['component_audit'] is not None:
            check_audit(rec['component_audit'], rec['clean_components'])
        assert [c['text'] for c in rec['candidates']] == rec['item']['choices']
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'records': len(r['record_hashes']), 'freeze_sha256': r['freeze_sha256']}


def launch(stage, authorization, output):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'running', 'pid': os.getpid(), 'stage': stage, 'started_at': exp.utc(),
                  'authorization_sha256': exp.sha(authorization), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    exp.write(output / 'execution.json', dict(controller), immutable=True)
    procs, logs, started = {}, [], time.monotonic()
    try:
        for gpu in (0, 1):
            log = (output / f'worker-{gpu}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 'localize.py'), 'run', '--stage', stage, '--gpu', str(gpu),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{gpu}')]
            procs[gpu] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(gpu)] = {'pid': procs[gpu].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            for gpu, p in list(pending.items()):
                code = p.poll()
                if code is None:
                    continue
                (output / f'worker-{gpu}').mkdir(exist_ok=True)
                exp.write(output / f'worker-{gpu}/exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
                controller['workers'][str(gpu)]['returncode'] = code
                failure |= code != 0
                del pending[gpu]
            exp.write(output / 'controller.json', controller)
            if failure:
                for p in pending.values():
                    p.terminate()
            if pending:
                time.sleep(2)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{g}') for g in (0, 1)]
        exp.write(output / 'verification.json', {'status': 'passed', 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for gpu, p in procs.items():
            if p.poll() is None:
                p.terminate()
                code = p.wait()
                w = output / f'worker-{gpu}'
                w.mkdir(exist_ok=True)
                if not (w / 'exit.json').exists():
                    exp.write(w / 'exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
        raise
    finally:
        for log in logs:
            log.close()
        controller.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'controller.json', controller)
    return controller


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    sub.add_parser('verify').add_argument('path')
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--gpu', required=True, type=int, choices=[0, 1])
    a = p.parse_args()
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        sys.path.insert(0, str(SOURCE))
        value = run(a.stage, a.gpu, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k != 'record_hashes'}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
