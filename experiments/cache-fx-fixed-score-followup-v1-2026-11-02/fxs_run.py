"""FXS-01: first-step fixed-candidate continuous scores for the FX-01 restoration arms
(plan docs/cache-fx-fixed-score-followup-plan-v1-2026-11-02.zh-CN.md + amendments v2; CONTRACT.zh-CN.md r01).

Per input: C.  Per direction: T_nat, T_V, T_FIXV, T_RESTV, T_U, T_Ubar (complement of the frozen U in the 448 deep value heads).
Each arm is ONE scoring forward of the last prompt token from an independent clone of the restored start cache; no generation.
Full-vocabulary logits are kept in their original dtype (tensors/, hashes in the receipt); selected values go to the record.
python fxs_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
FX_DIR = HERE.parent / 'cache-fixed-v-delivery-v1-2026-11-02'
sys.path.insert(0, str(FX_DIR))
sys.path.insert(0, str(HERE))
import fx_run as FXR  # noqa: E402  (frozen FX-01 runner: v_restore, record readers, head lists, model chain)

NRR, FC_DIR = FXR.NRR, FXR.FC_DIR
B3R, V, P, PK, X = FXR.B3R, FXR.V, FXR.P, FXR.PK, FXR.X
CF, CFK, LR, B = FXR.CF, FXR.CFK, FXR.LR, FXR.B
F, L, T1, exp = FXR.F, FXR.L, FXR.T1, FXR.exp

PLAN_ID = 'FXS-01-FIXED-SCORE-FOLLOWUP-v1'
PLAN_DOCS = [REPO / 'docs/cache-fx-fixed-score-followup-plan-v1-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-v-followup-self-check-v1-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-v-followup-amendments-v2-2026-11-02.zh-CN.md']
FX_FORMAL = FX_DIR / 'runs/formal-r01'
FIXED, URAND, FIXED_SHA, URAND_SHA = FXR.FIXED, FXR.URAND, FXR.FIXED_SHA, FXR.URAND_SHA
NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL, FC_FORMAL = FXR.NR_FORMAL, FXR.B3_FORMAL, FXR.XC_FORMAL, FXR.SK_FORMAL, FXR.FC_FORMAL
SPLIT = 13
DIRECTIONS = FXR.DIRECTIONS
PREFLIGHT_ITEMS = ('P01-f0', 'P01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = (248044, 248046)
S0 = 248046                                    # frozen fixed stop candidate (plan §3)
LIMITS = {'preflight': {'formations': 12, 'scores': 52, 'calibrations': 1},
          'formal': {'formations': 60, 'scores': 300, 'calibrations': 6}}
STORAGE_LIMIT = 2 * 2 ** 30
T_ARMS = ('T_nat', 'T_V', 'T_FIXV', 'T_RESTV', 'T_U', 'T_Ubar')
OLD_ARMS = ('T_nat', 'T_V', 'T_FIXV', 'T_RESTV', 'T_U')     # first-step hashes exist in the FX-01 formal records
NV, HD = 32, 128
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'scores', 'prefix_prefills', 'formation_token_forwards')
comp_sha = NRR.comp_sha
items, plan, conditions, b3_record, nr_record, fc_record = FXR.items, FXR.plan, FXR.conditions, FXR.b3_record, FXR.nr_record, FXR.fc_record
v_restore, restored_norm = FXR.v_restore, FXR.restored_norm


def fx_record(item_id):
    for w in sorted(FX_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'FX record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def spacing(v, dtype_name):
    """Gap between adjacent representable numbers at |v| for the dtype the logit was produced in (plan §3 precision)."""
    mant = {'torch.bfloat16': 7, 'torch.float16': 10, 'torch.float32': 23}[dtype_name]
    if v == 0:
        return 0.0
    return 2.0 ** (math.floor(math.log2(abs(v))) - mant)


def readout(z, raw_dtype, q0):
    """Selected first-step values (z = float32 view of the raw logits)."""
    import torch
    zq, zs = float(z[q0]), float(z[S0])
    zz = z.clone()
    zz[q0] = -float('inf')
    other = int(zz.argmax())
    stop_vals = {str(s): float(z[s]) for s in STOP}
    dn = str(raw_dtype)
    return {'q0': zq, 's0': zs, 'm': zq - zs, 'argmax': int(z.argmax()), 'q0_rank': int((z > z[q0]).sum()),
            'other_max_token': other, 'other_max': float(z[other]), 'q0_minus_other_max': zq - float(z[other]),
            'stop': stop_vals, 'stop_winner': max(STOP, key=lambda s: float(z[s])), 'dtype': dn,
            'spacing': {'q0': spacing(zq, dn), 's0': spacing(zs, dn)}}


def heads_sets(G, fixed, urand):
    allheads = [[l, h] for l in G for h in range(NV)]
    fixset = {(x[0], x[1]) for x in fixed}
    uset = {(x[0], x[1]) for x in urand}
    rest = [x for x in allheads if (x[0], x[1]) not in fixset]
    ubar = [x for x in allheads if (x[0], x[1]) not in uset]
    assert len(fixed) == len(urand) == 45 and len(fixset) == len(uset) == 45
    assert len(rest) == len(ubar) == 403
    assert sorted(x[0] for x in urand) == sorted(x[0] for x in fixed), 'U not layer-matched to FIX'
    assert sorted(x[0] for x in ubar) == sorted(x[0] for x in rest), 'Ubar not layer-matched to REST'
    return {'T_V': allheads, 'T_FIXV': fixed, 'T_RESTV': rest, 'T_U': urand, 'T_Ubar': ubar}


def run_item(engine, item, context, calib, conds, b3_rec, nr_rec, fx_rec, fixed, urand, output, preflight=False):
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
    assert exp.digest(prompt) == b3_rec['prompt_token_sha256'] == fx_rec['prompt_token_sha256'], 'prompt tokens differ from B3/FX'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {k: 0 for k in COUNT_KEYS}
    scores, tensors, gates, audits, cov = {}, {}, {}, {}, {}
    q0 = fx_rec['trajectories']['C_nat']['ids'][0]             # frozen: clean first token (FX-01 C_nat)
    assert q0 not in STOP, 'C_nat first token is a stop token'
    sets = heads_sets(G, fixed, urand)
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    allC = comp_sha(cC, types, ALLK, 0)
    nr_sha = lambda key: nr_rec['cells'][key]['score']['logits_sha256']   # noqa: E731

    def score(name, cache0):
        F.assert_no_hooks(model)
        cache = copy.deepcopy(cache0)
        with torch.inference_mode():
            out = L.forward(model, [last], n - 1, cache)
        counts['scores'] += 1
        raw = out.logits[0, -1]
        z = raw.float()
        assert torch.isfinite(z).all()
        r = readout(z, raw.dtype, q0)
        r['logits_sha256'] = F.th(z)
        r['cache_sha256'] = comp_sha(out.past_key_values, types, ALLK, 0)
        tensors[name] = raw.detach().to('cpu').clone()
        scores[name] = r
        return r

    def old_first(arm):
        return fx_rec['trajectories'][arm]['first']

    c = score('C', cC)
    assert c['logits_sha256'] == nr_sha('C_native') == old_first('C_nat')['logits_sha256'], 'C first step != NR / FX'
    assert c['cache_sha256'] == old_first('C_nat')['cache_sha256'], 'C updated cache != FX'
    assert c['argmax'] == q0, 'C argmax != frozen q0'
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
        caches = {'T_nat': cT}
        hT = {'X': NRR.comp_sha_range(cT, types, ALLK, 0, SPLIT), 'S': comp_sha(cT, types, ('recurrent',)), 'KV': comp_sha(cT, types, ('kv',))}
        for arm, heads in sets.items():
            cc = v_restore(cT, cC, types, G, heads)
            h = {'X': NRR.comp_sha_range(cc, types, ALLK, 0, SPLIT), 'S': comp_sha(cc, types, ('recurrent',)), 'KV': comp_sha(cc, types, ('kv',))}
            assert h == hT, ('V arm touched non-conv state', arm, d)
            hs = {(x[0], x[1]) for x in heads}
            for l in G:
                got, fT, fC = L._get(cc.layers[l], 'conv_states'), L._get(cT.layers[l], 'conv_states'), L._get(cC.layers[l], 'conv_states')
                assert torch.equal(got[:, :4096], fT[:, :4096]), ('q/k conv must stay T', arm, l)
                for hh in range(NV):
                    sl = slice(4096 + HD * hh, 4096 + HD * (hh + 1))
                    assert torch.equal(got[:, sl], (fC if (l, hh) in hs else fT)[:, sl]), ('V layout', arm, l, hh)
            caches[arm] = cc
            cov[k(arm)] = restored_norm(cT, cC, G, heads)
        for arm in T_ARMS:
            score(k(arm), caches[arm])
        assert scores[k('T_nat')]['logits_sha256'] == nr_sha(k('T_native')), ('T first step != NR T_native', d)
        for arm in OLD_ARMS:
            o = old_first(k(arm))
            assert scores[k(arm)]['logits_sha256'] == o['logits_sha256'], ('first step != FX-01', arm, d)
            assert scores[k(arm)]['cache_sha256'] == o['cache_sha256'], ('updated cache != FX-01', arm, d)
            assert scores[k(arm)]['argmax'] == o['argmax'], ('argmax != FX-01', arm, d)
        assert comp_sha(cT, types, ALLK, 0) == allT and comp_sha(cC, types, ALLK, 0) == allC, ('donor changed', d)
        if preflight and item['id'] == PREFLIGHT_ITEMS[0] and d == OFF_DIR:
            cC2 = P.form(engine, base, prefix, window, None, calib)
            cT2 = P.form(engine, base, prefix, window, cond, calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(window)
            assert comp_sha(cC2, types, ALLK, 0) == allC and comp_sha(cT2, types, ALLK, 0) == allT, 'rebuild differs'
            r1 = score('REBUILD:C', cC2)
            r2 = score(f'REBUILD:T_nat|{d}', cT2)
            assert r1['logits_sha256'] == c['logits_sha256'] and r1['cache_sha256'] == c['cache_sha256'], 'rebuild C score differs'
            assert r2['logits_sha256'] == scores[k('T_nat')]['logits_sha256'] and r2['cache_sha256'] == scores[k('T_nat')]['cache_sha256'], 'rebuild T score differs'
            gates['rebuild'] = 'C and T(4146) rebuilt: caches hash-equal; first-step logits and updated cache identical'
            del cC2, cT2
        del cT, caches
    gates['calibration'] = 'scenario f0 calibration (in process) equals the B3 record exactly'
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['replay'] = ('first-step logits (float32 view of raw) and updated cache: C == FX C_nat (== NR C_native); '
                       'T_nat/T_V/T_FIXV/T_RESTV/T_U == FX-01 first step; T_nat == NR T_native')
    gates['assembly'] = ('V arms: q/k conv T, listed V head slots C, other V T (exact); S/KV/shallow == T; FIX+REST = U+Ubar = 448; '
                         'U layer-matched to FIX, Ubar to REST; donors unchanged; no hooks')
    body = {'q0': q0, 'q0_text': tok.decode([q0]), 's0': S0, 'prompt_token_sha256': exp.digest(prompt), 'calibration': calib,
            'write_audits': audits, 'scores': scores, 'restored_v_norm': cov,
            'U_overlap_with_FIX': len({tuple(x) for x in urand} & {tuple(x) for x in fixed}),
            'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', FIXED, URAND, FX_DIR / 'fx_run.py', FC_DIR / 'fc_core.py', FC_DIR / 'fc_run.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    fc = [w / 'receipt.json' for w in sorted(FC_FORMAL.glob('worker-*')) if w.is_dir()] + [FC_FORMAL / 'verification.json']
    fx = [w / 'receipt.json' for w in sorted(FX_FORMAL.glob('worker-*')) if w.is_dir()] + [FX_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + fc + fx + [p for p in B3R.frozen_paths() if p not in own]


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
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
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
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, b3_rec, nr_record(item['id']), fx_record(item['id']),
                                 fixed, exp.read(URAND)['subsets'][item['id']][0], output, preflight=(stage == 'preflight'))
        for k in COUNT_KEYS:
            totals[k] += body['counts'][k]
        rel_t = f'tensors/{u["key"]}.pt'
        (output / 'tensors').mkdir(exist_ok=True)
        assert not (output / rel_t).exists()
        torch.save(tensors, output / rel_t)
        receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
        body['tensor_file'] = rel_t
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
    lock = open(f'/tmp/acupuncture-fxs-worker{worker}.lock', 'w')
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
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        want = {'C'} | {f'{a}|{d}' for a in T_ARMS for d in DIRECTIONS}
        first = r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]
        if first:
            want |= {'REBUILD:C', f'REBUILD:T_nat|{OFF_DIR}'}
        assert set(rec['scores']) == want, set(rec['scores']) ^ want
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
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
            cmd = [sys.executable, '-u', str(HERE / 'fxs_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
