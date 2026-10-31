"""CFM-S2-v3-20261031: native time-switched needles 00/10/01/11 on L16-18 (CONTRACT.zh-CN.md r01).

Imports never load a model. Builds on the frozen CFM-S1 recorder (cfm_trace.py): the same pass-through capture of
the delta-rule drivers, plus (a) the needle restricted to E (positions 0..b) or L (b+1..n-2) with the stage-1
masked injection, (b) the complete post-prefix cache M_tau of every trajectory, (c) common-history certification.

python s2_trace.py freeze PATH
python s2_trace.py run --stage preflight|formal --worker W --authorization AUTH --output DIR   (GPU = W % 2)
python s2_trace.py verify WORKER_DIR
python s2_trace.py launch --stage STAGE --authorization AUTH --output RUN_DIR
"""
import argparse
import copy
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
S1_DIR = HERE.parent / 'cache-formation-mechanism-s1-native-trace-v1-2026-10-31'
sys.path.insert(0, str(S1_DIR))
import cfm_trace as T1  # noqa: E402  (frozen S1 code; brings stage-1/2 primitives)
import account as A1  # noqa: E402
L, S2, exp = T1.L, T1.S2, T1.exp
sys.path.insert(0, str(HERE))

PLAN_ID = 'CFM-S2-v3-20261031'
PLAN_DOC = REPO / 'docs/cache-formation-mechanism-s2-formation-test-plan-v3-2026-10-31.zh-CN.md'
S1_COMMIT = 'eb5232ce9c43eea566141bccd1081c3dc2021734'
S1_FORMAL = S1_DIR / 'runs/formal-r01'
ANCHORS = ('N_L00_C4146_D-1', 'N_L12_C3621_D-1')
ARMS = ('10', '01', '11')            # E on/L off, E off/L on, both; '00' is the shared clean trajectory
STAGES = ('preflight', 'formal')
PREFLIGHT_ITEM = T1.PREFLIGHT_ITEM   # plan §9: VAR01-f0 x C and the two needles (00 and 11), duplicate path check
LIMITS = {'preflight': {'prefixes': 3, 'last_reads': 3, 'candidate_reads': 6},
          'formal': {'prefixes': 84, 'last_reads': 84, 'candidate_reads': 168}}
MAX_WORKERS = {'preflight': 1, 'formal': 2}


# ---------------------------------------------------------------- arms and masks

def boundary_b(labels):
    """b = position of the last fact token (state after its update); E = 0..b, L = b+1..n-2."""
    facts = [i for i, s in enumerate(labels) if s == 'fact']
    assert facts and facts == list(range(facts[0], facts[-1] + 1)), 'fact segment must be contiguous'
    b = facts[-1]
    assert b < len(labels) - 2, 'L must be non-empty'
    return b


def arm_mask(arm, labels):
    """Needle mask over prefix positions 0..n-2 (the last prompt token never carries the needle)."""
    n_prefix = len(labels) - 1
    b = boundary_b(labels)
    if arm == '11':
        return [True] * n_prefix
    if arm == '10':
        return [i <= b for i in range(n_prefix)]
    if arm == '01':
        return [i > b for i in range(n_prefix)]
    raise ValueError(arm)


def plan_items(stage):
    rows = T1.items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] == PREFLIGHT_ITEM]
        return [{'item_id': r['id'], 'base_id': r['base_id'], 'anchor': None, 'arm': '00'} for r in rows] + \
               [{'item_id': r['id'], 'base_id': r['base_id'], 'anchor': a, 'arm': '11'} for r in rows for a in ANCHORS]
    out = []
    for r in rows:
        out.append({'item_id': r['id'], 'base_id': r['base_id'], 'anchor': None, 'arm': '00'})
        for a in ANCHORS:
            for arm in ARMS:
                out.append({'item_id': r['id'], 'base_id': r['base_id'], 'anchor': a, 'arm': arm})
    return out


def key_of(s):
    return f'{s["item_id"]}__{s["anchor"] or "clean"}__{s["arm"]}'


def plan(stage, worker, n_workers):
    """Units = base scenarios, dealt round-robin; the union over workers is the whole stage."""
    assert 0 <= worker < n_workers
    specs = plan_items(stage)
    bases = list(dict.fromkeys(s['base_id'] for s in specs))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [dict(s, key=key_of(s)) for s in specs if s['base_id'] in mine]


