"""EH: does the ~8-logit e1 step (C_native -> N:CC) follow the layer-13 entry input or the deep history (layers 13-31
recurrent states + attention KV)?  2x2 entry x history with all convolution histories clean, plus FIX0 = clean background +
only the 45 FIX heads' conv V history from T (reverse order of NFC e2).  CONTRACT.zh-CN.md r01;
plan docs/cache-entry-history-plan-v1-2026-11-02.zh-CN.md.

Cells per input x direction:  00 = C_native (shared);  10 = all-C cache + entry x_T;  01 = deep T S/KV, conv C, shallow C,
natural entry (== x_C);  11 = N:CC (entry x_T; replay == B3);  FIX0 = all-C cache with FIX conv V from T, natural entry.
python eh_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
import json
import os
from pathlib import Path
import subprocess
import sys
import time
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

PLAN_ID = 'EH-ENTRY-HISTORY-v1'
PLAN_DOCS = [REPO / 'docs/cache-entry-history-plan-v1-2026-11-02.zh-CN.md']
B3_FORMAL = B3_DIR / 'runs/formal-r01'
SPLIT = 13
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1', 'R1_L00_D-1')
PREFLIGHT_ITEMS = V.PREFLIGHT_ITEMS
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 10, 'scores': 42, 'calibrations': 1},
          'formal': {'formations': 60, 'scores': 252, 'calibrations': 6}}
STORAGE_LIMIT = 2 * 2 ** 30
ARMS = ('X10', 'H01', 'XH11', 'FIX0')


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


def run_item(engine, item, context, calib, conds, fixed, b3_rec, output, preflight=False):
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
    res, logits, gates, audits = {}, {}, {}, {}
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    stop = list(engine.stop_ids)

    def b3_sha(key):
        return b3_rec['cells'][key]['score']['logits_sha256']

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
        return r

    rec0, cnt0 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
    with ExitStack() as st:
        st.enter_context(rec0)
        st.enter_context(cnt0)
        rc = score(rec0, cnt0, cC, 'C_native', F.hook_counts(model))
    a = rc['nonstop_winner']
    assert a == b3_rec['a_token'] and rc['logits_sha256'] == b3_sha('C_native'), 'C_native differs from B3'
    x_c = rec0.extra['C_native'][f'{SPLIT}:in'].detach().clone()
    fC = {l: L._get(cC.layers[l], 'conv_states') for l in G}

    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(window)
        k = lambda name: f'{name}|{d}'   # noqa: E731
        rec1, cnt1 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            st.enter_context(rec1)
            st.enter_context(cnt1)
            score(rec1, cnt1, cT, k('T_native'), F.hook_counts(model))
        assert res[k('T_native')]['score']['logits_sha256'] == b3_sha(k('T_native')), ('T_native vs B3', d)
        x_t = rec1.extra[k('T_native')][f'{SPLIT}:in'].detach().clone()
        fT = {l: L._get(cT.layers[l], 'conv_states') for l in G}
        # cache assemblies
        c_h01 = P.n_cache(cT, cC, types, {l: fC[l] for l in G})                       # deep T S/KV, conv C, shallow C
        c_x10 = P.n_cache(cC, cC, types)                                                # all C
        fix_conv = {l: PK.conv_subset(fT[l], fC[l], fixed, l) for l in G}
        c_fix0 = P.n_cache(cC, cC, types, fix_conv)                                     # all C, FIX conv V from T
        fixset = {(x[0], x[1]) for x in fixed}
        for l in G:                                                                     # conv layout of FIX0 (exact)
            got = L._get(c_fix0.layers[l], 'conv_states')
            assert torch.equal(got, fix_conv[l])
            assert torch.equal(got[:, :4096], fC[l][:, :4096]), ('FIX0 q/k conv must be C', l)
            for h in range(PK.NV):
                sl = slice(4096 + h * 128, 4096 + (h + 1) * 128)
                ref = fT[l] if (l, h) in fixset else fC[l]
                assert torch.equal(got[:, sl], ref[:, sl]), ('FIX0 V layout', l, h)
        for l in G:                                                                     # 01 deep recurrent state is T, conv is C
            assert torch.equal(L._get(c_h01.layers[l], 'conv_states'), fC[l])
        rec2, cnt2 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:                                                         # natural entry arms
            st.enter_context(rec2)
            st.enter_context(cnt2)
            exp2 = F.hook_counts(model)
            score(rec2, cnt2, c_h01, k('H01'), exp2)
            score(rec2, cnt2, c_fix0, k('FIX0'), exp2)
        for name in ('H01', 'FIX0'):
            assert torch.equal(rec2.extra[k(name)][f'{SPLIT}:in'], x_c), ('natural entry != x_C', name, d)
        rec3, cnt3 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:                                                         # entry = x_T arms
            e = st.enter_context(LR.Entry(model, x_t))
            st.enter_context(rec3)
            st.enter_context(cnt3)
            exp3 = F.hook_counts(model)
            score(rec3, cnt3, c_x10, k('X10'), exp3, e)
            score(rec3, cnt3, P.n_cache(cT, cC, types, {l: fC[l] for l in G}), k('XH11'), exp3, e)
        for name in ('X10', 'XH11'):
            assert torch.equal(rec3.extra[k(name)][f'{SPLIT}:in'].cpu(), x_t.cpu()), ('entry != x_T', name, d)
        assert res[k('XH11')]['score']['logits_sha256'] == b3_sha(k('N:CC')), ('11 != B3 N:CC', d)
        del cT, rec1, rec2, rec3, cnt1, cnt2, cnt3, c_h01, c_x10, c_fix0
    gates['calibration'] = 'scenario f0 calibration (in process) equals the B3 record exactly'
    gates['write'] = 'every direction: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'C_native (=00), T_native, XH11 (= N:CC) logits bitwise == B3'
    gates['entry'] = 'H01/FIX0 natural layer-13 input == x_C bitwise; X10/XH11 entry == x_T, hook once'
    gates['layout'] = 'FIX0: q/k conv C, FIX value-head conv channels T, others C (exact); H01 conv == C'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never'
    for key, z in logits.items():
        res[key]['readout'] = CFK.readout(z, a)
    body = {'a_token': a, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits,
            'FIX': fixed, 'cells': res, 'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, {'logits': logits}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    return own + b3 + [p for p in B3R.frozen_paths() if p not in own]


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
    fixed = exp.read(P.FIXED)['heads']
    conds = V.conditions()
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
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, fixed, b3_rec, output,
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
    return V.plan(stage, worker, n_workers)


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-eh-worker{worker}.lock', 'w')
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
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('calibration', 'write', 'replay', 'entry', 'layout', 'kernel'):
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
            cmd = [sys.executable, '-u', str(HERE / 'eh_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
