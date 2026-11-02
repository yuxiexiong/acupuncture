"""QST-01: does query-specific deep conv q/k history steer the full answer? (plan docs/cache-query-state-transfer-plan-v1-2026-11-02
.zh-CN.md + the three reviewed revisions in CONTRACT.zh-CN.md r01).  Receiver a, donor b (same scenario/order/record, same n):
  U(a,b)      receiver C(a); G conv V from C(a); G conv q/k from C(b)
  H_C(d,a,b)  receiver T(a,d); V from C(a); q/k from C(b)
  H_T(d,a,b)  receiver T(a,d); V from C(a); q/k from T(b,d)
  T_nat(d,a)  receiver T(a,d) unchanged
Everything else (shallow, recurrent S, full-attention KV) from the receiver; one replacement before reading the last prompt token;
natural greedy continuation + the shared-prefix diagnostic fork (SVQ generate).  Units are (scenario, order) groups.
python qst_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
QCD_DIR = HERE.parent / 'cache-coverage-dose-v1-2026-11-02'
sys.path.insert(0, str(QCD_DIR))
sys.path.insert(0, str(HERE))
import qcd_run as QCDR  # noqa: E402  (frozen QCD-01 runner and its QC/NQ/SVQ chain)

QCR, NQR, SVQ, NRR = QCDR.QCR, QCDR.NQR, QCDR.SVQ, QCDR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR = QCDR.FC_DIR, QCDR.SP_DIR, QCDR.SVQ_DIR, QCDR.NQ_DIR, QCDR.QC_DIR
B3R, V, P, PK, X = QCDR.B3R, QCDR.V, QCDR.P, QCDR.PK, QCDR.X
CF, CFK, LR, B = QCDR.CF, QCDR.CFK, QCDR.LR, QCDR.B
F, L, T1, exp, K = QCDR.F, QCDR.L, QCDR.T1, QCDR.exp, QCDR.K

PLAN_ID = 'QST-01-QUERY-STATE-TRANSFER-v1'
PLAN_DOCS = [REPO / 'docs/cache-query-state-transfer-plan-v1-2026-11-02.zh-CN.md', REPO / 'docs/cache-query-state-transfer-self-check-v1-2026-11-02.zh-CN.md']
DESIGN = HERE / 'data/design-r01.json'
QC_INPUTS, QC_TOKENS = QCDR.QC_INPUTS, QCDR.QC_TOKENS
QCD_G = QCD_DIR / 'runs/gformal-r01'
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QCDR.QC_FORMAL, QCDR.NQ_FORMAL, QCDR.SVQ_FORMAL, QCDR.SP_FORMAL, QCDR.NR_FORMAL, QCDR.B3_FORMAL, QCDR.XC_FORMAL, QCDR.SK_FORMAL
SPLIT = 13
DIRECTIONS = QCDR.DIRECTIONS
PREFLIGHT_GROUPS = ('NQ01-ABC', 'NQ02-ABC')
REBUILD_TEXTS = ('NA-NQ01-ABC-A', 'NA-NQ02-ABC-B')
SLOT_TEXT = 'NA-NQ01-ABC-A'
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = QCDR.STOP
LIMITS = {'preflight': {'formations': 30, 'trajectories': 150, 'decode_forwards': 4800, 'diagnostics': 150, 'slot_check_forwards': 1, 'calibrations': 0},
          'formal': {'formations': 240, 'trajectories': 1380, 'decode_forwards': 44160, 'diagnostics': 1380, 'slot_check_forwards': 0, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.25 * 3600, 'formal': 2.5 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
QK = SVQ.QK
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards', 'slot_check_forwards')
comp_sha = NRR.comp_sha
conditions, shared_tokens, generate = NQR.conditions, NQR.shared_tokens, NQR.generate


def design():
    return exp.read(DESIGN)


def items():
    return design()['texts']


def group_of(text_id):
    _, s, o, _q = text_id.split('-')
    return f'{s}-{o}'


def groups():
    g = {}
    for t in items():
        g.setdefault(group_of(t['id']), []).append(t['id'])
    return {k: sorted(v) for k, v in g.items()}


def plan(stage, worker, n_workers):
    gs = groups()
    if stage == 'preflight':
        return [{'item_id': k, 'base_id': k.split('-')[0], 'key': k} for k in PREFLIGHT_GROUPS]
    bases = list(dict.fromkeys(k.split('-')[0] for k in gs))
    mine = {b for i, b in enumerate(bases) if i % n_workers == worker}
    return [{'item_id': k, 'base_id': k.split('-')[0], 'key': k} for k in gs if k.split('-')[0] in mine]


def _g_record(text_id):
    for w in sorted(QCD_G.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{text_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'QCD G record hash'
            return exp.read(w / rel)
    raise KeyError(text_id)


def mix(recv, qk_src, v_src, G):
    """Deep G-layer conv: channels [0, 4096) (q/k) from qk_src, [4096, 8192) (V) from v_src; everything else from recv."""
    import torch
    c = copy.deepcopy(recv)
    for l in G:
        fq, fv = L._get(qk_src.layers[l], 'conv_states'), L._get(v_src.layers[l], 'conv_states')
        L._set(c.layers[l], 'conv_states', torch.cat([fq[:, :QK], fv[:, QK:]], dim=1).contiguous())
    return c


def check_mix(recv, qk_src, v_src, cc, types, G, label):
    import torch
    h = lambda c: {'X': NRR.comp_sha_range(c, types, ALLK, 0, SPLIT), 'S': comp_sha(c, types, ('recurrent',)), 'KV': comp_sha(c, types, ('kv',))}   # noqa: E731
    assert h(cc) == h(recv), ('mixed arm touched non-conv state', label)
    for l in G:
        got = L._get(cc.layers[l], 'conv_states')
        assert got.shape[1] == 2 * QK, ('conv width', label, l)
        assert torch.equal(got[:, :QK], L._get(qk_src.layers[l], 'conv_states')[:, :QK]), ('q/k source', label, l)
        assert torch.equal(got[:, QK:], L._get(v_src.layers[l], 'conv_states')[:, QK:]), ('V source', label, l)


def conv_snapshot(cache, G):
    return {l: L._get(cache.layers[l], 'conv_states').detach().clone() for l in G}


def assert_shift(before, after, G, label):
    """Sliding conv window: after one token, new slots [0:3] == old slots [1:4] in every G layer (kernel 4)."""
    import torch
    for l in G:
        assert before[l].shape[-1] == 4, ('conv kernel slots', label, l, tuple(before[l].shape))
        assert torch.equal(after[l][..., :3], before[l][..., 1:]), ('conv window did not shift', label, l)


def run_item(engine, unit, contexts, calib, conds, qctok, output, preflight=False):
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    D = design()
    T_by_id = {t['id']: t for t in D['texts']}
    members = groups()[unit['item_id']]
    pairs = [p for p in D['pairs'] if p['receiver'] in members]
    counts = {k: 0 for k in COUNT_KEYS}
    traj, tensors, gates, hashes, info = {}, {}, {}, {}, {}
    qi = QCDR.qc_items()
    C, T, ctxinfo = {}, {}, {}
    ns, lasts = set(), set()
    for a in members:
        plan_t = T_by_id[a]['plan']
        item = qi[plan_t['qc_broad_id']]
        seg = PK.label_tokens(tok, contexts[a], item['boundary_text'], encode_text)
        assert not seg['straddling_tokens'] and (seg['b'], seg['n']) == (plan_t['b_b'], plan_t['n'])
        prompt = seg['ids']
        assert exp.digest(prompt) == qctok['items'][item['id']]['prompt_token_sha256']
        prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
        ns.add(n), lasts.add(last)
        Bw = list(range(plan_t['p'], plan_t['e'] + 1))
        assert Bw == list(range(seg['b'] + 1, n - 1))
        F.assert_no_hooks(model)
        with torch.inference_mode():
            base = L.forward(model, list(prefix[:seg['b'] + 1]), 0, None).past_key_values
        counts['prefix_prefills'] += 1
        g = _g_record(a)
        assert comp_sha(base, types, ALLK, 0) == g['hashes']['base_b'], ('base_b != QCD G', a)
        C[a] = P.form(engine, base, prefix, Bw, None, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(Bw)
        assert comp_sha(C[a], types, ALLK, 0) == g['hashes']['C_b'], ('C != QCD G', a)
        for d, cond in conds.items():
            au = X.write_audit(engine, cond, calib)
            au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
            assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
            T[(a, d)] = P.form(engine, base, prefix, Bw, cond, calib)
            counts['formations'] += 1
            counts['formation_token_forwards'] += len(Bw)
            assert comp_sha(T[(a, d)], types, ALLK, 0) == g['hashes'][f'T_b|{d}'], ('T != QCD G', a, d)
        q_shared, t2, d2 = shared_tokens(tok, item)
        ctxinfo[a] = {'item': item, 'q_shared': q_shared, 'watch': [t2] + list(d2), 'g': g, 'last': last, 'n': n, 'prefix': prefix, 'base': base, 'Bw': Bw,
                      'code_tokens': {item['target']: t2, **dict(zip(item['distractors'], d2))}}
        hashes[a] = {'base_b': g['hashes']['base_b'], 'C': g['hashes']['C_b'], **{f'T|{d}': g['hashes'][f'T_b|{d}'] for d in conds}}
    assert len(ns) == 1 and len(lasts) == 1, 'group members differ in n or last prompt token'

    def run(name, cache, a):
        F.assert_no_hooks(model)
        ci = ctxinfo[a]
        r, lg = generate(engine, cache, ci['last'], ci['n'], ci['q_shared'], ci['watch'], types, counts)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        tensors[name] = lg
        if r['ids'][0] == ci['q_shared'] and len(r['ids']) > 1:
            assert r['diag']['watch'] == r['first']['step2'] and r['diag']['logits_sha256'] == r['first']['step2_logits_sha256'], ('diag != step 2', name)
        return r

    def same(name, r, o):
        assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'], ('replay != QCD', name)
        assert r['first']['cache_sha256'] == o['first']['cache_sha256'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('replay cache', name)
        assert r['diag'] == o['diag'], ('replay diag', name)

    donors_of = {a: sorted(p['donor'] for p in pairs if p['receiver'] == a) for a in members}
    for a in members:
        og = ctxinfo[a]['g']['trajectories']
        for b in donors_of[a]:
            cc = mix(C[a], C[b], C[a], G)
            check_mix(C[a], C[b], C[a], cc, types, G, f'U|{a}|{b}')
            r = run(f'U|-|{a}|{b}', cc, a)
            if b == a:
                same(f'U|-|{a}|{a}', r, og['C_b'])
            del cc
        for d in conds:
            r = run(f'T_nat|{d}|{a}|{a}', T[(a, d)], a)
            same(f'T_nat|{d}|{a}', r, og[f'T_b|{d}|nat'])
            for b in donors_of[a]:
                for arm, qk_src in (('H_C', C[b]), ('H_T', T[(b, d)])):
                    cc = mix(T[(a, d)], qk_src, C[a], G)
                    check_mix(T[(a, d)], qk_src, C[a], cc, types, G, f'{arm}|{d}|{a}|{b}')
                    if preflight and arm == 'H_C' and d == OFF_DIR and a == SLOT_TEXT and b != a and 'slot_readout' not in gates:
                        before = conv_snapshot(cc, G)
                        probe = copy.deepcopy(cc)
                        with torch.inference_mode():
                            out = L.forward(model, [ctxinfo[a]['last']], ctxinfo[a]['n'] - 1, probe)
                        counts['slot_check_forwards'] += 1
                        assert_shift(before, conv_snapshot(out.past_key_values, G), G, 'readout')
                        gates['slot_readout'] = 'first read-out step: new conv slots [0:3] == old slots [1:4] in all 14 G layers (stored 4, first read uses the old 3 + current)'
                        del probe, out
                    r = run(f'{arm}|{d}|{a}|{b}', cc, a)
                    if b == a:
                        same(f'{arm}|{d}|{a}', r, og[f'T_b|{d}|{"F_b" if arm == "H_C" else "V_b"}'])
                    del cc
    if preflight:
        for a in members:
            r = run(f'C|-|{a}', C[a], a)
            o = traj[f'U|-|{a}|{a}']
            assert r['ids'] == o['ids'] and r['first'] == o['first'] and r['diag'] == o['diag'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('C != U(a,a)', a)
        for a in members:
            if a not in REBUILD_TEXTS:
                continue
            ci = ctxinfo[a]
            with torch.inference_mode():
                base2 = L.forward(model, list(ci['prefix'][:ci['Bw'][0]]), 0, None).past_key_values
            counts['prefix_prefills'] += 1
            C2 = P.form(engine, base2, ci['prefix'], ci['Bw'], None, calib)
            T2 = P.form(engine, base2, ci['prefix'], ci['Bw'], conds[OFF_DIR], calib)
            counts['formations'] += 2
            counts['formation_token_forwards'] += 2 * len(ci['Bw'])
            assert comp_sha(C2, types, ALLK, 0) == hashes[a]['C'] and comp_sha(T2, types, ALLK, 0) == hashes[a][f'T|{OFF_DIR}'], ('rebuild differs', a)
            for nm, cache, ref in (('C', C2, f'U|-|{a}|{a}'), ('nat', T2, f'T_nat|{OFF_DIR}|{a}|{a}'),
                                   ('V', mix(T2, T2, C2, G), f'H_T|{OFF_DIR}|{a}|{a}'), ('F', mix(T2, C2, C2, G), f'H_C|{OFF_DIR}|{a}|{a}')):
                r = run(f'REBUILD:{nm}|{a}', cache, a)
                o = traj[ref]
                assert r['ids'] == o['ids'] and r['first'] == o['first'] and r['diag'] == o['diag'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('rebuild trajectory', nm, a)
            gates.setdefault('rebuild', []).append(a)
            del base2, C2, T2
        if SLOT_TEXT in members:
            ci = ctxinfo[SLOT_TEXT]
            cache = copy.deepcopy(ci['base'])
            for t in ci['Bw']:
                before = conv_snapshot(cache, G)
                cache, _ = F.forward_tokens(engine, cache, [ci['prefix'][t]], t, None, calib)
                assert_shift(before, conv_snapshot(cache, G), G, f'formation {t}')
            counts['formations'] += 1
            counts['formation_token_forwards'] += len(ci['Bw'])
            assert comp_sha(cache, types, ALLK, 0) == hashes[SLOT_TEXT]['C'], 'stepwise slot-check formation != C'
            gates['slot_formation'] = 'clean formation of NA-NQ01-ABC-A step by step: every step shifts the 4-slot conv window by one in all 14 G layers; final cache == C'
            del cache
    for a in members:
        assert comp_sha(ctxinfo[a]['base'], types, ALLK, 0) == hashes[a]['base_b'], ('base modified', a)
        assert comp_sha(C[a], types, ALLK, 0) == hashes[a]['C'], ('donor C modified', a)
        for d in conds:
            assert comp_sha(T[(a, d)], types, ALLK, 0) == hashes[a][f'T|{d}'], ('donor T modified', a, d)
    F.assert_no_hooks(model)
    gates['replay_qcd'] = 'U(a,a) == QCD C_b; H_C(d,a,a) == QCD T_b F_b; H_T(d,a,a) == QCD T_b V_b; T_nat == QCD T_b nat (ids, first-step and cache hashes, diagnostics)'
    gates['sources'] = 'base, C, T hashes == QCD G; every mixed arm: q/k block == donor, V block == C(a), S/KV/shallow == receiver; donors unchanged after all arms'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'group': unit['item_id'], 'members': members, 'pairs': pairs,
            'texts': {a: {'item': ctxinfo[a]['item'], 'code_tokens': ctxinfo[a]['code_tokens'], 'q_shared': ctxinfo[a]['q_shared']} for a in members},
            'hashes': hashes, 'calibration': calib, 'trajectories': traj, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, QCD_DIR / 'qcd_run.py', QCD_DIR / 'data/plan-r01.json', QC_DIR / 'qc_run.py', NQ_DIR / 'nq_run.py', NQ_DIR / 'nq_analysis.py', NQR.INPUTS, NQR.TOKENS, SVQ_DIR / 'svq_run.py', SP_DIR / 'sp_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    sp = [w / 'receipt.json' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir()] + [SP_FORMAL / 'verification.json']
    sp += [w / f'calibrations/{c.name}' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    svq = [w / 'receipt.json' for w in sorted(SVQ_FORMAL.glob('worker-*')) if w.is_dir()] + [SVQ_FORMAL / 'verification.json']
    nq = [w / 'receipt.json' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir()] + [NQ_FORMAL / 'verification.json']
    nq += [w / f'calibrations/{c.name}' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    qcd = [w / 'receipt.json' for w in sorted(QCD_G.glob('worker-*')) if w.is_dir()] + [QCD_G / 'verification.json']
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + [p for p in B3R.frozen_paths() if p not in own]


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
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = QCR.nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        body, tensors = run_item(engine, u, contexts, calib[rid], conds, qctok, output, preflight=(stage == 'preflight'))
        for k in COUNT_KEYS:
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        rel_t = f'tensors/{u["key"]}.pt'
        (output / 'tensors').mkdir(exist_ok=True)
        assert not (output / rel_t).exists()
        torch.save(tensors, output / rel_t)
        receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
        body['tensor_file'] = rel_t
        item = {'id': u['item_id']}
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
    lock = open(f'/tmp/acupuncture-qst-worker{worker}.lock', 'w')
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
        want = set()
        for p in rec['pairs']:
            want.add(f"U|-|{p['receiver']}|{p['donor']}")
            for d in DIRECTIONS:
                want |= {f"H_C|{d}|{p['receiver']}|{p['donor']}", f"H_T|{d}|{p['receiver']}|{p['donor']}"}
        for a in rec['members']:
            want |= {f'T_nat|{d}|{a}|{a}' for d in DIRECTIONS}
            if r['stage'] == 'preflight':
                want.add(f'C|-|{a}')
                if a in REBUILD_TEXTS:
                    want |= {f'REBUILD:{nm}|{a}' for nm in ('C', 'nat', 'V', 'F')}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        for g in ('replay_qcd', 'sources', 'calibration'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight' and rec['group'] == 'NQ01-ABC':
            assert rec['gates']['slot_readout'] and rec['gates']['slot_formation'] and rec['gates']['rebuild']
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
            cmd = [sys.executable, '-u', str(HERE / 'qst_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (18 if stage == 'formal' else len(PREFLIGHT_GROUPS)), units
        gpu_s = sum(x['wall_seconds'] for x in results)
        assert gpu_s <= GPU_CAP_S[stage], ('device-time cap exceeded', gpu_s)
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
