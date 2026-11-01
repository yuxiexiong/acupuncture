"""SK-01: inside the deep history (layers 13-31), does the history effect at the intervened entry follow the recurrent
states S, the old attention KV, or both; and does it correspond to recovery in the full native T background?
CONTRACT.zh-CN.md r01; plans docs/cache-sk-history-action-plan-v1/v2-2026-11-02.zh-CN.md.

Per input: C_native.  Per direction (N4146, N1210, R0, C1343): P = T_native (x_T);
main matrix (entry x_T, shallow C, deep conv C):  SK00 (S C, KV C; == EH-XC X10), SK10 (S T), SK01 (KV T), SK11 (S T, KV T; == XH11);
native recovery (from full T, natural entry == x_T):  P_S0 (deep S <- C), P_K0 (deep old KV <- C), P_SK0 (both <- C).
python sk_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import hashlib
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
B3_DIR = HERE.parent / 'cache-b3-fixed-head-trace-v1-2026-11-01'
sys.path.insert(0, str(B3_DIR))
sys.path.insert(0, str(HERE))
import b3_run as B3R  # noqa: E402  (frozen B3 runner: C2 chain, plan, conditions, assets)

V, P, PK, X = B3R.V, B3R.P, B3R.PK, B3R.X
CF, CFK, LR, B = B3R.CF, B3R.CFK, B3R.LR, B3R.B
F, L, T1, exp = B3R.F, B3R.L, B3R.T1, B3R.exp

PLAN_ID = 'SK-01-S-KV-HISTORY-v1'
PLAN_DOCS = [REPO / 'docs/cache-sk-history-action-plan-v1-2026-11-02.zh-CN.md', REPO / 'docs/cache-sk-history-action-plan-v2-2026-11-02.zh-CN.md']
XC_FORMAL = HERE.parent / 'cache-eh-cross-channel-v1-2026-11-02/runs/formal-r01'
B3_FORMAL = B3_DIR / 'runs/formal-r01'
SPLIT = 13
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'N_L00_C1343_D-1')
PREFLIGHT_ITEMS = ('P01-f0', 'P01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 12, 'scores': 68, 'calibrations': 1},
          'formal': {'formations': 60, 'scores': 396, 'calibrations': 6}}
STORAGE_LIMIT = 8 * 2 ** 30
ARMS = ('SK00', 'SK10', 'SK01', 'SK11', 'P_S0', 'P_K0', 'P_SK0')
OFF_DIR = 'N_L00_C4146_D-1'


def b3_record(item_id):
    for w in sorted(B3_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'B3 record hash'
            return exp.read(w / rel), r['gpu']
    raise KeyError(item_id)


def xc_record(item_id):
    for w in sorted(XC_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'EH-XC record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def conditions():
    dirs = X.load_directions()
    by = {n['id']: n for n in X.needles()}
    return {d: X.engine_condition(by[d], dirs) for d in DIRECTIONS}


def tensor_bytes_sha(ts):
    h = hashlib.sha256()
    for t in ts:
        h.update(t.detach().contiguous().cpu().view(-1).view(__import__('torch').uint8).numpy().tobytes())
    return h.hexdigest()


def comp_sha(cache, types, kinds, lo=SPLIT):
    return comp_sha_range(cache, types, kinds, lo, 10 ** 9)


def comp_sha_range(cache, types, kinds, lo, hi):
    rows = [(i, f) for i, k, f in L.component_tensors(cache, types) if lo <= i < hi and k in kinds]
    return tensor_bytes_sha([L._get(cache.layers[i], f) for i, f in rows])


def assemble(base, donor, types, kinds, lo=SPLIT):
    """Deep copy of base; for layers >= lo, the cache components of the given kinds are taken (cloned) from donor."""
    import copy
    c = copy.deepcopy(base)
    for i, k, f in L.component_tensors(c, types):
        if i >= lo and k in kinds:
            L._set(c.layers[i], f, L._get(donor.layers[i], f).clone())
    return c


def run_item(engine, item, context, calib, conds, b3_rec, xc_rec, output, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    deep_attn = [i for i, t in enumerate(types) if i >= SPLIT and t == 'full_attention']
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and deep_attn == [15, 19, 23, 27, 31], ('layer lists', G, deep_attn)
    seg = PK.label_tokens(engine.tokenizer, context, item['record'], encode_text)
    assert not seg['straddling_tokens']
    prompt, b = seg['ids'], seg['b']
    assert exp.digest(prompt) == b3_rec['prompt_token_sha256'], 'prompt tokens differ from B3'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'scores': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    res, logits, gates, audits, cache_hashes, saved = {}, {}, {}, {}, {}, {'final_h': {}, 'x_T': {}}
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    stop = list(engine.stop_ids)
    ALLK = ('recurrent', 'kv', 'conv')

    def hashes(c):
        return {'S': comp_sha(c, types, ('recurrent',)), 'KV': comp_sha(c, types, ('kv',)), 'conv': comp_sha(c, types, ('conv',)),
                'shallow': comp_sha_range(c, types, ALLK, 0, SPLIT)}
    hC = hashes(cC)
    allC = comp_sha(cC, types, ALLK, 0)

    def xc_sha(key):
        return xc_rec['cells'][key]['score']['logits_sha256']

    def score(rec, cnt, cache, key, expected, entry=None):
        cnt.key = key
        before = entry.hits if entry else 0
        r, z = B.score(engine, cache, last, n, rec, key, stop, expected)
        cnt.key = None
        counts['scores'] += 1
        assert cnt.hits.get(key, {}) == {i: 1 for i in G} and cnt.chunk.get(key, 0) == 0, ('kernel hits', key)
        if entry:
            assert entry.hits - before == 1, ('entry hits', key)
        assert torch.isfinite(z).all(), ('non-finite logits', key)
        logits[key] = z
        res[key] = {'score': r}
        saved['final_h'][key] = rec.extra[key]['final:h'].detach().cpu()
        return r

    rec0, cnt0 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
    with ExitStack() as st:
        st.enter_context(rec0)
        st.enter_context(cnt0)
        rc = score(rec0, cnt0, cC, 'C_native', F.hook_counts(model))
    a = rc['nonstop_winner']
    assert a == b3_rec['a_token'] and rc['logits_sha256'] == xc_sha('C_native'), 'C_native replay vs EH-XC'
    saved['x_C'] = rec0.extra['C_native'][f'{SPLIT}:in'].detach().cpu()

    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(window)
        hT = hashes(cT)
        allT = comp_sha(cT, types, ALLK, 0)
        k = lambda name: f'{name}|{d}'   # noqa: E731
        rec1, cnt1 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            st.enter_context(rec1)
            st.enter_context(cnt1)
            score(rec1, cnt1, cT, k('T_native'), F.hook_counts(model))
        assert res[k('T_native')]['score']['logits_sha256'] == xc_sha(k('T_native')), ('T_native vs EH-XC', d)
        x_t = rec1.extra[k('T_native')][f'{SPLIT}:in'].detach().clone()
        saved['x_T'][d] = x_t.cpu()
        cells = {'SK00': assemble(cC, cT, types, ()), 'SK10': assemble(cC, cT, types, ('recurrent',)),
                 'SK01': assemble(cC, cT, types, ('kv',)), 'SK11': assemble(cC, cT, types, ('recurrent', 'kv')),
                 'P_S0': assemble(cT, cC, types, ('recurrent',)), 'P_K0': assemble(cT, cC, types, ('kv',)),
                 'P_SK0': assemble(cT, cC, types, ('recurrent', 'kv'))}
        expect = {'SK00': (hC, hC, hC, hC), 'SK10': (hT, hC, hC, hC), 'SK01': (hC, hT, hC, hC), 'SK11': (hT, hT, hC, hC),
                  'P_S0': (hC, hT, hT, hT), 'P_K0': (hT, hC, hT, hT), 'P_SK0': (hC, hC, hT, hT)}
        hh = {}
        for name, c in cells.items():
            h = hashes(c)
            eS, eK, eConv, eSh = expect[name]
            assert (h['S'], h['KV'], h['conv'], h['shallow']) == (eS['S'], eK['KV'], eConv['conv'], eSh['shallow']), ('assembly', name, d)
            hh[name] = h
        rec2, cnt2 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:                                                          # native recovery arms: natural entry
            st.enter_context(rec2)
            st.enter_context(cnt2)
            exp2 = F.hook_counts(model)
            for name in ('P_S0', 'P_K0', 'P_SK0'):
                score(rec2, cnt2, cells[name], k(name), exp2)
        for name in ('P_S0', 'P_K0', 'P_SK0'):
            assert torch.equal(rec2.extra[k(name)][f'{SPLIT}:in'], x_t), ('native arm entry != x_T', name, d)
        rec3, cnt3 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:                                                          # main matrix: entry x_T
            e = st.enter_context(LR.Entry(model, x_t))
            st.enter_context(rec3)
            st.enter_context(cnt3)
            exp3 = F.hook_counts(model)
            for name in ('SK00', 'SK10', 'SK01', 'SK11'):
                score(rec3, cnt3, cells[name], k(name), exp3, e)
        for name in ('SK00', 'SK10', 'SK01', 'SK11'):
            assert torch.equal(rec3.extra[k(name)][f'{SPLIT}:in'].cpu(), x_t.cpu()), ('entry != x_T', name, d)
        assert res[k('SK00')]['score']['logits_sha256'] == xc_sha(k('X10')), ('SK00 != EH-XC X10', d)
        assert res[k('SK11')]['score']['logits_sha256'] == xc_sha(k('XH11')), ('SK11 != EH-XC XH11', d)
        assert comp_sha(cT, types, ALLK, 0) == allT and comp_sha(cC, types, ALLK, 0) == allC, ('donor changed', d)
        cache_hashes[d] = {'T': hT, **hh}
        if preflight and item['id'] == PREFLIGHT_ITEMS[0] and d == OFF_DIR:
            cC2 = P.form(engine, base, prefix, window, None, calib)
            cT2 = P.form(engine, base, prefix, window, cond, calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(window)
            assert comp_sha(cC2, types, ALLK, 0) == allC and comp_sha(cT2, types, ALLK, 0) == allT, 'rebuild differs'
            off = B._Off()
            for key, cache in (('OFF:C_native', cC2), (f'OFF:T_native|{d}', cT2)):
                r, z = B.score(engine, cache, last, n, off, key, stop, F.hook_counts(model))
                counts['scores'] += 1
                ref = 'C_native' if key == 'OFF:C_native' else k('T_native')
                assert r['logits_sha256'] == res[ref]['score']['logits_sha256'], ('recorder on/off', key)
                res[key] = {'score': r}
            gates['recorder_off'] = 'C and T(4146) rebuilt, scored without recorders: logits bitwise equal; rebuilt caches hash-equal'
            del cC2, cT2
        del cT, rec1, rec2, rec3, cnt1, cnt2, cnt3, cells
    gates['calibration'] = 'scenario f0 calibration (in process) equals the B3 record exactly'
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'C_native, T_native, SK00 (== X10), SK11 (== XH11) logits bitwise == EH-XC'
    gates['entry'] = 'main matrix entry == x_T (hook once); native recovery arms natural entry == x_T'
    gates['assembly'] = 'deep S, deep KV, deep conv and shallow hashed separately; every cell matches its source table; donors unchanged'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never; no formation hook during scoring (B.score)'
    for key, z in logits.items():
        res[key]['readout'] = CFK.readout(z, a)
    body = {'a_token': a, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits,
            'cells': res, 'cache_hashes': cache_hashes, 'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, {'logits': logits, 'saved': saved}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    return own + b3 + xc + [p for p in B3R.frozen_paths() if p not in own]


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
    totals = {'formations': 0, 'scores': 0, 'calibrations': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    calib = {}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        b3_rec, b3_gpu = b3_record(item['id'])
        assert b3_gpu == gpu, ('GPU assignment differs from B3', item['id'], b3_gpu, gpu)
        if rid not in calib:
            F.assert_no_hooks(engine.model)
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            totals['calibrations'] += 1
            assert calib[rid] == b3_rec['calibration'], ('calibration differs from B3', rid)
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        started = time.monotonic()
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, b3_rec, xc_record(item['id']), output,
                                 preflight=(stage == 'preflight'))
        for k in ('formations', 'scores', 'prefix_prefills', 'formation_token_forwards'):
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
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


def items():
    return V.items()


def plan(stage, worker, n_workers):
    if stage == 'preflight':                     # contract §6: preflight = first input only, all 14 needles
        rows = [r for r in items() if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
        return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows]
    return V.plan(stage, worker, n_workers)


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-sk-worker{worker}.lock', 'w')
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
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in list(r['tensor_hashes'].items()) + list(r['record_hashes'].items()):
        assert exp.sha(path / rel) == digest, rel
    want = {'C_native'} | {f'T_native|{d}' for d in DIRECTIONS} | {f'{a}|{d}' for a in ARMS for d in DIRECTIONS}
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        w = set(want)
        first = r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]
        if first:
            w |= {'OFF:C_native', f'OFF:T_native|{OFF_DIR}'}
        for g in ('calibration', 'write', 'replay', 'entry', 'assembly', 'kernel') + (('recorder_off',) if first else ()):
            assert rec['gates'][g], g
        assert set(rec['cells']) == w, set(rec['cells']) ^ w
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
            cmd = [sys.executable, '-u', str(HERE / 'sk_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
