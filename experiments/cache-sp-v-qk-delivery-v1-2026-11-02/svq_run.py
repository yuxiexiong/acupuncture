"""SVQ-01: V vs q/k conv restoration on the shared-first-token (SP) panel — natural bounded continuation plus a shared-prefix
step-2 diagnostic fork (plan docs/cache-sp-v-qk-delivery-plan-v1-2026-11-02.zh-CN.md + amendments v2; CONTRACT.zh-CN.md r01).

Per input: C_nat.  Per direction (N4146, N1210, R0, C1343): T_nat, T_V (all 448 deep value heads' conv V from C, q/k T),
T_QK (deep q/k conv from C, V T), T_F (whole deep conv from C).  Restoration once at the start; 32 new tokens max; greedy
(argmax); stop set {248044, 248046}; no needle, no forcing, no masking.
Diagnostic: after each trajectory's first scoring forward, the updated cache is cloned and fed the frozen shared first token
q_shared for exactly one forward; the three second-token candidates and the full logits are kept.  It never feeds the natural
trajectory.
python svq_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
SP_DIR = HERE.parent / 'cache-shared-prefix-continuation-v1-2026-11-02'
sys.path.insert(0, str(SP_DIR))
sys.path.insert(0, str(HERE))
import sp_run as SPR  # noqa: E402  (frozen SP-01 runner: panel, shared tokens, plan, conditions, model chain)

NRR, FC_DIR = SPR.NRR, SPR.FC_DIR
B3R, V, P, PK, X = SPR.B3R, SPR.V, SPR.P, SPR.PK, SPR.X
CF, CFK, LR, B = SPR.CF, SPR.CFK, SPR.LR, SPR.B
F, L, T1, exp, K = SPR.F, SPR.L, SPR.T1, SPR.exp, SPR.K

PLAN_ID = 'SVQ-01-SP-V-QK-DELIVERY-v1'
PLAN_DOCS = [REPO / 'docs/cache-sp-v-qk-delivery-plan-v1-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-v-followup-self-check-v1-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-v-followup-amendments-v2-2026-11-02.zh-CN.md']
INPUTS = SPR.INPUTS
SP_FORMAL = SP_DIR / 'runs/formal-r01'
NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = SPR.NR_FORMAL, SPR.B3_FORMAL, SPR.XC_FORMAL, SPR.SK_FORMAL
SPLIT = 13
DIRECTIONS = SPR.DIRECTIONS
PREFLIGHT_ITEMS = ('SP01-f0', 'SP01-f1')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
MAX_NEW = 32
STOP = (248044, 248046)
S0 = 248046
LIMITS = {'preflight': {'formations': 12, 'trajectories': 36, 'decode_forwards': 1152, 'diagnostics': 36, 'calibrations': 1},
          'formal': {'formations': 60, 'trajectories': 204, 'decode_forwards': 6528, 'diagnostics': 204, 'calibrations': 6}}
STORAGE_LIMIT = 8 * 2 ** 30
T_ARMS = ('T_nat', 'T_V', 'T_QK', 'T_F')
QK = 4096
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards')
comp_sha = NRR.comp_sha
items, plan, conditions, shared_tokens = SPR.items, SPR.plan, SPR.conditions, SPR.shared_tokens


def sp_record(item_id):
    for w in sorted(SP_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'SP record hash'
            return exp.read(w / rel), w
    raise KeyError(item_id)


def sp_calibration(rid):
    for w in sorted(SP_FORMAL.glob('worker-*')):
        p = w / f'calibrations/{rid}.json'
        if p.exists():
            return exp.read(p)
    raise KeyError(rid)


def conv_mix(cT, cC, G, qk_from, v_from):
    """Deep G-layer conv buffers: channels [0, 4096) (q/k) from qk_from, [4096, 8192) (V, all 32 value heads) from v_from."""
    import torch
    c = copy.deepcopy(cT)
    src = {'T': cT, 'C': cC}
    for l in G:
        fq = L._get(src[qk_from].layers[l], 'conv_states')
        fv = L._get(src[v_from].layers[l], 'conv_states')
        L._set(c.layers[l], 'conv_states', torch.cat([fq[:, :QK], fv[:, QK:]], dim=1).contiguous())
    return c


def watch_values(z, watch):
    return {str(w): float(z[w]) for w in watch}


def generate(engine, cache0, last, n, q_shared, watch, types, counts):
    """SP-01 natural greedy loop (identical feeding) + a diagnostic fork after the first scoring forward."""
    import torch
    model = engine.model
    cache = copy.deepcopy(cache0)
    ids, steps, logits = [], [], {}
    tok_in, pos = last, n - 1
    first, diag = {}, {}
    for step in range(MAX_NEW):
        with torch.inference_mode():
            out = L.forward(model, [tok_in], pos, cache)
        counts['decode_forwards'] += 1
        raw = out.logits[0, -1]
        z = raw.float()
        assert torch.isfinite(z).all()
        cache = out.past_key_values
        if step == 0:
            zz = z.clone()
            zz[q_shared] = -float('inf')
            first = {'logits_sha256': F.th(z), 'argmax': int(z.argmax()), 'cache_sha256': comp_sha(cache, types, ALLK, 0),
                     'q_shared': float(z[q_shared]), 's0': float(z[S0]), 'stop': {str(s): float(z[s]) for s in STOP},
                     'other_max_token': int(zz.argmax()), 'other_max': float(zz.max()), 'q_shared_rank': int((z > z[q_shared]).sum())}
            logits['step1'] = raw.detach().to('cpu').clone()
            fork = copy.deepcopy(cache)
            with torch.inference_mode():
                dout = L.forward(model, [q_shared], n, fork)
            counts['diagnostics'] += 1
            draw = dout.logits[0, -1]
            dz = draw.float()
            assert torch.isfinite(dz).all()
            diag = {'watch': watch_values(dz, watch), 'logits_sha256': F.th(dz), 'argmax': int(dz.argmax())}
            logits['diag'] = draw.detach().to('cpu').clone()
            del fork, dout
        elif step == 1:
            first['step2'] = watch_values(z, watch)
            first['step2_logits_sha256'] = F.th(z)
            logits['step2'] = raw.detach().to('cpu').clone()
        t = int(z.argmax())
        ids.append(t)
        steps.append({'token': t, 'masked': False, 'forced': False})
        if t in STOP:
            break
        tok_in, pos = t, pos + 1
    reason = 'stop' if ids[-1] in STOP else 'budget'
    return {'ids': ids, 'steps': steps, 'termination': reason, 'first': first, 'diag': diag,
            'final_cache_sha256': comp_sha(cache, types, ALLK, 0)}, logits


def run_item(engine, item, context, calib, conds, sp_rec, output, preflight=False):
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
    assert exp.digest(prompt) == sp_rec['prompt_token_sha256'], 'prompt tokens differ from SP-01'
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    window = list(range(b + 1, n - 1))
    counts = {k: 0 for k in COUNT_KEYS}
    traj, tensors, gates, audits = {}, {}, {}, {}
    ans, others = K.answer_and_distractors(item['record'])
    assert ans == item['target'] and sorted(others) == sorted(item['distractors']), 'panel answer extraction'
    q_shared, t2, d2 = shared_tokens(tok, item)
    assert (q_shared, t2, list(d2)) == (sp_rec['q_shared'], sp_rec['second_tokens']['target'], list(sp_rec['second_tokens']['distractors'])), 'tokens != SP-01'
    watch = [t2] + list(d2)
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    allC = comp_sha(cC, types, ALLK, 0)
    old = sp_rec['trajectories']

    def run(name, cache):
        F.assert_no_hooks(model)
        r, lg = generate(engine, cache, last, n, q_shared, watch, types, counts)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        tensors[name] = lg
        if r['ids'][0] == q_shared and len(r['ids']) > 1:   # internal: the fork equals the natural step 2 when prefixes agree
            assert r['diag']['watch'] == r['first']['step2'] and r['diag']['logits_sha256'] == r['first']['step2_logits_sha256'], ('diag != natural step 2', name)
        return r

    def same_as_sp(name, r, ref):
        assert r['ids'] == ref['ids'] and r['first']['logits_sha256'] == ref['first']['logits_sha256'], ('trajectory != SP-01', name)
        assert r['first']['cache_sha256'] == ref['first']['cache_sha256'] and r['final_cache_sha256'] == ref['final_cache_sha256'], ('cache != SP-01', name)
        if 'step2' in ref['first']:
            assert r['first']['step2'] == ref['first']['step2'], ('natural step 2 != SP-01', name)

    c_nat = run('C_nat', cC)
    same_as_sp('C_nat', c_nat, old['C_nat'])
    replay_diag = {'T_nat_vs_T_shared': 0, 'C_vs_natural': 0, 'T_F_vs_natural': 0, 'not_applicable': 0}
    if old['C_nat']['ids'][0] == q_shared:
        assert c_nat['diag']['watch'] == old['C_nat']['first']['step2'], 'C diag != SP-01 C_nat step 2'
        replay_diag['C_vs_natural'] += 1
    else:
        replay_diag['not_applicable'] += 1
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
        caches = {'T_nat': cT, 'T_V': conv_mix(cT, cC, G, 'T', 'C'), 'T_QK': conv_mix(cT, cC, G, 'C', 'T'), 'T_F': NRR.restore(cT, cC, types, '010')}
        hT = {'X': NRR.comp_sha_range(cT, types, ALLK, 0, SPLIT), 'S': comp_sha(cT, types, ('recurrent',)), 'KV': comp_sha(cT, types, ('kv',))}
        for arm, (qs, vs) in {'T_V': ('T', 'C'), 'T_QK': ('C', 'T'), 'T_F': ('C', 'C')}.items():
            cc = caches[arm]
            h = {'X': NRR.comp_sha_range(cc, types, ALLK, 0, SPLIT), 'S': comp_sha(cc, types, ('recurrent',)), 'KV': comp_sha(cc, types, ('kv',))}
            assert h == hT, ('arm touched non-conv state', arm, d)
            for l in G:
                got = L._get(cc.layers[l], 'conv_states')
                src = {'T': L._get(cT.layers[l], 'conv_states'), 'C': L._get(cC.layers[l], 'conv_states')}
                assert got.shape == src['T'].shape and got.shape[1] == 2 * QK, ('conv shape', arm, l, tuple(got.shape))
                assert torch.equal(got[:, :QK], src[qs][:, :QK]), ('q/k source', arm, l)
                assert torch.equal(got[:, QK:], src[vs][:, QK:]), ('V source', arm, l)
        for l in G:
            fT, fC = L._get(cT.layers[l], 'conv_states'), L._get(cC.layers[l], 'conv_states')
            assert not torch.equal(fT[:, :QK], fC[:, :QK]) and not torch.equal(fT[:, QK:], fC[:, QK:]), ('C == T block: restoration vacuous', l)
        for arm in T_ARMS:
            run(k(arm), caches[arm])
        same_as_sp(k('T_nat'), traj[k('T_nat')], old[k('T_nat')])
        same_as_sp(k('T_F'), traj[k('T_F')], old[k('T_F')])
        assert old[k('T_shared')]['ids'][0] == q_shared
        assert traj[k('T_nat')]['diag']['watch'] == old[k('T_shared')]['first']['step2'], ('T_nat diag != SP-01 T_shared step 2', d)
        replay_diag['T_nat_vs_T_shared'] += 1
        if old[k('T_F')]['ids'][0] == q_shared:
            assert traj[k('T_F')]['diag']['watch'] == old[k('T_F')]['first']['step2'], ('T_F diag != SP-01 T_F step 2', d)
            replay_diag['T_F_vs_natural'] += 1
        else:
            replay_diag['not_applicable'] += 1
        assert comp_sha(cT, types, ALLK, 0) == allT and comp_sha(cC, types, ALLK, 0) == allC, ('donor changed', d)
        if preflight and item['id'] == PREFLIGHT_ITEMS[0] and d == OFF_DIR:
            cC2 = P.form(engine, base, prefix, window, None, calib)
            cT2 = P.form(engine, base, prefix, window, cond, calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(window)
            assert comp_sha(cC2, types, ALLK, 0) == allC and comp_sha(cT2, types, ALLK, 0) == allT, 'rebuild differs'
            r1 = run('REBUILD:C_nat', cC2)
            r2 = run(f'REBUILD:T_nat|{d}', cT2)
            for a, b_ in ((r1, c_nat), (r2, traj[k('T_nat')])):
                assert a['ids'] == b_['ids'] and a['final_cache_sha256'] == b_['final_cache_sha256'] and a['diag'] == b_['diag'], 'rebuild differs'
            gates['rebuild'] = 'C and T(4146) rebuilt: caches hash-equal; trajectories, final cache and diagnostic identical'
            del cC2, cT2
        del cT, caches
    gates['calibration'] = 'scenario f0 calibration (in process) equals the SP-01 formal calibration exactly'
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['tokens'] = 'q_shared and second tokens recomputed from the tokenizer equal the SP-01 record'
    gates['replay'] = 'C_nat, T_nat, T_F == SP-01 token-by-token (first-step logits, caches, natural step-2 watch values)'
    gates['diag_replay'] = ('T_nat fork == SP-01 T_shared step 2 (every direction); C / T_F fork == SP-01 natural step 2 where '
                            'their first token was q_shared; every arm whose first token is q_shared: fork == own step 2')
    gates['assembly'] = 'T_V: q/k T, V C; T_QK: q/k C, V T; T_F: conv C (exact per channel block); S/KV/shallow == T; donors unchanged'
    body = {'answer': ans, 'distractors': others, 'q_shared': q_shared, 'q_shared_text': tok.decode([q_shared]),
            'second_tokens': {'target': t2, 'distractors': list(d2)}, 'diag_replay_counts': replay_diag,
            'prompt_token_sha256': exp.digest(prompt), 'calibration': calib, 'write_audits': audits, 'trajectories': traj,
            'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', INPUTS, SP_DIR / 'sp_run.py', SP_DIR / 'sp_core.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    sp = [w / 'receipt.json' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir()] + [SP_FORMAL / 'verification.json']
    sp += [w / f'calibrations/{c.name}' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    return own + b3 + xc + sk + nr + sp + [p for p in B3R.frozen_paths() if p not in own]


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
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    for u in units:
        item = rows[u['item_id']]
        rid = item['reference_id']
        if rid not in calib:
            F.assert_no_hooks(engine.model)
            calib[rid] = engine.calibrate([contexts[rid]])[0]
            totals['calibrations'] += 1
            assert calib[rid] == sp_calibration(rid), ('calibration differs from SP-01', rid)
            exp.write(output / f'calibrations/{rid}.json', calib[rid], immutable=True)
        started = time.monotonic()
        sp_rec, sp_w = sp_record(item['id'])
        assert int(sp_w.name.split('-')[1]) % 2 == gpu, ('GPU assignment differs from SP-01', item['id'])
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, sp_rec, output, preflight=(stage == 'preflight'))
        for k in COUNT_KEYS:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        rel_t = f'tensors/{u["key"]}.pt'
        (output / 'tensors').mkdir(exist_ok=True)
        assert not (output / rel_t).exists()
        torch.save(tensors, output / rel_t)
        receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
        body['tensor_file'] = rel_t
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
    lock = open(f'/tmp/acupuncture-svq-worker{worker}.lock', 'w')
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
        want = {'C_nat'} | {f'{a}|{d}' for a in T_ARMS for d in DIRECTIONS}
        first = r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]
        if first:
            want |= {'REBUILD:C_nat', f'REBUILD:T_nat|{OFF_DIR}'}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        assert all(t['diag'] and 'watch' in t['diag'] for t in rec['trajectories'].values()), 'missing diagnostic'
        assert rec['diag_replay_counts']['T_nat_vs_T_shared'] == len(DIRECTIONS)
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
        for g in ('calibration', 'write', 'tokens', 'replay', 'diag_replay', 'assembly') + (('rebuild',) if first else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'svq_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
