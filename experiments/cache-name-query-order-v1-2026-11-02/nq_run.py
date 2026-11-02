"""NQ-01: name query x record order on a label-free panel (6 scenarios x 3 cyclic orders x 3 queried items) — natural bounded
continuation plus the shared-prefix step-2 diagnostic fork (plan docs/cache-name-query-order-plan-v2-2026-11-02.zh-CN.md;
CONTRACT.zh-CN.md r01).

Query before the record; injection window b+1..n-2 = the fixed trailing instruction + chat-template tail, identical token ids for
all 54 inputs (frozen in data/tokens-r01.json).  One calibration per scenario (reference NQxx-ABC-A), shared by its 9 prompts.
Per input: C_nat.  Per direction (N4146, N1210, R0, C1343): T_nat, T_V (all deep value heads' conv V from C, q/k T), T_F (whole
deep conv from C).  Restoration once at the start; 32 new tokens max; greedy argmax; stop set {248044, 248046}; no forcing.
Preflight also replays SVQ-01 on SP01-f0 with the unchanged SVQ runner.
python nq_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
SVQ_DIR = HERE.parent / 'cache-sp-v-qk-delivery-v1-2026-11-02'
sys.path.insert(0, str(SVQ_DIR))
sys.path.insert(0, str(HERE))
import svq_run as SVQ  # noqa: E402  (frozen SVQ-01 runner: generation + diagnostic fork, conv_mix, model chain, SP replay)

SPR, NRR, FC_DIR, SP_DIR = SVQ.SPR, SVQ.NRR, SVQ.FC_DIR, SVQ.SP_DIR
B3R, V, P, PK, X = SVQ.B3R, SVQ.V, SVQ.P, SVQ.PK, SVQ.X
CF, CFK, LR, B = SVQ.CF, SVQ.CFK, SVQ.LR, SVQ.B
F, L, T1, exp, K = SVQ.F, SVQ.L, SVQ.T1, SVQ.exp, SVQ.K

PLAN_ID = 'NQ-01-NAME-QUERY-ORDER-v2'
PLAN_DOCS = [REPO / 'docs/cache-name-query-order-plan-v2-2026-11-02.zh-CN.md',
             REPO / 'docs/cache-name-query-order-self-check-v2-2026-11-02.zh-CN.md']
INPUTS = HERE / 'data/inputs-r01.json'
TOKENS = HERE / 'data/tokens-r01.json'
SVQ_FORMAL = SVQ_DIR / 'runs/formal-r01'
SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = SVQ.SP_FORMAL, SVQ.NR_FORMAL, SVQ.B3_FORMAL, SVQ.XC_FORMAL, SVQ.SK_FORMAL
SPLIT = 13
DIRECTIONS = SVQ.DIRECTIONS
PREFLIGHT_ITEMS = ('NQ01-ABC-A',)
REPLAY_ITEM = 'SP01-f0'
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = SVQ.STOP
LIMITS = {'preflight': {'formations': 12, 'trajectories': 32, 'decode_forwards': 1024, 'diagnostics': 32, 'calibrations': 2},
          'formal': {'formations': 270, 'trajectories': 702, 'decode_forwards': 22464, 'diagnostics': 702, 'calibrations': 6}}
STORAGE_LIMIT = 8 * 2 ** 30
T_ARMS = ('T_nat', 'T_V', 'T_F')
QK = SVQ.QK
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = SVQ.COUNT_KEYS
comp_sha = NRR.comp_sha
conditions, shared_tokens, conv_mix, generate = SVQ.conditions, SVQ.shared_tokens, SVQ.conv_mix, SVQ.generate


def items():
    return exp.read(INPUTS)['items']


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
        return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows] + \
            [{'item_id': REPLAY_ITEM, 'base_id': 'SP01', 'key': f'REPLAY-{REPLAY_ITEM}', 'replay': True}]
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def tok_text(tok, ids):
    return tok.decode(ids, skip_special_tokens=False)


def svq_record(item_id):
    for w in sorted(SVQ_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'SVQ record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def run_item(engine, item, context, calib, conds, tokrec, output, preflight=False):
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
    t_item = tokrec['items'][item['id']]
    assert exp.digest(prompt) == t_item['prompt_token_sha256'] and b == t_item['b'] and n == t_item['n'], 'prompt tokens != token audit'
    assert exp.digest(prompt[b + 1:n - 1]) == tokrec['window_token_sha256'], 'injection window differs from the frozen window'
    counts = {k: 0 for k in COUNT_KEYS}
    traj, tensors, gates, audits = {}, {}, {}, {}
    ans, others = item['target'], list(item['distractors'])
    q_shared, t2, d2 = shared_tokens(tok, item)
    assert (q_shared, t2, list(d2)) == (t_item['q_shared'], t_item['second_tokens']['target'], t_item['second_tokens']['distractors'])
    watch = [t2] + list(d2)
    code_tok = {ans: t2, **dict(zip(others, d2))}
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    base_sha = comp_sha(base, types, ALLK, 0)
    cC = P.form(engine, base, prefix, window, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(window)
    assert comp_sha(base, types, ALLK, 0) == base_sha, 'shared pre-window cache modified by formation'
    allC = comp_sha(cC, types, ALLK, 0)

    def run(name, cache):
        F.assert_no_hooks(model)
        r, lg = generate(engine, cache, last, n, q_shared, watch, types, counts)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        tensors[name] = lg
        if r['ids'][0] == q_shared and len(r['ids']) > 1:
            assert r['diag']['watch'] == r['first']['step2'] and r['diag']['logits_sha256'] == r['first']['step2_logits_sha256'], ('diag != natural step 2', name)
        return r

    c_nat = run('C_nat', cC)
    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        audits[d] = au
        cT = P.form(engine, base, prefix, window, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(window)
        assert comp_sha(base, types, ALLK, 0) == base_sha, 'shared pre-window cache modified by formation'
        allT = comp_sha(cT, types, ALLK, 0)
        k = lambda a: f'{a}|{d}'   # noqa: E731
        caches = {'T_nat': cT, 'T_V': conv_mix(cT, cC, G, 'T', 'C'), 'T_F': NRR.restore(cT, cC, types, '010')}
        hT = {'X': NRR.comp_sha_range(cT, types, ALLK, 0, SPLIT), 'S': comp_sha(cT, types, ('recurrent',)), 'KV': comp_sha(cT, types, ('kv',))}
        for arm, (qs, vs) in {'T_V': ('T', 'C'), 'T_F': ('C', 'C')}.items():
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
    gates['tokens'] = 'prompt ids, b, n, shared/second tokens equal the frozen token audit; injection window ids equal the frozen window'
    gates['calibration'] = 'one calibration per scenario on NQxx-ABC-A, shared by its 9 prompts (formal NQ01 == preflight)'
    gates['write'] = 'every needle: BF16 nominal L0 write norm within 1% of |dose| x scale'
    gates['prefix'] = 'C and all T share one hook-free pre-window cache (hash unchanged across formations)'
    gates['diag_internal'] = 'every arm whose first token is q_shared: fork == own natural step 2 (watch values and full-logit hash)'
    gates['assembly'] = 'T_V: q/k T, V C; T_F: conv C (exact per channel block); S/KV/shallow == T; C != T per block; donors unchanged'
    body = {'answer': ans, 'distractors': others, 'code_tokens': {c: t for c, t in code_tok.items()}, 'q_shared': q_shared,
            'q_shared_text': tok.decode([q_shared]), 'second_tokens': {'target': t2, 'distractors': list(d2)},
            'prompt_token_sha256': exp.digest(prompt), 'pre_window_cache_sha256': base_sha, 'calibration': calib,
            'write_audits': audits, 'trajectories': traj, 'counts': counts, 'gates': gates, 'b': b, 'n': n, 'window': len(window)}
    return body, tensors


def run_replay(engine, conds, output):
    """Preflight history replay: SVQ-01 SP01-f0 through the unchanged SVQ runner (its own SP-01 gates), then every trajectory
    (ids, first-step hash, caches, diagnostic watch values) equals the SVQ-01 formal record, T_V and T_QK included."""
    tok = engine.tokenizer
    it = [r for r in SVQ.items() if r['id'] == REPLAY_ITEM][0]
    ctx = exp.contexts_for(tok, [it])[it['id']]
    calib = engine.calibrate([ctx])[0]
    assert it['reference_id'] == it['id'] and calib == SVQ.sp_calibration(it['id']), 'SP01-f0 calibration differs from SP-01'
    sp_rec, _ = SVQ.sp_record(it['id'])
    body, tensors = SVQ.run_item(engine, it, ctx, calib, conds, sp_rec, output, preflight=False)
    old = svq_record(it['id'])['trajectories']
    assert set(body['trajectories']) == set(old), 'replay arm set differs from SVQ-01'
    for name, r in body['trajectories'].items():
        o = old[name]
        assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'], ('replay != SVQ-01', name)
        assert r['first']['cache_sha256'] == o['first']['cache_sha256'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('replay cache', name)
        assert r['diag'] == o['diag'], ('replay diagnostic != SVQ-01', name)
    body['gates']['svq_replay'] = 'SP01-f0 through the SVQ runner == SVQ-01 formal record for all 17 trajectories (ids, hashes, diagnostics)'
    body['replay_of'] = 'cache-sp-v-qk-delivery-v1-2026-11-02 formal-r01 SP01-f0'
    return it, calib, body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', INPUTS, TOKENS, SVQ_DIR / 'svq_run.py', SVQ_DIR / 'svq_core.py', SP_DIR / 'sp_run.py', SP_DIR / 'sp_core.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    sp = [w / 'receipt.json' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir()] + [SP_FORMAL / 'verification.json']
    sp += [w / f'calibrations/{c.name}' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    svq = [w / 'receipt.json' for w in sorted(SVQ_FORMAL.glob('worker-*')) if w.is_dir()] + [SVQ_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + sp + svq + [p for p in B3R.frozen_paths() if p not in own]


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
    tokrec = exp.read(TOKENS)
    assert tokrec['passed'] is True
    for u in units:
        started = time.monotonic()
        if u.get('replay'):
            item, c_sp, body, tensors = run_replay(engine, conds, output)
            totals['calibrations'] += 1
        else:
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
            body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, tokrec, output, preflight=(stage == 'preflight'))
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
    lock = open(f'/tmp/acupuncture-nq-worker{worker}.lock', 'w')
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
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
        assert all(t['diag'] and 'watch' in t['diag'] for t in rec['trajectories'].values()), 'missing diagnostic'
        if rec['unit'].get('replay'):
            assert rec['gates']['svq_replay'] and len(rec['trajectories']) == 17
            continue
        want = {'C_nat'} | {f'{a}|{d}' for a in T_ARMS for d in DIRECTIONS}
        first = r['stage'] == 'preflight' and rec['item']['id'] == PREFLIGHT_ITEMS[0]
        if first:
            want |= {'REBUILD:C_nat', f'REBUILD:T_nat|{OFF_DIR}'}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        for g in ('tokens', 'calibration', 'write', 'prefix', 'diag_internal', 'assembly') + (('rebuild',) if first else ()):
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
            cmd = [sys.executable, '-u', str(HERE / 'nq_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (54 if stage == 'formal' else len(PREFLIGHT_ITEMS) + 1), units
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
