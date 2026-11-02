"""QCO-01: is there a cross-record common additive component of the needle-formed deep conv q/k history that removes (R) and
reproduces (A) the V-only answer effect?  (plan docs/cache-qst-review-and-common-offset-plan-v1-2026-11-02.zh-CN.md; CONTRACT r01)
Stages: preflight (2 inputs, zero-offset no-op arms), collect (save q/k conv slots of C and T for all 48 inputs), formal (6 arms).
Arms per input i, direction d (receiver T(i,d), G conv V from C(i), S/KV/shallow from T(i,d)):
  V: q/k = T(i,d)   F: q/k = C(i)   R: q/k = T - mu(-s,d)   A: q/k = C + mu(-s,d)   R_rand: T - r(-s,d)   A_rand: C + r(-s,d)
Edits touch only the three conv slots [1,4) of channels [0, 4096) (slot 0 is never read).  mu: leave-one-scenario-out, scenario
equal-weight mean of Delta = T - C (qco_offsets.py, frozen before any edited output).
python qco_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
QST_DIR = HERE.parent / 'cache-query-state-transfer-v1-2026-11-02'
sys.path.insert(0, str(QST_DIR))
sys.path.insert(0, str(HERE))
import qst_run as QSTR  # noqa: E402  (frozen QST-01 runner: design, groups, QCD G readers, mix, slot helpers)

QCDR, QCR, NQR, SVQ, NRR = QSTR.QCDR, QSTR.QCR, QSTR.NQR, QSTR.SVQ, QSTR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR = QSTR.FC_DIR, QSTR.SP_DIR, QSTR.SVQ_DIR, QSTR.NQ_DIR, QSTR.QC_DIR, QSTR.QCD_DIR
B3R, V, P, PK, X = QSTR.B3R, QSTR.V, QSTR.P, QSTR.PK, QSTR.X
CF, CFK, LR, B = QSTR.CF, QSTR.CFK, QSTR.LR, QSTR.B
F, L, T1, exp, K = QSTR.F, QSTR.L, QSTR.T1, QSTR.exp, QSTR.K

PLAN_ID = 'QCO-01-COMMON-OFFSET-v1'
PLAN_DOCS = [REPO / 'docs/cache-qst-review-and-common-offset-plan-v1-2026-11-02.zh-CN.md', REPO / 'docs/cache-qco-self-check-v1-2026-11-02.zh-CN.md']
DESIGN = QSTR.DESIGN
QC_INPUTS, QC_TOKENS = QSTR.QC_INPUTS, QSTR.QC_TOKENS
QCD_G, QST_FORMAL = QSTR.QCD_G, QST_DIR / 'runs/formal-r01'
COLLECT = HERE / 'runs/collect-r01'
OFFSETS_PT = HERE / 'runs/offsets-r01/offsets.pt'
OFFSETS_MANIFEST = HERE / 'analysis/offsets-manifest-r01.json'
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QSTR.QC_FORMAL, QSTR.NQ_FORMAL, QSTR.SVQ_FORMAL, QSTR.SP_FORMAL, QSTR.NR_FORMAL, QSTR.B3_FORMAL, QSTR.XC_FORMAL, QSTR.SK_FORMAL
SPLIT = 13
DIRECTIONS = QSTR.DIRECTIONS
PREFLIGHT_ITEMS = ('NA-NQ01-ABC-A', 'NA-NQ02-ABC-B')
STAGES = ('preflight', 'collect', 'formal')
MAX_WORKERS = {'preflight': 1, 'collect': 2, 'formal': 2}
STOP = QSTR.STOP
LIMITS = {'preflight': {'formations': 10, 'trajectories': 42, 'decode_forwards': 1344, 'diagnostics': 42, 'calibrations': 0},
          'collect': {'formations': 240, 'trajectories': 0, 'decode_forwards': 0, 'diagnostics': 0, 'calibrations': 0},
          'formal': {'formations': 240, 'trajectories': 1392, 'decode_forwards': 44544, 'diagnostics': 1392, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.25 * 3600, 'collect': 0.5 * 3600, 'formal': 2.0 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
QK, HALF = SVQ.QK, 2048
EDIT_SLOTS = slice(1, 4)
NORM_TOL = 0.05
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards')
ARMS = ('V', 'F', 'R', 'A', 'R_rand', 'A_rand')
comp_sha = NRR.comp_sha
conditions, shared_tokens, generate, mix = QSTR.conditions, QSTR.shared_tokens, QSTR.generate, QSTR.mix


def items():
    return QSTR.items()


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        return [{'item_id': i, 'base_id': i.split('-')[1], 'key': i} for i in PREFLIGHT_ITEMS]
    bases = list(dict.fromkeys(t['plan']['base_id'] for t in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': t['id'], 'base_id': t['plan']['base_id'], 'key': t['id']} for t in rows if t['plan']['base_id'] in mine]


def qst_traj():
    out = {}
    for w in sorted(QST_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'QST record hash'
            out.update(exp.read(w / rel)['trajectories'])
    return out


def qk_tensor(cache, G):
    """[len(G), 4096, 4] q/k block of the deep G conv buffers (BF16, CPU copy)."""
    import torch
    return torch.stack([L._get(cache.layers[l], 'conv_states')[0, :QK, :].detach().to('cpu').clone() for l in G])


def edit_block(q, vec_j, sign):
    """q: [1, 4096, 4] BF16 q/k block; vec_j: [4096, 3] float32.  Slots [1,4) <- BF16(FP32(q) + sign * vec_j); slot 0 untouched.
    Returns (new block, squared norm of the actually written change)."""
    import torch
    q = q.clone()
    add = (sign * vec_j).to(device=q.device, dtype=torch.float32)
    old = q[0, :, EDIT_SLOTS].float()
    new = (old + add).to(q.dtype)
    q[0, :, EDIT_SLOTS] = new
    return q, float((new.float() - old).pow(2).sum())


def edited_arm(recv, qk_base, v_src, G, vec, sign):
    """Receiver state with G conv q/k from qk_base (slots [1,4) += sign * vec, FP32 then one cast to BF16), V from v_src.
    vec: [len(G), 4096, 3] float32 or None.  Returns (cache, actual written edit norm)."""
    import torch
    c = copy.deepcopy(recv)
    tot = 0.0
    for j, l in enumerate(G):
        fq, fv = L._get(qk_base.layers[l], 'conv_states'), L._get(v_src.layers[l], 'conv_states')
        q = fq[:, :QK].clone()
        if vec is not None:
            q, sq = edit_block(q, vec[j], sign)
            tot += sq
        L._set(c.layers[l], 'conv_states', torch.cat([q, fv[:, QK:]], dim=1).contiguous())
    return c, tot ** 0.5


def check_edit(recv, qk_base, v_src, cc, types, G, edited, label):
    import torch
    h = lambda c: {'X': NRR.comp_sha_range(c, types, ALLK, 0, SPLIT), 'S': comp_sha(c, types, ('recurrent',)), 'KV': comp_sha(c, types, ('kv',))}   # noqa: E731
    assert h(cc) == h(recv), ('arm touched non-conv state', label)
    for l in G:
        got, fq, fv = L._get(cc.layers[l], 'conv_states'), L._get(qk_base.layers[l], 'conv_states'), L._get(v_src.layers[l], 'conv_states')
        assert torch.equal(got[:, QK:], fv[:, QK:]), ('V source', label, l)
        assert torch.equal(got[:, :QK, 0], fq[:, :QK, 0]), ('slot 0 changed', label, l)
        if not edited:
            assert torch.equal(got[:, :QK], fq[:, :QK]), ('q/k source', label, l)


def form_text(engine, a, contexts, calib, conds, qctok, counts):
    """C(a) and T(a,d) on the broad split (frozen P.form); hashes must equal QCD stage G."""
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    t = {x['id']: x for x in items()}[a]
    plan_t = t['plan']
    item = QCDR.qc_items()[plan_t['qc_broad_id']]
    seg = PK.label_tokens(tok, contexts[a], item['boundary_text'], encode_text)
    assert not seg['straddling_tokens'] and (seg['b'], seg['n']) == (plan_t['b_b'], plan_t['n'])
    prompt = seg['ids']
    assert exp.digest(prompt) == qctok['items'][item['id']]['prompt_token_sha256']
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    Bw = list(range(plan_t['p'], plan_t['e'] + 1))
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:seg['b'] + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    g = QSTR._g_record(a)
    assert comp_sha(base, types, ALLK, 0) == g['hashes']['base_b'], ('base_b != QCD G', a)
    C = P.form(engine, base, prefix, Bw, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(Bw)
    assert comp_sha(C, types, ALLK, 0) == g['hashes']['C_b'], ('C != QCD G', a)
    T = {}
    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        T[d] = P.form(engine, base, prefix, Bw, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(Bw)
        assert comp_sha(T[d], types, ALLK, 0) == g['hashes'][f'T_b|{d}'], ('T != QCD G', a, d)
    q_shared, t2, d2 = shared_tokens(tok, item)
    info = {'item': item, 'q_shared': q_shared, 'watch': [t2] + list(d2), 'last': last, 'n': n, 'base': base, 'scenario': plan_t['base_id'],
            'code_tokens': {item['target']: t2, **dict(zip(item['distractors'], d2))}, 'g': g}
    return C, T, info


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, offsets=None, qst=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    traj, tensors, gates, edits = {}, {}, {}, {}
    C, T, info = form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC = comp_sha(C, types, ALLK, 0)
    hT = {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    if stage == 'collect':
        tensors['qk'] = {'C': qk_tensor(C, G), **{f'T|{d}': qk_tensor(T[d], G) for d in conds}}
        gates['collect'] = 'C and T(d) hashes == QCD G; q/k conv slots of all 14 G layers saved (BF16, [14, 4096, 4])'
        gates['qk_sha'] = {k: L.tensor_hash(v) for k, v in tensors['qk'].items()}
    else:
        def run(name, cache):
            F.assert_no_hooks(model)
            r, lg = generate(engine, cache, info['last'], info['n'], info['q_shared'], info['watch'], types, counts)
            counts['trajectories'] += 1
            r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
            traj[name] = r
            tensors[name] = lg
            if r['ids'][0] == info['q_shared'] and len(r['ids']) > 1:
                assert r['diag']['watch'] == r['first']['step2'] and r['diag']['logits_sha256'] == r['first']['step2_logits_sha256'], ('diag != step 2', name)
            return r

        def same(name, r, o):
            assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'], ('replay != QST', name)
            assert r['first']['cache_sha256'] == o['first']['cache_sha256'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('replay cache', name)
            assert r['diag'] == o['diag'], ('replay diag', name)

        same('C', run('C|-', C), qst[f'U|-|{a}|{a}'])
        for d in conds:
            same(f'T_nat|{d}', run(f'T_nat|{d}', T[d]), qst[f'T_nat|{d}|{a}|{a}'])
            specs = {'V': (T[d], None, 1), 'F': (C, None, 1)}
            if stage == 'formal':
                s = info['scenario']
                mu, rr = offsets['mu'][(s, d)], offsets['r'][(s, d)]
                specs.update({'R': (T[d], mu, -1), 'A': (C, mu, 1), 'R_rand': (T[d], rr, -1), 'A_rand': (C, rr, 1)})
            for arm, (qb, vec, sign) in specs.items():
                cc, nrm = edited_arm(T[d], qb, C, G, vec, sign)
                check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
                edits[f'{arm}|{d}'] = nrm
                r = run(f'{arm}|{d}', cc)
                if arm == 'V':
                    same(f'V|{d}', r, qst[f'H_T|{d}|{a}|{a}'])
                elif arm == 'F':
                    same(f'F|{d}', r, qst[f'H_C|{d}|{a}|{a}'])
                del cc
            if stage == 'preflight':
                zero = torch.zeros(len(G), QK, 3)
                for arm, qb, ref in (('R_zero', T[d], f'V|{d}'), ('A_zero', C, f'F|{d}')):
                    cc, nrm = edited_arm(T[d], qb, C, G, zero, -1 if arm == 'R_zero' else 1)
                    assert nrm == 0.0, ('zero edit wrote something', arm, d)
                    r = run(f'{arm}|{d}', cc)
                    o = traj[ref]
                    assert r['ids'] == o['ids'] and r['first'] == o['first'] and r['diag'] == o['diag'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('zero-offset no-op differs', arm, d)
                    del cc
                gates['noop'] = 'zero-offset R/A edits write nothing and reproduce V/F trajectories, diagnostics and caches exactly'
            if stage == 'formal':
                ok = {}
                for x, y in (('R', 'R_rand'), ('A', 'A_rand')):
                    u, v = edits[f'{x}|{d}'], edits[f'{y}|{d}']
                    ok[x] = (u == v == 0.0) or abs(u - v) / max(u, v) <= NORM_TOL
                edits[f'norm_ok|{d}'] = ok
        gates['replay_qst'] = 'C == QST U(a,a); T_nat == QST T_nat; V == QST H_T(a,a); F == QST H_C(a,a) (ids, first-step and cache hashes, diagnostics)'
        gates['sources'] = 'every arm: V block == C(a), slot 0 of q/k == base, S/KV/shallow == T(a,d); unedited arms q/k == base'
    assert comp_sha(C, types, ALLK, 0) == hC and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    assert comp_sha(info['base'], types, ALLK, 0) == info['g']['hashes']['base_b'], 'base modified'
    F.assert_no_hooks(model)
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': info['item'], 'code_tokens': info['code_tokens'], 'q_shared': info['q_shared'],
            'hashes': {'C': hC, **{f'T|{d}': hT[d] for d in conds}}, 'edit_norms': edits, 'calibration': calib, 'trajectories': traj,
            'counts': counts, 'gates': gates}
    return body, tensors


def load_offsets():
    import torch
    man = exp.read(OFFSETS_MANIFEST)
    assert man['status'] == 'passed' and exp.sha(OFFSETS_PT) == man['offsets_sha256'], 'offsets file != manifest'
    raw = torch.load(OFFSETS_PT)
    return {'mu': {tuple(k.split('|')): v for k, v in raw['mu'].items()}, 'r': {tuple(k.split('|')): v for k, v in raw['r'].items()}}


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, QST_DIR / 'qst_run.py', QST_DIR / 'qst_core.py', QCD_DIR / 'qcd_run.py', QCD_DIR / 'data/plan-r01.json', QC_DIR / 'qc_run.py', NQ_DIR / 'nq_run.py', NQ_DIR / 'nq_analysis.py', NQR.INPUTS, NQR.TOKENS, SVQ_DIR / 'svq_run.py', SP_DIR / 'sp_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    qst = [w / 'receipt.json' for w in sorted(QST_FORMAL.glob('worker-*')) if w.is_dir()] + [QST_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + [p for p in B3R.frozen_paths() if p not in own]


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
    if stage in ('collect', 'formal'):
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    if stage == 'formal':
        col = exp.read(COLLECT / 'verification.json')
        assert col['status'] == 'passed' and col['freeze_sha256'] == auth['freeze_sha256'] and col['stage'] == 'collect'
        man = exp.read(OFFSETS_MANIFEST)
        assert man['status'] == 'passed' and man['freeze_sha256'] == auth['freeze_sha256'] and exp.sha(OFFSETS_PT) == man['offsets_sha256']
        assert auth['required_evidence'].get('analysis/offsets-manifest-r01.json') == exp.sha(OFFSETS_MANIFEST)
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
    offsets = load_offsets() if stage == 'formal' else None
    qst = qst_traj() if stage != 'collect' else None
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = QCR.nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        body, tensors = run_item(engine, u, contexts, calib[rid], conds, qctok, output, stage, offsets=offsets, qst=qst)
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
    lock = open(f'/tmp/acupuncture-qco-worker{worker}.lock', 'w')
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
        a = rec['text']
        if r['stage'] == 'collect':
            want = set()
            assert set(rec['gates']['qk_sha']) == {'C'} | {f'T|{d}' for d in DIRECTIONS}
        else:
            arms = ('V', 'F') + (('R_zero', 'A_zero') if r['stage'] == 'preflight' else ('R', 'A', 'R_rand', 'A_rand'))
            want = {'C|-'} | {f'{x}|{d}' for d in DIRECTIONS for x in ('T_nat',) + arms}
            for g in ('replay_qst', 'sources'):
                assert rec['gates'][g], g
            if r['stage'] == 'preflight':
                assert rec['gates']['noop']
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        assert rec['gates']['calibration']
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
            cmd = [sys.executable, '-u', str(HERE / 'qco_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (len(PREFLIGHT_ITEMS) if stage == 'preflight' else 48), units
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