def reference_key(spec):
    """00 and 11 replay the archived II-B (and CFM-S1) trajectory; 10 and 01 are new."""
    if spec['arm'] == '00':
        return f'{spec["item_id"]}__clean'
    if spec['arm'] == '11':
        return f'{spec["item_id"]}__{spec["anchor"]}'
    return None


# ---------------------------------------------------------------- one trajectory (plan §3 timing)

def full_cache(cache, types):
    """Complete M_tau: every KV/recurrent/conv tensor (CPU copies), management state, manifest, and the cache object."""
    tensors = {f'{i}:{field}': L._get(cache.layers[i], field).detach().to('cpu', copy=True) for i, _, field in L.component_tensors(cache, types)}
    other = S2.other_state(cache)
    return {'tensors': tensors, 'manifest': S2.cache_manifest(cache, types), 'other_state': other}


def trajectory(engine, condition, mask, reference, prompt, candidates, layers=T1.OBS_LAYERS, boundary=T1.BOUNDARY):
    """Same path as CFM-S1 trajectory; the needle uses the stage-1 masked injection on prompt[:-1] (all-true for 11).
    Returns (meta, tensors, prefix_cache)."""
    import torch
    model, stop = engine.model, engine.stop_ids
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    types = L.layer_types(model)
    tensors, meta = {}, {}
    with T1.Recorder(model, layers, boundary) as rec:
        if condition['kind'] == 'clean':
            assert mask is None
            cache, decay = L._clean_cache(engine, prefix)
            writes = []
        else:
            assert mask is not None and len(mask) == len(prefix) and any(mask)
            cache, writes, decay = L._build_T(engine, condition, reference, prefix, mask=list(mask))
        tensors['prefix'] = rec.take()
        meta['prefix_manifest'] = S2.cache_manifest(cache, types)
        meta['prefix_other_state_sha256'] = S2.other_state(cache)['sha256']
        tensors['prefix_states'] = T1.obs_states(cache, layers)
        with torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(cache))
        logits = out.logits[0, -1].float()
        assert torch.isfinite(logits).all()
        post = out.past_key_values
        tensors['last'] = rec.take()
        tensors['last_states'] = T1.obs_states(post, layers)
        tensors['first_logits'] = logits.detach().cpu().clone()
        lp = torch.log_softmax(logits, -1)
        top = lp.topk(5)
        meta['first_step'] = {'token': int(logits.argmax()), 'stop_advantage': T1.stop_advantage(logits, stop),
                              'logits_sha256': L.tensor_hash(logits),
                              'top5': [{'token_id': int(t), 'logprob': float(v)} for v, t in zip(top.values, top.indices)]}
        meta['candidates'] = []
        for j, cand in enumerate(candidates):
            assert cand and not any(t in stop for t in cand[:-1])
            branch = copy.deepcopy(post)
            logprobs, hashes = [float(lp[cand[0]])], [L.tensor_hash(logits)]
            with torch.inference_mode():
                for pos, (current, target) in enumerate(zip(cand[:-1], cand[1:])):
                    o = L.forward(model, [current], n + pos, branch)
                    branch = o.past_key_values
                    lg = o.logits[0, -1].float()
                    logprobs.append(float(torch.log_softmax(lg, -1)[target]))
                    hashes.append(L.tensor_hash(lg))
            tensors[f'cand{j}'] = rec.take()
            tensors[f'cand{j}_states'] = T1.obs_states(branch, layers)
            meta['candidates'].append({'token_ids': list(cand), 'token_logprobs': logprobs, 'loglikelihood': sum(logprobs),
                                       'logits_sha256': hashes, 'fed_tokens': len(cand) - 1})
        meta['recorder_calls'] = dict(rec.calls)
    assert S2.cache_manifest(cache, types) == meta['prefix_manifest'], 'prefix cache mutated'
    # Needle audit: one masked write per prefix forward, positions equal to the mask.
    if condition['kind'] != 'clean':
        assert len(writes) == 1 and writes[0]['width'] == len(prefix) and writes[0]['positions'] == sum(mask), writes
    meta['mask'] = list(mask) if mask is not None else None
    meta['needle_positions'] = [i for i, m in enumerate(mask) if m] if mask is not None else []
    meta['write_audit'] = writes
    meta['gate_decay'] = decay
    return meta, tensors, cache


