"""C1-P: does the frozen head-selection rule predict causal V effects on new inputs? (CONTRACT.zh-CN.md r01; plan
docs/cache-head-rule-prospective-input-plan-v1-2026-11-01.zh-CN.md r2.)

Per input: calibrate on the scenario's f0 context (old rule), form C (no needle) and T (L0/N4146/-1 on b+1..n-2) step
route, score C_native / T_native, then in the N background (C shallow + T deep, decoder-13 entry = x_T): N:TT, N:CC,
N:CT; select H (FV-local-path arithmetic on the N:TT run) and freeze it to disk; then N:CH, N:CU1..4, N:CFIX
(+ preflight N:ALL, N:EMPTY).

python c1p_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
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
CF_DIR = HERE.parent / 'cache-conv-factor-v1-2026-11-01'
sys.path.insert(0, str(CF_DIR))
sys.path.insert(0, str(HERE))
import conv_factor as CF  # noqa: E402
import cf_core as CFK  # noqa: E402
import c1p_core as K  # noqa: E402

LR, CO, B = CF.LR, CF.CO, CF.B
F, L, T1, exp = B.F, B.L, B.T1, B.exp

PLAN_ID = 'C1P-HEADRULE-PROSPECTIVE-v1'
PLAN_DOC = REPO / 'docs/cache-head-rule-prospective-input-plan-v1-2026-11-01.zh-CN.md'
INPUTS = HERE / 'data/inputs-r01.json'
FIXED = HERE / 'data/fixed-heads-r01.json'
FV_RESULTS = HERE.parent / 'cache-fv-local-path-v1-2026-11-01/results-r01.json'
SPLIT = 13
PREFLIGHT_ITEMS = ('P01-f0', 'P01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 4, 'scores': 26}, 'formal': {'formations': 24, 'scores': 132}}
STORAGE_LIMIT = 6 * 2 ** 30
SUBSETS = ('N:CH', 'N:CU1', 'N:CU2', 'N:CU3', 'N:CU4', 'N:CFIX')


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


def form(engine, base, prefix, window, cond, reference):
    cache = copy.deepcopy(base)
    for t in window:
        cache, _ = F.forward_tokens(engine, cache, [prefix[t]], t, cond, reference)
    return cache


def n_cache(cT, cC, types, conv=None):
    """C shallow + T deep (S, K, conv); optional per-layer conv override."""
    c = copy.deepcopy(cT)
    for i, _, f in L.component_tensors(c, types):
        if i < SPLIT:
            L._set(c.layers[i], f, L._get(cC.layers[i], f).clone())
        elif conv is not None and f == 'conv_states' and i in conv:
            L._set(c.layers[i], f, conv[i].clone())
    return c


def run_item(engine, item, context, calib, fixed, output, receipt, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert G == K.G
    stop = list(engine.stop_ids)
    seg = K.label_tokens(engine.tokenizer, context, item['record'], encode_text)
    assert not seg['straddling_tokens'], ('token straddles a segment boundary', seg['straddling_tokens'])
    prompt, b = seg['ids'], seg['b']
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'scores': 0}
    cond = T1.engine_condition(F.A0)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    cC = form(engine, base, prefix, window, None, calib)
    cT = form(engine, base, prefix, window, cond, calib)
    counts['formations'] += 2
    res, logits, gates = {}, {}, {}
    token_set = stop

    def score(rec, cnt, cache, key, expected, entry=None):
        cnt.key = key
        before = entry.hits if entry else 0
        r, z = B.score(engine, cache, last, n, rec, key, token_set, expected)
        cnt.key = None
        counts['scores'] += 1
        assert cnt.hits.get(key, {}) == {i: 1 for i in G} and cnt.chunk.get(key, 0) == 0, ('kernel hits', key)
        if entry:
            assert entry.hits - before == 1, ('entry hits', key)
        logits[key] = z
        res[key] = {'score': r}
        return r

    rec1, cnt1 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
    with ExitStack() as st:
        st.enter_context(rec1)
        st.enter_context(cnt1)
        exp1 = F.hook_counts(model)
        rc = score(rec1, cnt1, cC, 'C_native', exp1)
        score(rec1, cnt1, cT, 'T_native', exp1)
    a = rc['nonstop_winner']
    x_t = rec1.extra['T_native'][f'{SPLIT}:in'].detach().clone()
    fT = {l: L._get(cT.layers[l], 'conv_states') for l in G}
    fC = {l: L._get(cC.layers[l], 'conv_states') for l in G}
    rec2, cnt2 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
    with ExitStack() as st:
        e = st.enter_context(LR.Entry(model, x_t))
        st.enter_context(rec2)
        st.enter_context(cnt2)
        exp2 = F.hook_counts(model)
        score(rec2, cnt2, n_cache(cT, cC, types), 'N:TT', exp2, e)
        score(rec2, cnt2, n_cache(cT, cC, types, {l: fC[l] for l in G}), 'N:CC', exp2, e)
        score(rec2, cnt2, n_cache(cT, cC, types, {l: CFK.assemble(fC[l], fT[l]) for l in G}), 'N:CT', exp2, e)
        assert res['N:TT']['score']['logits_sha256'] == res['T_native']['score']['logits_sha256'], 'N:TT does not replay T_native'
        # ---- head selection on the N:TT reference run (FV-local-path arithmetic), frozen to disk before subsets
        lay = L.model_layers(model)
        fn = B.S3.final_norm(model)
        eps = fn.eps
        E = model.get_output_embeddings().weight
        mean_e = torch.zeros(E.shape[1], dtype=torch.float64, device=E.device)
        for i in range(0, E.shape[0], 16384):
            mean_e += E[i:i + 16384].double().sum(0)
        mean_e /= E.shape[0]
        hT = rec2.extra['N:TT']['final:h'].double()
        u = (E[K.S46].double() - mean_e) * (1 + fn.weight.double()) * torch.rsqrt(hT.pow(2).mean() + eps)

        def get_w(l):
            at = lay[l].linear_attn
            return {'ln': lay[l].input_layernorm.weight.double(), 'Wv': at.in_proj_qkv.weight[4096:8192].double(),
                    'cw': at.conv1d.weight[4096:8192, 0, :].double(), 'gn': at.norm.weight.double(), 'Wo': at.out_proj.weight.double()}
        drivers = {l: rec2.rows['N:TT'][l] for l in G}
        entries = {l: rec2.extra['N:TT'][f'{l}:in'] for l in G}
        sc, val = K.select_scores(get_w, drivers, entries, {l: fT[l][0, 4096:8192] for l in G}, {l: fC[l][0, 4096:8192] for l in G},
                                  u, eps, outproj_ref={l: cnt2.extra['N:TT'][f'{l}:out_proj'] for l in G})
        assert val['v_rel'] <= K.RULE['rebuild_rel'] and val['outproj_rel'] <= K.RULE['rebuild_rel'], ('selection rebuild', val)
        H = K.top_heads(sc)
        U = [K.random_subset(item['id'], j, H) for j in range(1, 5)]
        sel = {'item': item['id'], 'H': H, 'U': U, 'FIX': fixed, 'validation': val,
               'scores': [[c, l, h] for c, l, h in sc], 'frozen_before_subset_scoring': True, 'created_at': exp.utc()}
        spath = output / f'selections/{item["id"]}.json'
        exp.write(spath, sel, immutable=True)
        receipt.setdefault('selection_hashes', {})[str(spath.relative_to(output))] = exp.sha(spath)
        exp.write(output / 'receipt.json', receipt)
        sets = {'N:CH': H, 'N:CU1': U[0], 'N:CU2': U[1], 'N:CU3': U[2], 'N:CU4': U[3], 'N:CFIX': fixed}
        if preflight:
            sets['N:ALL'] = [[l, h] for l in G for h in range(K.NV)]
            sets['N:EMPTY'] = []
        for key, heads in sets.items():
            score(rec2, cnt2, n_cache(cT, cC, types, {l: K.conv_subset(fT[l], fC[l], heads, l) for l in G}), key, exp2, e)
    for key in ['N:TT', 'N:CC', 'N:CT'] + list(sets):
        assert torch.equal(rec2.extra[key][f'{SPLIT}:in'].cpu(), x_t.cpu()), ('entry', key)
    l0 = K.G[0]
    for key, heads in sets.items():
        hs = {(l, h) for l, h in heads}
        v, vT, vC = (rec2.rows[k][l0]['v'].cpu() for k in (key, 'N:CT', 'N:CC'))
        for h in range(K.NV):
            assert torch.equal(v[h], (vT if (l0, h) in hs else vC)[h]), ('per-head layout', key, h)
    gates['replay'] = 'N:TT logits bitwise == T_native; every N cell entry == x_T'
    gates['layout'] = 'layer 13: every value head of every subset cell equals N:CT (selected) or N:CC (not selected) bitwise'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never; entry hook once per N cell'
    gates['selection'] = f"rebuild v_rel {val['v_rel']:.4f}, out_proj_rel {val['outproj_rel']:.4f} (<= 0.02); list frozen to disk before subset scoring"
    if preflight:
        assert res['N:ALL']['score']['logits_sha256'] == res['N:CT']['score']['logits_sha256'], 'all-heads subset != N:CT'
        assert res['N:EMPTY']['score']['logits_sha256'] == res['N:CC']['score']['logits_sha256'], 'empty subset != N:CC'
        gates['preflight_subsets'] = 'all-448 subset == N:CT and empty subset == N:CC bitwise'
    for key, z in logits.items():
        res[key]['readout'] = CFK.readout(z, a)
    body = {'a_token': a, 'segments': {k: seg[k] for k in ('labels', 'b', 'n', 'fact_span')}, 'prompt_token_sha256': exp.digest(prompt),
            'calibration': calib, 'selection_path': str(spath.relative_to(output)), 'H': H, 'U': U, 'FIX': fixed,
            'overlap': {k: len({tuple(x) for x in v} & {tuple(x) for x in H}) for k, v in sets.items()},
            'cells': res, 'counts': counts, 'gates': gates}
    tensors = {'logits': logits, 'drivers': {k: B.to_cpu({i: {f: v for f, v in rec2.rows[k][i].items() if hasattr(v, 'detach')} for i in G}) for k in rec2.rows},
               'extras': {k: B.to_cpu(r.extra[k]) for r in (rec1, rec2) for k in r.extra}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, INPUTS, FIXED, FV_RESULTS]
    return own + [p for p in CF.frozen_paths() if p not in own]


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
    assert auth['cpu_receipt_path'] in auth['required_evidence']
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units):
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    fixed = exp.read(FIXED)['heads']
    assert exp.read(FIXED)['source_sha256'] == exp.sha(FV_RESULTS)
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    totals = {'formations': 0, 'scores': 0}
    calib = {}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            F.assert_no_hooks(engine.model)
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        started = time.monotonic()
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], fixed, output, receipt, preflight=(stage == 'preflight'))
        for k in totals:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item, **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-c1p-worker{worker}.lock', 'w')
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
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units)
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
    units = exp.read(path / 'plan.json')
    assert units == plan(r['stage'], r['worker'], r['n_workers'])
    expected = {f'records/{u["key"]}.json' for u in units}
    assert set(r['record_hashes']) == expected
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    assert set(r['selection_hashes']) == {f'selections/{u["key"]}.json' for u in units}
    for rel, digest in list(r['tensor_hashes'].items()) + list(r['record_hashes'].items()) + list(r['selection_hashes'].items()):
        assert exp.sha(path / rel) == digest, rel
    want = {'C_native', 'T_native', 'N:TT', 'N:CC', 'N:CT'} | set(SUBSETS) | ({'N:ALL', 'N:EMPTY'} if r['stage'] == 'preflight' else set())
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('replay', 'layout', 'kernel', 'selection'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight':
            assert rec['gates']['preflight_subsets']
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes']}


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
            cmd = [sys.executable, '-u', str(HERE / 'c1p_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        calls = {k: sum(x['model_calls'][k] for x in results) for k in ('formations', 'scores')}
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
