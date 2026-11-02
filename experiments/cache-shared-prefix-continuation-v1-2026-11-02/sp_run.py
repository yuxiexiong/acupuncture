"""SP-01: shared-first-token panel (three same-letter codes per record, f0/f1 share the code set and swap the target) —
bounded greedy continuation (plan docs/cache-shared-prefix-continuation-plan-v1-2026-11-02.zh-CN.md; CONTRACT.zh-CN.md r01).

Per input: C_nat, C_noEOS1 (shared).  Per direction (N4146, N1210, R0, C1343): T_nat, T_noEOS1, T_shared (first output forced
to the shared first token q_shared, fixed from the tokenizer before any output), T_F (deep G-layer conv restored to C at start).
32 new tokens max (forced token and stop token included); greedy; stop set {248044, 248046}; no needle during generation.
python fc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
NR_DIR = HERE.parent / 'cache-native-complement-recovery-v1-2026-11-02'
FC_DIR = HERE.parent / 'cache-first-token-continuation-v1-2026-11-02'
sys.path.insert(0, str(NR_DIR))
sys.path.insert(0, str(FC_DIR))
sys.path.insert(0, str(HERE))
import nr_run as NRR  # noqa: E402  (frozen NR-01 runner: restore(), cache hashing, model chain)
import fc_core as K  # noqa: E402  (frozen FC-01 classifier)

B3R, V, P, PK, X = NRR.B3R, NRR.V, NRR.P, NRR.PK, NRR.X
CF, CFK, LR, B = NRR.CF, NRR.CFK, NRR.LR, NRR.B
F, L, T1, exp = NRR.F, NRR.L, NRR.T1, NRR.exp

PLAN_ID = 'SP-01-SHARED-PREFIX-CONTINUATION-v1'
PLAN_DOCS = [REPO / 'docs/cache-shared-prefix-continuation-plan-v1-2026-11-02.zh-CN.md']
INPUTS = HERE / 'data/inputs-r01.json'
NR_FORMAL = NR_DIR / 'runs/formal-r01'
B3_FORMAL = NRR.B3_FORMAL
XC_FORMAL = NRR.XC_FORMAL
SK_FORMAL = NRR.SK_FORMAL
SPLIT = 13
DIRECTIONS = NRR.DIRECTIONS
PREFLIGHT_ITEMS = ('SP01-f0', 'SP01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
MAX_NEW = 32
STOP = (248044, 248046)
LIMITS = {'preflight': {'formations': 12, 'trajectories': 40, 'decode_forwards': 1280, 'calibrations': 1},
          'formal': {'formations': 60, 'trajectories': 216, 'decode_forwards': 6912, 'calibrations': 6}}
STORAGE_LIMIT = 8 * 2 ** 30
T_ARMS = ('T_nat', 'T_noEOS1', 'T_shared', 'T_F')
OFF_DIR = 'N_L00_C4146_D-1'
comp_sha = NRR.comp_sha


def items():
    return exp.read(INPUTS)['items']


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def shared_tokens(tok, item):
    """q_shared = common first token of the three codes written without a leading space; second tokens pairwise distinct."""
    codes = [item['target']] + item['distractors']
    enc = [tok.encode(c, add_special_tokens=False) for c in codes]
    assert len({e[0] for e in enc}) == 1 and len({e[1] for e in enc}) == 3, ('panel tokenization', item['id'], enc)
    return enc[0][0], enc[0][1], [e[1] for e in enc[1:]]


def conditions():
    return NRR.conditions()


def b3_record(item_id):
    return NRR.b3_record(item_id)


def nr_record(item_id):
    for w in sorted(NR_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'NR record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


ALLK = ('recurrent', 'kv', 'conv')


def generate(engine, cache0, last, n, mode, q0, types, counts, watch=None):
    """Greedy continuation from an independent clone.  mode: 'nat' | 'noeos1' (first-step stop set masked for the choice only)
    | 'q0' (first output forced to q0).  The chosen token is what is fed to the next step."""
    import torch
    model = engine.model
    cache = copy.deepcopy(cache0)
    ids, steps = [], []
    tok_in, pos = last, n - 1
    first = {}
    for step in range(MAX_NEW):
        with torch.inference_mode():
            out = L.forward(model, [tok_in], pos, cache)
        counts['decode_forwards'] += 1
        z = out.logits[0, -1].float()
        assert torch.isfinite(z).all()
        cache = out.past_key_values
        masked = forced = False
        if step == 0:
            first = {'logits_sha256': F.th(z), 'argmax': int(z.argmax()), 'cache_sha256': comp_sha(cache, types, ALLK, 0)}
            if mode == 'noeos1':
                zz = z.clone()
                zz[list(STOP)] = -float('inf')
                t, masked = int(zz.argmax()), True
            elif mode == 'q0':
                t, forced = int(q0), True
            else:
                t = int(z.argmax())
        else:
            t = int(z.argmax())
            if step == 1 and watch:
                first['step2'] = {str(w): float(z[w]) for w in watch}
        ids.append(t)
        steps.append({'token': t, 'masked': masked, 'forced': forced})
        if t in STOP:
            break
        tok_in, pos = t, pos + 1
    reason = 'stop' if ids[-1] in STOP else 'budget'
    return {'ids': ids, 'steps': steps, 'termination': reason, 'first': first, 'final_cache_sha256': comp_sha(cache, types, ALLK, 0)}


def run_item(engine, item, context, calib, conds, output, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    tok = engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    seg = PK.label_tokens(tok, context, item['record'], encode_text)
    assert not seg['straddling_tokens']
    prompt, b = seg['ids'], seg['b']
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'trajectories': 0, 'decode_forwards': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    traj, gates, audits = {}, {}, {}
    ans, others = K.answer_and_distractors(item['record'])
    assert ans == item['target'] and sorted(others) == sorted(item['distractors']), 'panel answer extraction'
    q_shared, t2, d2 = shared_tokens(tok, item)
    watch = [t2] + d2
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    allC = comp_sha(cC, types, ALLK, 0)

    def run(name, cache, mode, q0=None):
        F.assert_no_hooks(model)
        r = generate(engine, cache, last, n, mode, q0, types, counts, watch)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        return r

    c_nat = run('C_nat', cC, 'nat')
    c_first = c_nat['ids'][0]
    c_no = run('C_noEOS1', cC, 'noeos1')
    if c_first not in STOP:
        assert c_no['ids'] == c_nat['ids'] and c_no['final_cache_sha256'] == c_nat['final_cache_sha256'], 'C_noEOS1 != C_nat'
        gates['C_equivalence'] = 'C_nat first token is not a stop token; C_noEOS1 == C_nat token-by-token and final cache hash'
    else:
        gates['C_equivalence'] = 'not applicable: C_nat stopped at the first step (baseline observation)'
    if preflight:
        c_sh = run('C_shared', cC, 'q0', q_shared)
        if c_first == q_shared:
            assert c_sh['ids'] == c_nat['ids'] and c_sh['final_cache_sha256'] == c_nat['final_cache_sha256'], 'C_shared != C_nat'
            gates['C_shared_equivalence'] = 'C_nat first token == q_shared; C_shared == C_nat token-by-token and final cache hash'
        else:
            gates['C_shared_equivalence'] = 'not applicable: C_nat first token != q_shared (baseline observation, recorded)'
    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(window)
        allT = comp_sha(cT, types, ALLK, 0)
        k = lambda a: f'{a}|{d}'   # noqa: E731
        cF = NRR.restore(cT, cC, types, '010')
        hF = {'X': NRR.comp_sha_range(cF, types, ALLK, 0, SPLIT), 'F': comp_sha(cF, types, ('conv',)),
              'S': comp_sha(cF, types, ('recurrent',)), 'KV': comp_sha(cF, types, ('kv',))}
        assert hF == {'X': NRR.comp_sha_range(cT, types, ALLK, 0, SPLIT), 'F': comp_sha(cC, types, ('conv',)),
                      'S': comp_sha(cT, types, ('recurrent',)), 'KV': comp_sha(cT, types, ('kv',))}, ('T_F assembly', d)
        tn = run(k('T_nat'), cT, 'nat')
        te = run(k('T_noEOS1'), cT, 'noeos1')
        ts = run(k('T_shared'), cT, 'q0', q_shared)
        run(k('T_F'), cF, 'nat')
        for r in (te, ts):
            assert r['first']['logits_sha256'] == tn['first']['logits_sha256'] and r['first']['cache_sha256'] == tn['first']['cache_sha256'], ('T arms first step differ', d)
        assert te['steps'][0]['masked'] and ts['steps'][0]['forced'] and ts['ids'][0] == q_shared
        assert all(not s_['masked'] and not s_['forced'] for r in (te, ts) for s_ in r['steps'][1:]), 'mask/force beyond first step'
        assert comp_sha(cT, types, ALLK, 0) == allT and comp_sha(cC, types, ALLK, 0) == allC, ('donor changed', d)
        if preflight and item['id'] == PREFLIGHT_ITEMS[0] and d == OFF_DIR:
            cC2 = P.form(engine, base, prefix, window, None, calib)
            cT2 = P.form(engine, base, prefix, window, cond, calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(window)
            assert comp_sha(cC2, types, ALLK, 0) == allC and comp_sha(cT2, types, ALLK, 0) == allT, 'rebuild differs'
            r1 = run('REBUILD:C_nat', cC2, 'nat')
            r2 = run(f'REBUILD:T_nat|{d}', cT2, 'nat')
            assert r1['ids'] == c_nat['ids'] and r1['final_cache_sha256'] == c_nat['final_cache_sha256'], 'rebuild C trajectory differs'
            assert r2['ids'] == tn['ids'] and r2['final_cache_sha256'] == tn['final_cache_sha256'], 'rebuild T trajectory differs'
            gates['rebuild'] = 'C and T(4146) rebuilt: caches hash-equal; natural trajectories identical token-by-token and final cache'
            del cC2, cT2
        del cT, cF
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['first_step'] = 'T_nat / T_noEOS1 / T_shared share first-step logits and updated cache'
    gates['q_shared'] = 'q_shared = common unspaced first token of the three codes; second tokens pairwise distinct'
    gates['mask_force'] = 'mask / force applied only at the first step; forced token fed to the next step'
    gates['assembly'] = 'T_F: shallow, S, KV from T, deep conv from C (hashes); donors unchanged; no hooks during generation'
    body = {'answer': ans, 'distractors': others, 'q_shared': q_shared, 'q_shared_text': tok.decode([q_shared]),
            'second_tokens': {'target': t2, 'distractors': d2}, 'c_first_token': c_first, 'c_first_is_shared': c_first == q_shared,
            'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits, 'trajectories': traj,
            'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, {}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', INPUTS, FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + [p for p in B3R.frozen_paths() if p not in own]


def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'created_at': exp.utc(),
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
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    totals = {'formations': 0, 'trajectories': 0, 'decode_forwards': 0, 'calibrations': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    calib = {}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            F.assert_no_hooks(engine.model)
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            totals['calibrations'] += 1
            pre = HERE / 'runs/preflight-r01/worker-0' / f'calibrations/{rid}.json'
            if stage == 'formal' and pre.exists():
                assert calib[rid] == exp.read(pre), ('calibration differs from preflight', rid)
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        started = time.monotonic()
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, output, preflight=(stage == 'preflight'))
        for k in ('formations', 'trajectories', 'decode_forwards', 'prefix_prefills', 'formation_token_forwards'):
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item, **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        exp.write(output / 'receipt.json', receipt)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals,
                                               'bytes': receipt['bytes']}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-sp-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    assert free_mib >= T1.MIN_FREE_MIB, f'Only {free_mib} MiB free on GPU {gpu}'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'tensor_hashes': {}, 'gpu_free_mib_at_start': free_mib}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine
    import torch
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units, gpu)
        receipt['integrity'] = engine.verify_unchanged()
        receipt['peak_memory_bytes'] = int(torch.cuda.max_memory_allocated(gpu))
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
    units = exp.read(path / 'plan.json')
    assert units == plan(r['stage'], r['worker'], r['n_workers'])
    assert set(r['record_hashes']) == {f'records/{u["key"]}.json' for u in units}
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        want = {'C_nat', 'C_noEOS1'} | {f'{a}|{d}' for a in T_ARMS for d in DIRECTIONS}
        first = r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]
        if r['stage'] == 'preflight':
            want |= {'C_shared'}
        if first:
            want |= {'REBUILD:C_nat', f'REBUILD:T_nat|{OFF_DIR}'}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        for g in ('write', 'first_step', 'q_shared', 'C_equivalence', 'mask_force', 'assembly') + \
                ((('C_shared_equivalence',) if r['stage'] == 'preflight' else ()) + (('rebuild',) if first else ())):
            assert rec['gates'][g], g
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(units), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes'], 'peak_memory_bytes': r.get('peak_memory_bytes')}


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
            cmd = [sys.executable, '-u', str(HERE / 'sp_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
                time.sleep(3)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        units = sum(x['units'] for x in results)
        calls = {k: sum(x['model_calls'][k] for x in results) for k in results[0]['model_calls']}
        check_limits(calls, stage)
        assert units == (12 if stage == 'formal' else len(PREFLIGHT_ITEMS)), units
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': units, 'model_calls': calls, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for w, p in procs.items():
            if p.poll() is None:
                p.terminate()
                p.wait()
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