def mtau_roundtrip(engine, cache, path, prompt):
    """M_tau saved as a torch file reloads to the same manifest/management state and the same first-step logits."""
    import torch
    types = L.layer_types(engine.model)
    with path.open('xb') as f:
        torch.save(cache, f)
    loaded = torch.load(path, map_location=next(engine.model.parameters()).device, weights_only=False)
    assert S2.cache_manifest(loaded, types) == S2.cache_manifest(cache, types), 'M_tau reload changed tensors'
    assert S2.other_state(loaded)['sha256'] == S2.other_state(cache)['sha256'], 'M_tau reload changed management state'
    a = L.decode(engine.model, loaded, prompt[-1], len(prompt), engine.stop_ids, max_new_tokens=1, attentions=False)
    b = L.decode(engine.model, cache, prompt[-1], len(prompt), engine.stop_ids, max_new_tokens=1, attentions=False)
    assert a['readouts'][0]['logits_sha256'] == b['readouts'][0]['logits_sha256'], 'M_tau reload changed first-step logits'
    return {'path_sha256': exp.sha(path), 'manifest_sha256': exp.digest(S2.cache_manifest(cache, types)), 'reload_first_step_identical': True}


def s1_repeat_check(spec, tensors, s1_records):
    """Plan §8 fixed repeat path: 00/11 drivers, readouts and exposed states equal the archived CFM-S1 capture bitwise."""
    import torch
    rec = s1_records[reference_key(spec)]
    path = Path(rec['_dir']) / rec['tensor_file']
    assert exp.sha(path) == rec['tensor_sha256'], 'S1 tensor archive changed'
    old = torch.load(path, map_location='cpu', weights_only=False)
    checked = 0
    for phase in ('prefix', 'last', 'cand0', 'cand1'):
        for layer, fields in tensors[phase].items():
            for name, values in fields.items():
                ref = old[phase][layer][name]
                assert len(ref) == len(values) and all(torch.equal(x, y) for x, y in zip(ref, values)), (phase, layer, name)
                checked += len(values)
    for phase in ('prefix_states', 'last_states', 'cand0_states', 'cand1_states'):
        for layer, d in tensors[phase].items():
            assert all(torch.equal(d[k], old[phase][layer][k]) for k in d), (phase, layer)
    assert torch.equal(tensors['first_logits'], old['first_logits'])
    return {'s1_record': rec['spec']['key'], 's1_tensor_sha256': rec['tensor_sha256'], 'tensors_compared': checked, 'status': 'bitwise_identical'}


def load_s1_records():
    out = {}
    v = exp.read(S1_FORMAL / 'verification.json')
    assert v['status'] == 'passed' and v['stage'] == 'formal'
    for w in sorted(S1_FORMAL.glob('worker-*')):
        for p in sorted((w / 'records').glob('*.json')):
            rec = exp.read(p)
            rec['_dir'] = str(w)
            out[rec['spec']['key']] = rec
    assert len(out) == 36
    return out


# ---------------------------------------------------------------- common history (plan §3)

def common_history(t_a, t_b, b, layers=T1.OBS_LAYERS):
    """Pair sharing positions 0..b (01 with 00, 11 with 10): every captured driver and boundary residual at those
    positions must be bitwise equal; then the offline S_b of the two arms is identical by construction."""
    import torch
    out = {}
    for layer in layers:
        pa, pb = t_a['prefix'][str(layer)], t_b['prefix'][str(layer)]
        same = {n: bool(torch.equal(pa[n][0][:b + 1], pb[n][0][:b + 1])) for n in ('q', 'k', 'v', 'g', 'beta', 'qkv_pre', 'z', 'a', 'b')}
        later = {n: bool(torch.equal(pa[n][0][b + 1:], pb[n][0][b + 1:])) for n in ('v', 'g', 'beta')}
        out[str(layer)] = {'positions_0_to_b_bitwise': same, 'after_b_identical': later}
    bnd = {n: bool(torch.equal(t_a['prefix']['boundary'][n][0][:b + 1], t_b['prefix']['boundary'][n][0][:b + 1])) for n in t_a['prefix']['boundary']}
    out['boundary_0_to_b_bitwise'] = bnd
    ok = all(all(v['positions_0_to_b_bitwise'].values()) for k, v in out.items() if k.isdigit()) and all(bnd.values())
    out['status'] = 'certified_bitwise' if ok else 'not_certified'
    return out


