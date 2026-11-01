"""B4: does the fixed-list main effect depend on the non-FIX G-layer value heads' current-step readouts?
(CONTRACT.zh-CN.md r01; plan v2 docs/cache-b4-nonfix-readout-dependence-plan-v2-2026-11-02.zh-CN.md + v3 amendments.)

Per P-series input (B3/C2 worker-GPU assignment and in-process f0 calibration): form C, score C_native; per direction:
form T, score T_native (x_T); then in the N background score, in this order,
    CC, CFIX (replay, bitwise == B3), K0 (CC + clamp to own donor; must == CC), K (CFIX + non-FIX rows of all 14 G layers
    clamped to the CC donor), K_early (layers 13-18), K_late (20-30), M_nat, M_rand (CFIX + per-layer out_proj-matched
    additive perturbation of the non-FIX rows; directions from B3 next-scenario responses / frozen Gaussian seeds).
python b4_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
import hashlib
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
import b4_core as K  # noqa: E402
import b4_hooks as H  # noqa: E402

V, P, PK, X = B3R.V, B3R.P, B3R.PK, B3R.X
CF, CFK, LR, B = B3R.CF, B3R.CFK, B3R.LR, B3R.B
F, L, T1, exp = B3R.F, B3R.L, B3R.T1, B3R.exp

PLAN_ID = 'B4-NONFIX-READOUT-v1'
PLAN_DOCS = [REPO / 'docs/cache-b4-nonfix-readout-dependence-plan-v2-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-b4-nonfix-readout-dependence-plan-v3-2026-11-02.zh-CN.md']
B3_FORMAL = B3_DIR / 'runs/formal-r01'
SHADOW = HERE / 'readiness/shadow-r01.json'
SPLIT = 13
PREFLIGHT_ITEMS = V.PREFLIGHT_ITEMS
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'formations': 10, 'scores': 74, 'calibrations': 1},
          'formal': {'formations': 60, 'scores': 444, 'calibrations': 6}}
STORAGE_LIMIT = 2 * 2 ** 30
N_ARMS = ('CC', 'CFIX', 'K0', 'K', 'K_early', 'K_late', 'M_nat', 'M_rand')
CLAMP_LAYERS = {'K0': K.G_LAYERS, 'K': K.G_LAYERS, 'K_early': K.EARLY, 'K_late': K.LATE}


def next_scenario(iid):
    s, f = iid.rsplit('-', 1)
    n = int(s[1:]) % 6 + 1
    return f'P{n:02d}-{f}'


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


def b3_templates(item_ids):
    """(gno_CC - gno_CFIX) per direction and G layer from the B3 tensors of the given inputs, hash-checked."""
    import torch
    out = {}
    for w in sorted(B3_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for iid in item_ids:
            rel = f'tensors/{iid}.pt'
            if rel not in r['tensor_hashes']:
                continue
            assert exp.sha(w / rel) == r['tensor_hashes'][rel], ('B3 tensor hash', rel)
            ten = torch.load(w / rel, map_location='cpu', weights_only=False)
            out[iid] = {d: {l: (ten['counter'][f'N:CC|{d}'][f'{l}:gated_norm_out'].float()
                                - ten['counter'][f'N:CFIX|{d}'][f'{l}:gated_norm_out'].float()).reshape(K.NV, K.HD)
                            for l in K.G_LAYERS} for d in K.DIRECTIONS}
            del ten
    assert set(out) == set(item_ids), set(item_ids) - set(out)
    return out


def run_item(engine, item, context, calib, conds, fixed, b3_rec, tmpl_next, output, preflight=False):
    import torch
    from control_engine import encode_text
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == K.G_LAYERS
    seg = PK.label_tokens(engine.tokenizer, context, item['record'], encode_text)
    assert not seg['straddling_tokens']
    prompt, b = seg['ids'], seg['b']
    assert exp.digest(prompt) == b3_rec['prompt_token_sha256'], 'prompt tokens differ from B3'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'scores': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    res, logits, gates, audits, matching, saved = {}, {}, {}, {}, {}, {}
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    stop = list(engine.stop_ids)
    lay = L.model_layers(model)
    Wbf = {l: lay[l].linear_attn.out_proj.weight for l in G}
    W32 = {l: Wbf[l].float() for l in G}
    fixset = {(x[0], x[1]) for x in fixed}
    nonfix = {l: torch.tensor([(l, h) not in fixset for h in range(K.NV)]) for l in G}

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

    cnt0 = CF.Counter(model, G)
    with ExitStack() as st:
        st.enter_context(cnt0)
        rc = score(B._Off(), cnt0, cC, 'C_native', F.hook_counts(model))
    a = rc['nonstop_winner']
    assert a == b3_rec['a_token'] and rc['logits_sha256'] == b3_sha('C_native'), 'C_native differs from B3'
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
        cache_cc = lambda: P.n_cache(cT, cC, types, {l: fC[l] for l in G})                                   # noqa: E731
        cache_fix = lambda: P.n_cache(cT, cC, types, {l: PK.conv_subset(fT[l], fC[l], fixed, l) for l in G})  # noqa: E731
        hook = H.ReadoutHook({l: (lay[l].linear_attn.norm, Wbf[l]) for l in G}, nonfix)
        cnt2 = CF.Counter(model, G)
        off = B._Off()
        mrow = {}
        with ExitStack() as st:
            e = st.enter_context(LR.Entry(model, x_t))
            st.enter_context(hook)                       # registered before the Counter: Counter reads the post-hook rows
            st.enter_context(cnt2)
            exp2 = F.hook_counts(model)

            def run_arm(name, cache, mode=None, specs=None):
                hook.arm(k(name), mode, specs)
                try:
                    score(off, cnt2, cache, k(name), exp2, e)
                finally:
                    hook.disarm()
                assert hook.hits.get(k(name), {}) == {l: 1 for l in G}, ('readout hook hits', name)
                for l in G:                                   # Counter saw exactly what the hook returned
                    row = hook.rec[k(name)][l]
                    seen = cnt2.extra[k(name)][f'{l}:gated_norm_out'].reshape(K.NV, K.HD)
                    assert torch.equal(seen, row.get('post', row['pre'])), ('hook/counter mismatch', name, l)

            run_arm('CC', cache_cc())
            run_arm('CFIX', cache_fix())
            for name in ('CC', 'CFIX'):
                assert res[k(name)]['score']['logits_sha256'] == b3_sha(k('N:' + name)), ('replay vs B3', d, name)
                for l in G:                                   # audit path: F.linear(pre) == model's out_proj output
                    assert torch.equal(hook.rec[k(name)][l]['outproj_pre'], cnt2.extra[k(name)][f'{l}:out_proj']), ('out_proj audit path', name, l)
            donor = {l: hook.rec[k('CC')][l]['pre'] for l in G}
            run_arm('K0', cache_cc(), 'clamp', donor)
            assert res[k('K0')]['score']['logits_sha256'] == res[k('CC')]['score']['logits_sha256'], ('K0 != CC', d)
            for name in ('K', 'K_early', 'K_late'):
                run_arm(name, cache_fix(), 'clamp', {l: donor[l] for l in CLAMP_LAYERS[name]})
                for l in CLAMP_LAYERS[name]:
                    m = nonfix[l]
                    assert torch.equal(hook.rec[k(name)][l]['post'][m.to(donor[l].device)], donor[l][m.to(donor[l].device)]), ('clamp rows', name, l)
            # K actual per-layer change (live, not the unclamped reference)
            dK, A, headK = {}, {}, {}
            for l in G:
                dg = (donor[l].float() - hook.rec[k('K')][l]['pre'].float())
                dg[~nonfix[l].to(dg.device)] = 0
                dK[l] = dg
                headK[l] = dg.norm(dim=1)
                A[l] = float((W32[l] @ dg.reshape(-1)).norm())
            # templates and per-layer scaling (no logit, rho or label of K is read here)
            specs = {'M_nat': {}, 'M_rand': {}}
            for arm in ('M_nat', 'M_rand'):
                info = {'constructible': True, 'layers': {}}
                for l in G:
                    if arm == 'M_nat':
                        raw = tmpl_next[d][l].to(donor[l].device)
                    else:
                        raw = torch.stack([K.seeded_gaussian(f'{item["id"]}|{d}|{l}|{h}', (K.HD,)) for h in range(K.NV)]).to(donor[l].device)
                    v, ok = K.build_template(raw, headK[l], nonfix[l])
                    sc = K.scale_layer(W32[l], v, A[l], donor[l])
                    if not ok:
                        sc = dict(sc, ok=False, reason='zero_template_direction')
                    info['constructible'] &= bool(ok and sc['ok'])
                    specs[arm][l] = (v * (sc['lambda'] or 0.0)) if sc['ok'] and not sc['near_zero'] else torch.zeros_like(v)
                    info['layers'][l] = {'A': A[l], 'lambda': sc['lambda'], 'near_zero': sc['near_zero'], 'ok': bool(ok and sc['ok']),
                                         'reason': sc.get('reason'), 'thr': sc['thr'],
                                         'template_head_norms_pre_scale': [float(x) for x in v.norm(dim=1)],
                                         'K_head_norms': [float(x) for x in headK[l]]}
                mrow[arm] = info
            for arm in ('M_nat', 'M_rand'):
                run_arm(arm, cache_fix(), 'add', specs[arm])
            # matching gates on the actual BF16 hook differences (unit-level: failure -> comparison not judgeable)
            for arm in ('M_nat', 'M_rand', 'K'):
                worst_p, worst_a = 0.0, 0.0
                for l in G:
                    row = hook.rec[k(arm)][l]
                    if 'post' not in row:
                        continue
                    act = row['post'].float() - row['pre'].float()
                    lin = W32[l] @ act.reshape(-1)
                    real = cnt2.extra[k(arm)][f'{l}:out_proj'].float() - row['outproj_pre'].float()
                    near = arm != 'K' and mrow[arm]['layers'][l]['near_zero']
                    if near or float(lin.norm()) == 0:
                        continue
                    if arm != 'K':
                        worst_p = max(worst_p, abs(float(lin.norm()) - A[l]) / A[l])
                    worst_a = max(worst_a, float((real - lin).norm()) / float(lin.norm()))
                if arm == 'K':
                    mrow['K_outproj_audit_max_rel'] = worst_a
                else:
                    mrow[arm]['projection_rel_err_max'] = worst_p
                    mrow[arm]['outproj_audit_rel_err_max'] = worst_a
                    mrow[arm]['matched'] = bool(mrow[arm]['constructible'] and worst_p <= K.RULE['match_rel'] and worst_a <= K.RULE['match_rel'])
            matching[d] = mrow
            saved[d] = {'K_diff': {l: dK[l].to(torch.bfloat16).cpu() for l in G}, 'donor_CC': {l: donor[l].cpu() for l in G},
                        'K_pre': {l: hook.rec[k('K')][l]['pre'].cpu() for l in G},
                        'M_delta': {arm: {l: specs[arm][l].cpu() for l in G} for arm in specs},
                        'M_actual_diff': {arm: {l: (hook.rec[k(arm)][l]['post'].float() - hook.rec[k(arm)][l]['pre'].float()).to(torch.bfloat16).cpu()
                                                for l in G} for arm in specs}}
        del cT, rec1, cnt1, cnt2, hook
    gates['calibration'] = 'scenario f0 calibration (in process) equals C1-P/B3 records exactly'
    gates['write'] = 'every direction: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'C_native, T_native, N:CC, N:CFIX logits bitwise == B3'
    gates['K0'] = 'CC + clamp to its own donor == CC bitwise'
    gates['hooks'] = 'readout hook once per G layer per N score; Counter reads exactly the hook output; FIX rows never written; clamped rows == donor'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never; entry hook once per N cell'
    gates['audit_path'] = 'F.linear(pre) == recorded out_proj output for CC and CFIX'
    for key, z in logits.items():
        res[key]['readout'] = CFK.readout(z, a)
    body = {'a_token': a, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits,
            'FIX': fixed, 'cells': res, 'matching': matching, 'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, {'logits': logits, 'saved': saved}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', SHADOW] + PLAN_DOCS
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
    tmpl = b3_templates(sorted({next_scenario(u['item_id']) for u in units}))
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
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, fixed, b3_rec,
                                 tmpl[next_scenario(item['id'])], output, preflight=(stage == 'preflight'))
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
    lock = open(f'/tmp/acupuncture-b4-worker{worker}.lock', 'w')
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
    want = {'C_native'} | {f'T_native|{d}' for d in K.DIRECTIONS} | {f'{a}|{d}' for a in N_ARMS for d in K.DIRECTIONS}
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('calibration', 'write', 'replay', 'K0', 'hooks', 'kernel', 'audit_path'):
            assert rec['gates'][g], g
        assert set(rec['matching']) == set(K.DIRECTIONS)
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
            cmd = [sys.executable, '-u', str(HERE / 'b4_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
