"""EH-XC: is the EH relation (deep history carries most of e1, entry amplifies it) present for other native L0 channels
and for random directions?  Same 2x2 (entry x, deep history H = layers 13-31 recurrent S + attention KV; conv histories C)
for 14 needles: 8 validation channels, anchors 1210/4146, random R0-R3.  CONTRACT.zh-CN.md r01 (reviewed, c751914);
plan docs/cache-eh-cross-channel-plan-v1-2026-11-02.zh-CN.md.

Cells per input x needle: 00 = C_native (shared); P = T_native; X10 = all-C cache + entry x_T; H01 = deep T S/KV, conv C,
natural entry (== x_C); XH11 = deep T S/KV, conv C, entry x_T.  EH directions replay EH bitwise.
python eh_xc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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

PLAN_ID = 'EH-XC-CROSS-CHANNEL-v1'
PLAN_DOCS = [REPO / 'docs/cache-eh-cross-channel-plan-v1-2026-11-02.zh-CN.md']
EH_FORMAL = HERE.parent / 'cache-entry-history-v1-2026-11-02/runs/formal-r01'
B3_FORMAL = B3_DIR / 'runs/formal-r01'
SPLIT = 13
EH_DIRS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
CHANNELS = (1343, 2191, 3152, 3959, 6137, 6547, 6616, 8215)
VALIDATION = tuple(f'N_L00_C{c}_D-1' for c in CHANNELS)
RANDOM = ('R0_L00_D-1', 'R1_L00_D-1', 'R2_L00_D-1', 'R3_L00_D-1')
ANCHORS = ('N_L00_C1210_D-1', 'N_L00_C4146_D-1')
DIRECTIONS = EH_DIRS + ('R2_L00_D-1', 'R3_L00_D-1') + VALIDATION          # EH directions first (replay gates early)
PREFLIGHT_ITEMS = ('P01-f0',)
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 17, 'scores': 59, 'calibrations': 1},
          'formal': {'formations': 180, 'scores': 684, 'calibrations': 6}}
STORAGE_LIMIT = 8 * 2 ** 30
ARMS = ('X10', 'H01', 'XH11')
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


def eh_record(item_id):
    for w in sorted(EH_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'EH record hash'
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
    rows = [(i, f) for i, k, f in L.component_tensors(cache, types) if i >= lo and k in kinds]
    return tensor_bytes_sha([L._get(cache.layers[i], f) for i, f in rows])


def tv(z1, z2):
    import torch
    return float(0.5 * (torch.softmax(z1.double(), -1) - torch.softmax(z2.double(), -1)).abs().sum())


def run_item(engine, item, context, calib, conds, b3_rec, eh_rec, output, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
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
    H_KINDS, CONV = ('recurrent', 'kv'), ('conv',)
    hC = {'H': comp_sha(cC, types, H_KINDS), 'conv': comp_sha(cC, types, CONV), 'all': comp_sha(cC, types, ('recurrent', 'kv', 'conv'), 0)}

    def eh_sha(key):
        return eh_rec['cells'][key]['score']['logits_sha256']

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
    assert a == b3_rec['a_token'] and rc['logits_sha256'] == b3_rec['cells']['C_native']['score']['logits_sha256'] == eh_sha('C_native'), 'C_native replay'
    x_c = rec0.extra['C_native'][f'{SPLIT}:in'].detach().clone()
    saved['x_C'] = x_c.cpu()
    fC = {l: L._get(cC.layers[l], 'conv_states') for l in G}

    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(window)
        hT = {'H': comp_sha(cT, types, H_KINDS), 'conv': comp_sha(cT, types, CONV), 'all': comp_sha(cT, types, ('recurrent', 'kv', 'conv'), 0)}
        k = lambda name: f'{name}|{d}'   # noqa: E731
        rec1, cnt1 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            st.enter_context(rec1)
            st.enter_context(cnt1)
            score(rec1, cnt1, cT, k('T_native'), F.hook_counts(model))
        x_t = rec1.extra[k('T_native')][f'{SPLIT}:in'].detach().clone()
        saved['x_T'][d] = x_t.cpu()
        c_h = P.n_cache(cT, cC, types, {l: fC[l] for l in G})                       # deep T S/KV, conv C, shallow C
        c_x = P.n_cache(cC, cC, types)                                               # all C
        hh = {'H01': {'H': comp_sha(c_h, types, H_KINDS), 'conv': comp_sha(c_h, types, CONV)},
              'X10': {'H': comp_sha(c_x, types, H_KINDS), 'conv': comp_sha(c_x, types, CONV)}}
        assert hh['H01']['H'] == hT['H'] and hh['H01']['conv'] == hC['conv'], ('H01 assembly', d)
        assert hh['X10']['H'] == hC['H'] and hh['X10']['conv'] == hC['conv'], ('X10 assembly', d)
        rec2, cnt2 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            st.enter_context(rec2)
            st.enter_context(cnt2)
            score(rec2, cnt2, c_h, k('H01'), F.hook_counts(model))
        assert torch.equal(rec2.extra[k('H01')][f'{SPLIT}:in'], x_c), ('natural entry != x_C', d)
        rec3, cnt3 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            e = st.enter_context(LR.Entry(model, x_t))
            st.enter_context(rec3)
            st.enter_context(cnt3)
            exp3 = F.hook_counts(model)
            score(rec3, cnt3, c_x, k('X10'), exp3, e)
            score(rec3, cnt3, P.n_cache(cT, cC, types, {l: fC[l] for l in G}), k('XH11'), exp3, e)
        for name in ('X10', 'XH11'):
            assert torch.equal(rec3.extra[k(name)][f'{SPLIT}:in'].cpu(), x_t.cpu()), ('entry != x_T', name, d)
        # donors immutable through the direction's scoring
        assert comp_sha(cT, types, ('recurrent', 'kv', 'conv'), 0) == hT['all'], ('T donor changed', d)
        assert comp_sha(cC, types, ('recurrent', 'kv', 'conv'), 0) == hC['all'], ('C donor changed', d)
        if d in EH_DIRS:
            for mine, theirs in (('T_native', 'T_native'), ('X10', 'X10'), ('H01', 'H01'), ('XH11', 'XH11')):
                assert res[k(mine)]['score']['logits_sha256'] == eh_sha(k(theirs)), ('EH replay', d, mine)
            assert res[k('XH11')]['score']['logits_sha256'] == b3_rec['cells'][k('N:CC')]['score']['logits_sha256'], ('XH11 != B3 N:CC', d)
        cache_hashes[d] = {'T': hT, **hh}
        res[k('T_native')]['tv_vs_C'] = tv(logits[k('T_native')], logits['C_native'])
        res[k('XH11')]['tv_vs_C'] = tv(logits[k('XH11')], logits['C_native'])
        if preflight and d == OFF_DIR:                                               # recorder on/off: rebuild C and T, score bare
            cC2 = P.form(engine, base, prefix, window, None, calib)
            cT2 = P.form(engine, base, prefix, window, cond, calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(window)
            assert comp_sha(cC2, types, ('recurrent', 'kv', 'conv'), 0) == hC['all'] and comp_sha(cT2, types, ('recurrent', 'kv', 'conv'), 0) == hT['all'], 'rebuild differs'
            off = B._Off()
            for key, cache in (('OFF:C_native', cC2), (f'OFF:T_native|{d}', cT2)):
                r, z = B.score(engine, cache, last, n, off, key, stop, F.hook_counts(model))
                counts['scores'] += 1
                ref = 'C_native' if key == 'OFF:C_native' else k('T_native')
                assert r['logits_sha256'] == res[ref]['score']['logits_sha256'], ('recorder on/off', key)
                res[key] = {'score': r}
            gates['recorder_off'] = 'C and T(4146) rebuilt, scored without recorders: logits bitwise equal; rebuilt caches hash-equal'
            del cC2, cT2
        del cT, rec1, rec2, rec3, cnt1, cnt2, cnt3, c_h, c_x
    gates['calibration'] = 'scenario f0 calibration (in process) equals the B3 record exactly'
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'C_native == B3 == EH; EH directions: T_native, X10, H01, XH11 == EH bitwise; XH11 == B3 N:CC'
    gates['entry'] = 'H01 natural layer-13 input == x_C; X10/XH11 entry == x_T, hook once'
    gates['assembly'] = 'H (deep recurrent+KV) and conv hashed separately: H01 = (H_T, conv_C), X10 = (H_C, conv_C); donors unchanged'
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
    eh = [w / 'receipt.json' for w in sorted(EH_FORMAL.glob('worker-*')) if w.is_dir()] + [EH_FORMAL / 'verification.json']
    return own + b3 + eh + [p for p in B3R.frozen_paths() if p not in own]


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
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, b3_rec, eh_record(item['id']), output,
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
    lock = open(f'/tmp/acupuncture-ehxc-worker{worker}.lock', 'w')
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
        if r['stage'] == 'preflight':
            w |= {'OFF:C_native', f'OFF:T_native|{OFF_DIR}'}
        for g in ('calibration', 'write', 'replay', 'entry', 'assembly', 'kernel') + (('recorder_off',) if r['stage'] == 'preflight' else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'eh_xc_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