# ---------------------------------------------------------------- freeze and authorization

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', PLAN_DOC]
    return own + [p for p in T1.frozen_paths() if p not in own]


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 's1_commit': S1_COMMIT, 'created_at': exp.utc(),
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
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['plan_id'] == PLAN_ID
    assert auth['user_instruction'] and stage in auth['allowed_stages'] and auth['maximum_workers'] == MAX_WORKERS[stage]
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert auth['cpu_receipt_path'] in auth['required_evidence']
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    assert cpu['selftest']['status'] == 'passed'
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


# ---------------------------------------------------------------- execution

def execute(engine, stage, output, receipt, specs):
    from control_engine import exact_pair, encode_text
    import torch
    ref = exp.read(T1.REFERENCE)
    seg = exp.read(T1.SEGMENTS)['items']
    rows = {r['id']: r for r in T1.items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    s1 = load_s1_records()
    references = {}
    for rid in sorted({rows[s['item_id']]['reference_id'] for s in specs}):
        references[rid] = engine.calibrate([contexts[rid]])[0]
        assert references[rid] == ref['calibrations'][rid], f'calibration differs from II-B: {rid}'
        exp.write(output / f'calibrations/{rid}.json', references[rid], immutable=True)
    counts = {'records': 0, 'prefixes': 0, 'last_reads': 0, 'candidate_reads': 0}
    kept = {}
    for spec in specs:
        item = rows[spec['item_id']]
        context, reference = contexts[item['id']], references[item['reference_id']]
        prompt = encode_text(engine.tokenizer, context)
        labels = seg[item['id']]['labels']
        assert seg[item['id']]['prompt_token_sha256'] == exp.digest(prompt) and len(labels) == len(prompt)
        cands = [exact_pair(engine.tokenizer, context, choice)[1] for choice in item['choices']]
        condition = {'id': 'clean', 'kind': 'clean', 'dose': 0.0} if spec['arm'] == '00' else T1.engine_condition(spec['anchor'])
        mask = None if spec['arm'] == '00' else arm_mask(spec['arm'], labels)
        started = time.monotonic()
        meta, tensors, prefix_cache = trajectory(engine, condition, mask, reference, prompt, cands)
        fed = sum(c['fed_tokens'] for c in meta['candidates'])
        T1.check_calls(meta['recorder_calls'], T1.OBS_LAYERS, fed)
        gates = {'recorder_calls': 'passed'}
        rk = reference_key(spec)
        if rk is not None:
            gates['replay'] = T1.replay_check(meta, ref['rows'][rk], reference, prompt)
            gates['s1_repeat'] = s1_repeat_check(spec, tensors, s1)
        else:
            assert exp.digest(reference) == ref['rows'][f'{item["id"]}__clean']['reference_sha256']
        if stage == 'preflight':
            gates['inertness'] = (T1.inertness_gate(engine, condition, reference, prompt, cands, meta) if mask is None
                                  else masked_inertness(engine, condition, mask, reference, prompt, cands, meta))
            gates['capture_consistency'] = T1.capture_consistency(engine, tensors)
        mtau_rel = f'mtau/{spec["key"]}.pt'
        (output / 'mtau').mkdir(exist_ok=True)
        gates['mtau'] = mtau_roundtrip(engine, prefix_cache, output / mtau_rel, prompt)
        receipt['tensor_hashes'][mtau_rel] = gates['mtau']['path_sha256']
        del prefix_cache
        recon = A1.reconstruction_gate(A1.from_capture(tensors, T1.OBS_LAYERS))
        assert recon['status'] == 'passed', ('reconstruction', spec['key'], recon)
        gates['reconstruction'] = {k: {'state_rel_max': max(v['state_rel'].values()), 'out_rel_max': v['out_rel_max']} for k, v in recon['layers'].items()}
        counts['prefixes'] += 1
        counts['last_reads'] += 1
        counts['candidate_reads'] += len(cands)
        tensor_rel = f'tensors/{spec["key"]}.pt'
        tensor_sha = T1.save_tensors(output / tensor_rel, tensors)
        receipt['tensor_hashes'][tensor_rel] = tensor_sha
        b = boundary_b(labels)
        kept[spec['key']] = tensors
        record = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'spec': spec, 'item': item,
                  'context': context, 'prompt_token_ids': prompt, 'prompt_token_sha256': exp.digest(prompt),
                  'reference_sha256': exp.digest(reference), 'condition': condition, 'segments': seg[item['id']], 'b': b,
                  'mask': meta['mask'], 'needle_positions': meta['needle_positions'], 'write_audit': meta['write_audit'],
                  'first_step': meta['first_step'], 'first_step_eos': meta['first_step']['token'] in engine.stop_ids,
                  'candidates': [{'text': t, **c} for t, c in zip(item['choices'], meta['candidates'])],
                  'prefix_manifest': meta['prefix_manifest'], 'prefix_other_state_sha256': meta['prefix_other_state_sha256'],
                  'recorder_calls': meta['recorder_calls'], 'gate_decay': meta['gate_decay'], 'gates': gates,
                  'tensor_file': tensor_rel, 'tensor_sha256': tensor_sha, 'mtau_file': mtau_rel, 'mtau_sha256': gates['mtau']['path_sha256'],
                  'reconstruction': recon, 'seconds': time.monotonic() - started,
                  'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{spec["key"]}.json', record)
        counts['records'] += 1
        # Common-history certification as soon as both members of a same-start pair exist (plan §3).
        _certify_ready(output, item, labels, kept, receipt)
        torch.cuda.empty_cache() if torch.cuda.is_available() else None
    for k, v in counts.items():
        assert v <= LIMITS[stage][k], (k, v)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'records': [s['key'] for s in specs]}, immutable=True)
    return counts


