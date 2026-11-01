"""C2: does the fixed 45-head list carry the V effect across intervention directions? (CONTRACT.zh-CN.md r01; plan
docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01.zh-CN.md.)

Per P-series input: calibrate on the scenario f0 (must equal C1-P), form C once; for each direction d in
{N4146 (anchor), N1210, R0, R1} (XCHAN definitions, L0, dose -1, late window) audit the L0 write, form T_d and score
T_native|d, then in the N background (C shallow + T_d deep, decoder-13 entry = x_T of T_native|d): N:TT, N:CC, N:CT,
N:CFIX, N:CUF1-4 (FIX's own layer-matched random subsets), then select H on N:TT (FV-local-path arithmetic), freeze it,
score N:CH. Preflight adds N:ALL / N:EMPTY for R0.

python c2_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
C1P_DIR = HERE.parent / 'cache-head-rule-prospective-v1-2026-11-01'
XCHAN_DIR = HERE.parent / 'cache-cross-channel-validation-v1-2026-10-31'
sys.path.insert(0, str(C1P_DIR))
sys.path.insert(0, str(XCHAN_DIR))
sys.path.insert(0, str(HERE))
import c1p_run as P  # noqa: E402  (frozen C1-P runner: inputs, formation, N-cache assembly, CF/LR chain)
import c1p_core as PK  # noqa: E402
import xchan as X  # noqa: E402  (frozen XCHAN: needle definitions, directions, write audit)
import c2_core as K  # noqa: E402

CF, CFK, LR, CO, B = P.CF, P.CFK, P.LR, P.CO, P.B
F, L, T1, exp = B.F, B.L, B.T1, B.exp

PLAN_ID = 'C2-FIXLIST-CROSS-DIRECTION-v1'
PLAN_DOC = REPO / 'docs/cache-c2-fixed-list-cross-direction-plan-v1-2026-11-01.zh-CN.md'
FIXU = HERE / 'data/fix-random-r01.json'
C1P_FORMAL = C1P_DIR / 'runs/formal-r01'
SPLIT = 13
PREFLIGHT_ITEMS = ('P01-f0', 'P01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 10, 'scores': 86}, 'formal': {'formations': 60, 'scores': 492}}
STORAGE_LIMIT = 8 * 2 ** 30
PER_DIR = ('T_native', 'N:TT', 'N:CC', 'N:CT', 'N:CFIX', 'N:CUF1', 'N:CUF2', 'N:CUF3', 'N:CUF4', 'N:CH')


def items():
    return P.items()


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def conditions():
    dirs = X.load_directions()
    by = {n['id']: n for n in X.needles()}
    return {d: X.engine_condition(by[d], dirs) for d in K.DIRECTIONS}


def c1p_assets(item_id):
    for w in sorted(C1P_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'C1-P record hash'
            rec = exp.read(w / rel)
            cal = exp.read(w / f'calibrations/{rec["item"]["reference_id"]}.json')
            return rec, cal
    raise KeyError(item_id)


def run_item(engine, item, context, calib, conds, fixed, ufix, c1p_rec, output, receipt, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert G == PK.G
    seg = PK.label_tokens(engine.tokenizer, context, item['record'], encode_text)
    assert not seg['straddling_tokens']
    prompt, b = seg['ids'], seg['b']
    assert exp.digest(prompt) == c1p_rec['prompt_token_sha256'], 'prompt tokens differ from C1-P'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'scores': 0}
    res, logits, gates, audits, selections = {}, {}, {}, {}, {}
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    stop = list(engine.stop_ids)

    def score(rec, cnt, cache, key, expected, entry=None):
        cnt.key = key
        before = entry.hits if entry else 0
        r, z = B.score(engine, cache, last, n, rec, key, stop, expected)
        cnt.key = None
        counts['scores'] += 1
        assert cnt.hits.get(key, {}) == {i: 1 for i in G} and cnt.chunk.get(key, 0) == 0, ('kernel hits', key)
        if entry:
            assert entry.hits - before == 1, ('entry hits', key)
        logits[key] = z
        res[key] = {'score': r}
        return r

    rec0, cnt0 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
    with ExitStack() as st:
        st.enter_context(rec0)
        st.enter_context(cnt0)
        rc = score(rec0, cnt0, cC, 'C_native', F.hook_counts(model))
    a = rc['nonstop_winner']
    assert rc['logits_sha256'] == c1p_rec['cells']['C_native']['score']['logits_sha256'], 'C_native differs from C1-P'
    fC = {l: L._get(cC.layers[l], 'conv_states') for l in G}
    lay = L.model_layers(model)
    fn = B.S3.final_norm(model)
    E = model.get_output_embeddings().weight
    mean_e = torch.zeros(E.shape[1], dtype=torch.float64, device=E.device)
    for i in range(0, E.shape[0], 16384):
        mean_e += E[i:i + 16384].double().sum(0)
    mean_e /= E.shape[0]

    def get_w(l):
        at = lay[l].linear_attn
        return {'ln': lay[l].input_layernorm.weight.double(), 'Wv': at.in_proj_qkv.weight[4096:8192].double(),
                'cw': at.conv1d.weight[4096:8192, 0, :].double(), 'gn': at.norm.weight.double(), 'Wo': at.out_proj.weight.double()}

    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        rec1, cnt1 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            st.enter_context(rec1)
            st.enter_context(cnt1)
            score(rec1, cnt1, cT, f'T_native|{d}', F.hook_counts(model))
        x_t = rec1.extra[f'T_native|{d}'][f'{SPLIT}:in'].detach().clone()
        fT = {l: L._get(cT.layers[l], 'conv_states') for l in G}
        sets = {'N:CFIX': fixed, 'N:CUF1': ufix[0], 'N:CUF2': ufix[1], 'N:CUF3': ufix[2], 'N:CUF4': ufix[3]}
        if preflight and d == 'R0_L00_D-1':
            sets['N:ALL'] = [[l, h] for l in G for h in range(PK.NV)]
            sets['N:EMPTY'] = []
        rec2, cnt2 = B.Recorder(model, G, SPLIT), CF.Counter(model, G)
        with ExitStack() as st:
            e = st.enter_context(LR.Entry(model, x_t))
            st.enter_context(rec2)
            st.enter_context(cnt2)
            exp2 = F.hook_counts(model)
            k = lambda name: f'{name}|{d}'   # noqa: E731
            score(rec2, cnt2, P.n_cache(cT, cC, types), k('N:TT'), exp2, e)
            score(rec2, cnt2, P.n_cache(cT, cC, types, {l: fC[l] for l in G}), k('N:CC'), exp2, e)
            score(rec2, cnt2, P.n_cache(cT, cC, types, {l: CFK.assemble(fC[l], fT[l]) for l in G}), k('N:CT'), exp2, e)
            assert res[k('N:TT')]['score']['logits_sha256'] == res[k('T_native')]['score']['logits_sha256'], ('N:TT replay', d)
            for name, heads in sets.items():
                score(rec2, cnt2, P.n_cache(cT, cC, types, {l: PK.conv_subset(fT[l], fC[l], heads, l) for l in G}), k(name), exp2, e)
            hT = rec2.extra[k('N:TT')]['final:h'].double()
            u = (E[PK.S46].double() - mean_e) * (1 + fn.weight.double()) * torch.rsqrt(hT.pow(2).mean() + fn.eps)
            sc, val = PK.select_scores(get_w, {l: rec2.rows[k('N:TT')][l] for l in G}, {l: rec2.extra[k('N:TT')][f'{l}:in'] for l in G},
                                       {l: fT[l][0, 4096:8192] for l in G}, {l: fC[l][0, 4096:8192] for l in G}, u, fn.eps,
                                       outproj_ref={l: cnt2.extra[k('N:TT')][f'{l}:out_proj'] for l in G})
            assert val['v_rel'] <= K.RULE['rebuild_rel'] and val['outproj_rel'] <= K.RULE['rebuild_rel'], ('selection rebuild', d, val)
            H = PK.top_heads(sc)
            spath = output / f'selections/{item["id"]}__{d}.json'
            exp.write(spath, {'item': item['id'], 'direction': d, 'H': H, 'validation': val, 'frozen_before_subset_scoring': True,
                              'created_at': exp.utc()}, immutable=True)
            receipt.setdefault('selection_hashes', {})[str(spath.relative_to(output))] = exp.sha(spath)
            exp.write(output / 'receipt.json', receipt)
            sets['N:CH'] = H
            score(rec2, cnt2, P.n_cache(cT, cC, types, {l: PK.conv_subset(fT[l], fC[l], H, l) for l in G}), k('N:CH'), exp2, e)
        l0 = PK.G[0]
        for name, heads in sets.items():
            hs = {(x[0], x[1]) for x in heads}
            v, vT, vC = (rec2.rows[k(c)][l0]['v'].cpu() for c in (name, 'N:CT', 'N:CC'))
            for h in range(PK.NV):
                assert torch.equal(v[h], (vT if (l0, h) in hs else vC)[h]), ('layout', d, name, h)
            assert torch.equal(rec2.extra[k(name)][f'{SPLIT}:in'].cpu(), x_t.cpu()), ('entry', d, name)
        if preflight and d == 'R0_L00_D-1':
            assert res[k('N:ALL')]['score']['logits_sha256'] == res[k('N:CT')]['score']['logits_sha256'], 'all-heads != N:CT'
            assert res[k('N:EMPTY')]['score']['logits_sha256'] == res[k('N:CC')]['score']['logits_sha256'], 'empty != N:CC'
        selections[d] = {'H': H, 'validation': val, 'overlap_H_FIX': len({tuple(x) for x in H} & {tuple(x) for x in fixed}),
                         'path': str(spath.relative_to(output))}
        if d == K.ANCHOR:
            for mine, theirs in (('T_native', 'T_native'), ('N:CC', 'N:CC'), ('N:CT', 'N:CT'), ('N:CFIX', 'N:CFIX')):
                assert res[k(mine)]['score']['logits_sha256'] == c1p_rec['cells'][theirs]['score']['logits_sha256'], ('anchor replay vs C1-P', mine)
        del cT, rec1, rec2, cnt1, cnt2
    gates['calibration'] = 'scenario f0 calibration equals the C1-P record exactly'
    gates['write'] = 'every direction: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'C_native and anchor T_native/N:CC/N:CT/N:CFIX bitwise == C1-P; every direction N:TT == T_native|d'
    gates['layout'] = 'layer 13: every subset cell value head equals N:CT (selected) or N:CC (not) bitwise; entries == x_T'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never; entry hook once per N cell'
    gates['selection'] = 'adaptive H rebuild <= 0.02, frozen to disk before N:CH'
    if preflight:
        gates['preflight_subsets'] = 'R0: all-448 subset == N:CT and empty subset == N:CC bitwise'
    for key, z in logits.items():
        res[key]['readout'] = CFK.readout(z, a)
    body = {'a_token': a, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits,
            'selections': selections, 'FIX': fixed, 'UFIX': ufix, 'cells': res, 'counts': counts, 'gates': gates}
    tensors = {'logits': logits}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, FIXU, X.DIRECTIONS, XCHAN_DIR / 'xchan.py']
    c1p = [w / 'receipt.json' for w in sorted(C1P_FORMAL.glob('worker-*')) if w.is_dir()] + [C1P_FORMAL / 'verification.json']
    return own + c1p + [p for p in P.frozen_paths() if p not in own]


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
    fx = exp.read(P.FIXED)
    fixed = fx['heads']
    fu = exp.read(FIXU)
    assert fu['fixed_heads_sha256'] == exp.sha(P.FIXED) and fu['inputs_sha256'] == exp.sha(P.INPUTS)
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    totals = {'formations': 0, 'scores': 0}
    calib = {}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        c1p_rec, c1p_cal = c1p_assets(item['id'])
        if rid not in calib:
            F.assert_no_hooks(engine.model)
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            assert calib[rid] == c1p_cal, ('calibration differs from C1-P', rid)
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        started = time.monotonic()
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, fixed, fu['subsets'][item['id']], c1p_rec,
                                 output, receipt, preflight=(stage == 'preflight'))
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
    lock = open(f'/tmp/acupuncture-c2-worker{worker}.lock', 'w')
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
    assert set(r['selection_hashes']) == {f'selections/{u["key"]}__{d}.json' for u in units for d in K.DIRECTIONS}
    for rel, digest in list(r['tensor_hashes'].items()) + list(r['record_hashes'].items()) + list(r['selection_hashes'].items()):
        assert exp.sha(path / rel) == digest, rel
    want = {'C_native'} | {f'{c}|{d}' for c in PER_DIR for d in K.DIRECTIONS}
    if r['stage'] == 'preflight':
        want |= {'N:ALL|R0_L00_D-1', 'N:EMPTY|R0_L00_D-1'}
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('calibration', 'write', 'replay', 'layout', 'kernel', 'selection'):
            assert rec['gates'][g], g
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
            cmd = [sys.executable, '-u', str(HERE / 'c2_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
