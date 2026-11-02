"""FX-01: does restoring the frozen 45-head conv V history recover full delivery in the native T background?
(plan docs/cache-fixed-v-delivery-plan-v1-2026-11-02.zh-CN.md; CONTRACT.zh-CN.md r01.)

Per input: C_nat.  Per direction: T_nat, T_F (all deep conv restored), T_V (all deep V restored, q/k T), T_FIXV (FIX heads' V),
T_RESTV (other heads' V), T_U (frozen layer-matched random 45 heads, C2 subsets[input][0]).  Natural greedy continuation.
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
import fc_run as FCR  # noqa: E402  (frozen FC-01 generation loop)

B3R, V, P, PK, X = NRR.B3R, NRR.V, NRR.P, NRR.PK, NRR.X
CF, CFK, LR, B = NRR.CF, NRR.CFK, NRR.LR, NRR.B
F, L, T1, exp = NRR.F, NRR.L, NRR.T1, NRR.exp

PLAN_ID = 'FX-01-FIXED-V-DELIVERY-v1'
PLAN_DOCS = [REPO / 'docs/cache-fixed-v-delivery-plan-v1-2026-11-02.zh-CN.md']
FC_FORMAL = FC_DIR / 'runs/formal-r01'
FIXED = HERE.parent / 'cache-head-rule-prospective-v1-2026-11-01/data/fixed-heads-r01.json'
URAND = HERE.parent / 'cache-c2-cross-direction-v1-2026-11-01/data/fix-random-r01.json'
FIXED_SHA = 'dbc7f13071d6c387079447d843c2c90e086638c8cd463c2b2d2274e6ea1ed3cb'
URAND_SHA = '5a2ddbcb122a232d5f2766435c567c52a13dbbf9f8c79e23b5b03a8aa1b31bb1'
NR_FORMAL = NR_DIR / 'runs/formal-r01'
B3_FORMAL = NRR.B3_FORMAL
XC_FORMAL = NRR.XC_FORMAL
SK_FORMAL = NRR.SK_FORMAL
SPLIT = 13
DIRECTIONS = NRR.DIRECTIONS
PREFLIGHT_ITEMS = ('P01-f0', 'P01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
MAX_NEW = 32
STOP = (248044, 248046)
LIMITS = {'preflight': {'formations': 12, 'trajectories': 52, 'decode_forwards': 1664, 'calibrations': 1},
          'formal': {'formations': 60, 'trajectories': 300, 'decode_forwards': 9600, 'calibrations': 6}}
STORAGE_LIMIT = 8 * 2 ** 30
T_ARMS = ('T_nat', 'T_F', 'T_V', 'T_FIXV', 'T_RESTV', 'T_U')
NV, HD = 32, 128
OFF_DIR = 'N_L00_C4146_D-1'
comp_sha = NRR.comp_sha


def items():
    return V.items()


def plan(stage, worker, n_workers):
    if stage == 'preflight':
        rows = [r for r in items() if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
        return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows]
    return V.plan(stage, worker, n_workers)


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


def generate(engine, cache0, last, n, mode, q0, types, counts):
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
        ids.append(t)
        steps.append({'token': t, 'masked': masked, 'forced': forced})
        if t in STOP:
            break
        tok_in, pos = t, pos + 1
    reason = 'stop' if ids[-1] in STOP else 'budget'
    return {'ids': ids, 'steps': steps, 'termination': reason, 'first': first, 'final_cache_sha256': comp_sha(cache, types, ALLK, 0)}


def fc_record(item_id):
    for w in sorted(FC_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'FC record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def v_restore(cT, cC, types, G, heads):
    """From T: restore the conv V channels of the listed (layer, head) to C; q/k conv, other V, S, KV, shallow stay T."""
    c = copy.deepcopy(cT)
    for l in G:
        fT, fC = L._get(cT.layers[l], 'conv_states'), L._get(cC.layers[l], 'conv_states')
        L._set(c.layers[l], 'conv_states', PK.conv_subset(fC, fT, heads, l))     # base = fT, listed V heads from fC
    return c


def restored_norm(cT, cC, G, heads):
    """Descriptive covariate (plan addition 2): norm of the conv V difference (C - T) over the restored slots."""
    import torch
    tot = 0.0
    hs = {(x[0], x[1]) for x in heads}
    for l in G:
        d = (L._get(cC.layers[l], 'conv_states').float() - L._get(cT.layers[l], 'conv_states').float())
        for h in range(NV):
            if (l, h) in hs:
                tot += float(d[:, 4096 + HD * h:4096 + HD * (h + 1), :].pow(2).sum())
    return tot ** 0.5


def run_item(engine, item, context, calib, conds, b3_rec, nr_rec, fc_rec, fixed, urand, output, preflight=False):
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
    assert exp.digest(prompt) == b3_rec['prompt_token_sha256'], 'prompt tokens differ from B3'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {'formations': 0, 'trajectories': 0, 'decode_forwards': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
    traj, gates, audits, cov = {}, {}, {}, {}
    allheads = [[l, h] for l in G for h in range(NV)]
    fixset = {(x[0], x[1]) for x in fixed}
    rest = [x for x in allheads if (x[0], x[1]) not in fixset]
    assert len(rest) + len(fixed) == len(allheads) == 448
    assert sorted(x[0] for x in urand) == sorted(x[0] for x in fixed), 'U not layer-matched to FIX'
    sets = {'T_V': allheads, 'T_FIXV': fixed, 'T_RESTV': rest, 'T_U': urand}
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    allC = comp_sha(cC, types, ALLK, 0)
    nr_sha = lambda key: nr_rec['cells'][key]['score']['logits_sha256']   # noqa: E731

    def run(name, cache):
        F.assert_no_hooks(model)
        r = FCR.generate(engine, cache, last, n, 'nat', None, types, counts)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        return r

    c_nat = run('C_nat', cC)
    assert c_nat['first']['logits_sha256'] == nr_sha('C_native'), 'C first step != NR C_native'
    assert c_nat['ids'] == fc_rec['trajectories']['C_nat']['ids'], 'C_nat != FC-01 C_nat'
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
        caches = {'T_nat': cT, 'T_F': NRR.restore(cT, cC, types, '010')}
        hT = {'X': NRR.comp_sha_range(cT, types, ALLK, 0, SPLIT), 'S': comp_sha(cT, types, ('recurrent',)), 'KV': comp_sha(cT, types, ('kv',))}
        for arm, heads in sets.items():
            c = v_restore(cT, cC, types, G, heads)
            h = {'X': NRR.comp_sha_range(c, types, ALLK, 0, SPLIT), 'S': comp_sha(c, types, ('recurrent',)), 'KV': comp_sha(c, types, ('kv',))}
            assert h == hT, ('V arm touched non-conv state', arm, d)
            hs = {(x[0], x[1]) for x in heads}
            for l in G:
                got, fT, fC = L._get(c.layers[l], 'conv_states'), L._get(cT.layers[l], 'conv_states'), L._get(cC.layers[l], 'conv_states')
                assert torch.equal(got[:, :4096], fT[:, :4096]), ('q/k conv must stay T', arm, l)
                for hh in range(NV):
                    sl = slice(4096 + HD * hh, 4096 + HD * (hh + 1))
                    assert torch.equal(got[:, sl], (fC if (l, hh) in hs else fT)[:, sl]), ('V layout', arm, l, hh)
            caches[arm] = c
            cov[k(arm)] = restored_norm(cT, cC, G, heads)
        for arm in T_ARMS:
            run(k(arm), caches[arm])
        assert traj[k('T_nat')]['first']['logits_sha256'] == nr_sha(k('T_native')), ('T first step != NR T_native', d)
        assert traj[k('T_F')]['first']['logits_sha256'] == nr_sha(k('R010')), ('T_F first step != NR R010', d)
        assert traj[k('T_nat')]['ids'] == fc_rec['trajectories'][k('T_nat')]['ids'], ('T_nat != FC-01', d)
        assert traj[k('T_F')]['ids'] == fc_rec['trajectories'][k('T_F')]['ids'], ('T_F != FC-01', d)
        assert comp_sha(cT, types, ALLK, 0) == allT and comp_sha(cC, types, ALLK, 0) == allC, ('donor changed', d)
        if preflight and item['id'] == PREFLIGHT_ITEMS[0] and d == OFF_DIR:
            cC2 = P.form(engine, base, prefix, window, None, calib)
            cT2 = P.form(engine, base, prefix, window, cond, calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(window)
            assert comp_sha(cC2, types, ALLK, 0) == allC and comp_sha(cT2, types, ALLK, 0) == allT, 'rebuild differs'
            r1 = run('REBUILD:C_nat', cC2)
            r2 = run(f'REBUILD:T_nat|{d}', cT2)
            assert r1['ids'] == c_nat['ids'] and r1['final_cache_sha256'] == c_nat['final_cache_sha256'], 'rebuild C trajectory differs'
            assert r2['ids'] == traj[k('T_nat')]['ids'] and r2['final_cache_sha256'] == traj[k('T_nat')]['final_cache_sha256'], 'rebuild T trajectory differs'
            gates['rebuild'] = 'C and T(4146) rebuilt: caches hash-equal; natural trajectories identical token-by-token and final cache'
            del cC2, cT2
        del cT, caches
    gates['calibration'] = 'scenario f0 calibration (in process) equals the B3 record exactly'
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = 'first-step logits: C == NR C_native, T_nat == NR T_native, T_F == NR R010; C_nat/T_nat/T_F trajectories == FC-01'
    gates['assembly'] = 'V arms: q/k conv T, listed V head slots C, other V T (exact); S/KV/shallow == T; FIX+REST = 448; U layer-matched; donors unchanged'
    body = {'answer': None, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits,
            'trajectories': traj, 'restored_v_norm': cov, 'U_overlap_with_FIX': len({tuple(x) for x in urand} & fixset),
            'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    body['answer'], body['distractors'] = K.answer_and_distractors(item['record'])
    return body, {}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', FIXED, URAND, FC_DIR / 'fc_core.py', FC_DIR / 'fc_run.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    fc = [w / 'receipt.json' for w in sorted(FC_FORMAL.glob('worker-*')) if w.is_dir()] + [FC_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + fc + [p for p in B3R.frozen_paths() if p not in own]


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
    assert exp.sha(FIXED) == FIXED_SHA and exp.sha(URAND) == URAND_SHA, 'frozen head lists changed'
    fixed = exp.read(FIXED)['heads']
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    totals = {'formations': 0, 'trajectories': 0, 'decode_forwards': 0, 'calibrations': 0, 'prefix_prefills': 0, 'formation_token_forwards': 0}
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
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, b3_rec, nr_record(item['id']), fc_record(item['id']),
                                 fixed, exp.read(URAND)['subsets'][item['id']][0], output, preflight=(stage == 'preflight'))
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
    lock = open(f'/tmp/acupuncture-fx-worker{worker}.lock', 'w')
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
        want = {'C_nat'} | {f'{a}|{d}' for a in T_ARMS for d in DIRECTIONS}
        first = r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]
        if first:
            want |= {'REBUILD:C_nat', f'REBUILD:T_nat|{OFF_DIR}'}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        for g in ('calibration', 'write', 'replay', 'assembly') + (('rebuild',) if first else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'fx_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