def _certify_ready(output, item, labels, kept, receipt):
    """Write the certification of every same-start pair of this item whose two members are both in memory."""
    b = boundary_b(labels)
    clean = kept.get(f'{item["id"]}__clean__00')
    for a in ANCHORS:
        pairs = (('01', clean, kept.get(f'{item["id"]}__{a}__01')), ('11v10', kept.get(f'{item["id"]}__{a}__10'), kept.get(f'{item["id"]}__{a}__11')))
        for name, ta, tb in pairs:
            rel = f'certification/{item["id"]}__{a}__{name}.json'
            if ta is None or tb is None or (output / rel).exists():
                continue
            cert = common_history(ta, tb, b)
            exp.write(output / rel, cert, immutable=True)
            receipt['record_hashes'][rel] = exp.sha(output / rel)
            # Plan §3: a pair that cannot be certified stops the same-start conclusions; the run stops here.
            assert cert['status'] == 'certified_bitwise', (rel, cert)
    done = [k for k in kept if k.startswith(item['id'] + '__')]
    if len(done) == 1 + len(ANCHORS) * len(ARMS):
        for k in done:
            del kept[k]


def masked_inertness(engine, condition, mask, reference, prompt, cands, meta):
    """Masked-needle trajectory without any recorder: identical cache manifest, candidate floats and first-step logits."""
    model = engine.model
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    types = L.layer_types(model)
    cache, _, _ = L._build_T(engine, condition, reference, prefix, mask=list(mask))
    assert S2.cache_manifest(cache, types) == meta['prefix_manifest'], 'recorder changed the prefix cache'
    for j, cand in enumerate(cands):
        s = L.score(model, cache, last, n, cand)
        assert s['token_logprobs'] == meta['candidates'][j]['token_logprobs']
    d = L.decode(model, cache, last, n, engine.stop_ids, max_new_tokens=1, attentions=False)
    assert d['readouts'][0]['logits_sha256'] == meta['first_step']['logits_sha256']
    return 'passed'


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    assert 0 <= worker < n_workers
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-s2-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    neighbours = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid,used_memory', '--format=csv,noheader,nounits'], text=True).strip()
    assert free_mib >= T1.MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'tensor_hashes': {},
               'gpu_free_mib_at_start': free_mib, 'coresident_processes_at_start': neighbours.splitlines()}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        receipt['load_seconds'] = time.monotonic() - started
        specs = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', specs, immutable=True)
        receipt['plan_sha256'] = exp.sha(output / 'plan.json')
        receipt['summary'] = execute(engine, stage, output, receipt, specs)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        receipt.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'receipt.json', receipt)
    return receipt


def verify_worker(path):
    path = Path(path)
    r = exp.read(path / 'receipt.json')
    assert r['status'] == 'completed'
    assert r['freeze_sha256'] == exp.sha(HERE / r['freeze_path'])
    check_freeze(HERE / r['freeze_path'])
    assert r['authorization_sha256'] == exp.sha(path / 'authorization.json')
    auth = exp.read(path / 'authorization.json')
    execution = exp.read(path / 'execution.json')
    for key in ('stage', 'worker', 'n_workers', 'gpu', 'pid', 'started_at', 'freeze_sha256', 'authorization_sha256'):
        assert execution[key] == r[key], key
    assert r['n_workers'] == auth['maximum_workers'] and r['gpu'] == r['worker'] % 2
    specs = exp.read(path / 'plan.json')
    assert specs == plan(r['stage'], r['worker'], r['n_workers'])
    expected = {f'records/{s["key"]}.json' for s in specs}
    assert {k for k in r['record_hashes'] if k.startswith('records/')} == expected
    assert {str(p.relative_to(path)) for p in (path / 'records').glob('*.json')} == expected
    assert set(r['tensor_hashes']) == {f'tensors/{s["key"]}.pt' for s in specs} | {f'mtau/{s["key"]}.pt' for s in specs}
    for rel, digest in {**r['record_hashes'], **r['tensor_hashes']}.items():
        assert exp.sha(path / rel) == digest, rel
    certs = [k for k in r['record_hashes'] if k.startswith('certification/')]
    if r['stage'] == 'formal':
        items = {s['item_id'] for s in specs}
        assert len(certs) == len(items) * len(ANCHORS) * 2, len(certs)
        assert all(exp.read(path / c)['status'] == 'certified_bitwise' for c in certs)
    for rel in expected:
        rec = exp.read(path / rel)
        assert rec['freeze_sha256'] == r['freeze_sha256'] and rec['tensor_sha256'] == r['tensor_hashes'][rec['tensor_file']]
        assert rec['reconstruction']['status'] == 'passed'
        if reference_key(rec['spec']) is not None:
            assert rec['gates']['replay']['candidate_token_logprobs'] == 'identical'
            assert rec['gates']['s1_repeat']['status'] == 'bitwise_identical'
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'records': len(expected), 'certifications': len(certs),
            'freeze_sha256': r['freeze_sha256'], **r['summary'], 'wall_seconds': r['wall_seconds']}


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
        for w in range(auth['maximum_workers']):
            log = (output / f'worker-{w}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 's2_trace.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            for w, p in list(pending.items()):
                code = p.poll()
                if code is None:
                    continue
                (output / f'worker-{w}').mkdir(exist_ok=True)
                exp.write(output / f'worker-{w}/exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
                controller['workers'][str(w)]['returncode'] = code
                failure |= code != 0
                del pending[w]
            exp.write(output / 'controller.json', controller)
            if failure:
                for p in pending.values():
                    p.terminate()
            if pending:
                time.sleep(2)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        totals = {k: sum(w[k] for w in results) for k in ('records', 'prefixes', 'last_reads', 'candidate_reads', 'certifications')}
        for k, v in LIMITS[stage].items():
            assert totals[k] <= v, (k, totals[k])
        if stage == 'formal':
            assert totals['prefixes'] == LIMITS['formal']['prefixes'] and totals['certifications'] == 48, totals
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, **totals, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for w, p in procs.items():
            if p.poll() is None:
                p.terminate()
                code = p.wait()
                d = output / f'worker-{w}'
                d.mkdir(exist_ok=True)
                if not (d / 'exit.json').exists():
                    exp.write(d / 'exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
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
            q.add_argument('--worker', required=True, type=int, choices=range(2))
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k not in ('record_hashes', 'tensor_hashes')}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
