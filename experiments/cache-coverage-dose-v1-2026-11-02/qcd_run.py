"""QCD-01: formation-time injection coverage vs dose (design v2 in CONTRACT.zh-CN.md r01, from plan v1 c030d28 + the reviewed
revisions).  Texts: the 108 QC-01 NA/LA texts.  Stage G (gate): cross clean-V source x split on all texts; stage S (science):
equal-length position comparison E1 vs N1 and four dose-matched policies, all on the unified broad split with donor C_b.
Every needle position is audited with read-only hooks around the frozen injection hook (actual injected amount).
python qcd_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
QC_DIR = HERE.parent / 'cache-query-layout-coverage-v1-2026-11-02'
sys.path.insert(0, str(QC_DIR))
sys.path.insert(0, str(HERE))
import qc_run as QCR  # noqa: E402  (frozen QC-01 runner: NQ chain, calibrations, record readers)

NQR, SVQ, SPR, NRR = QCR.NQR, QCR.SVQ, QCR.SPR, QCR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR = QCR.FC_DIR, QCR.SP_DIR, QCR.SVQ_DIR, QCR.NQ_DIR
B3R, V, P, PK, X = QCR.B3R, QCR.V, QCR.P, QCR.PK, QCR.X
CF, CFK, LR, B = QCR.CF, QCR.CFK, QCR.LR, QCR.B
F, L, T1, exp, K = QCR.F, QCR.L, QCR.T1, QCR.exp, QCR.K

PLAN_ID = 'QCD-01-COVERAGE-DOSE-v2'
PLAN_DOCS = [REPO / 'docs/cache-coverage-dose-plan-v1-2026-11-02.zh-CN.md', REPO / 'docs/cache-coverage-dose-self-check-v1-2026-11-02.zh-CN.md']
PLAN = HERE / 'data/plan-r01.json'
QC_INPUTS, QC_TOKENS = QCR.INPUTS, QCR.TOKENS
QC_FORMAL = QC_DIR / 'runs/formal-r01'
G_FORMAL = HERE / 'runs/gformal-r01'
G_GATE = HERE / 'analysis/g-gate-r01.json'
NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QCR.NQ_FORMAL, QCR.SVQ_FORMAL, QCR.SP_FORMAL, QCR.NR_FORMAL, QCR.B3_FORMAL, QCR.XC_FORMAL, QCR.SK_FORMAL
SPLIT = 13
DIRECTIONS = QCR.DIRECTIONS
PREFLIGHT_ITEMS = ('NA-NQ01-ABC-A', 'LA-NQ01-ABC-A')
REBUILD_ITEM = 'LA-NQ01-ABC-A'
STAGES = ('preflight', 'gformal', 'sformal')
MAX_WORKERS = {'preflight': 1, 'gformal': 2, 'sformal': 2}
STOP = QCR.STOP
NEW_POLICIES = ('E1', 'N-A', 'N-Q', 'B-A', 'B-Q')
LIMITS = {'preflight': {'formations': 86, 'trajectories': 166, 'decode_forwards': 5312, 'diagnostics': 166, 'calibrations': 0},
          'gformal': {'formations': 1512, 'trajectories': 4536, 'decode_forwards': 145152, 'diagnostics': 4536, 'calibrations': 0},
          'sformal': {'formations': 3024, 'trajectories': 4320, 'decode_forwards': 138240, 'diagnostics': 4320, 'calibrations': 0}}
STORAGE_LIMIT = 48 * 2 ** 30
QK = SVQ.QK
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards',
              'audited_positions', 'shadow_gemv')
comp_sha = NRR.comp_sha
conditions, shared_tokens, conv_mix, generate = NQR.conditions, NQR.shared_tokens, NQR.conv_mix, NQR.generate


def texts():
    return exp.read(PLAN)['texts']


def qc_items():
    return {r['id']: r for r in exp.read(QC_INPUTS)['items']}


def items():
    return texts()


def plan(stage, worker, n_workers):
    rows = texts()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert sorted(r['id'] for r in rows) == sorted(PREFLIGHT_ITEMS)
        return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows]
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def qc_record(item_id):
    for w in sorted(QC_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'QC record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def g_record(item_id):
    for w in sorted(G_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel = f'records/{item_id}.json'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'G record hash'
            return exp.read(w / rel)
    raise KeyError(item_id)


def scaled(cond, a):
    c = dict(cond)
    c['dose'] = -float(a)
    return c


def forward_audit(engine, cache, token, t, cond, calib, counts):
    """F.forward_tokens(engine, cache, [token], t, cond, calib) with read-only hooks before and after the frozen injection hook.
    Returns (cache, audit row).  Native: actual BF16 activation change on the channel, local down_proj output difference
    (shadow GEMV on the unchanged / changed inputs, not written back).  Direction: actual change of the MLP output vector."""
    import torch
    model = engine.model
    layer = cond['layer']
    rec = {}
    if cond['kind'] == 'native':
        mod, ch = engine.modules[layer], cond['channel']

        def before(_m, args):
            rec['x0'] = args[0].detach().clone()

        def after(_m, args):
            x1 = args[0]
            W = _m.weight
            rec['a0'] = float(rec['x0'][0, -1, ch].float())
            rec['a1'] = float(x1[0, -1, ch].float())
            others = torch.equal(torch.cat([x1[..., :ch], x1[..., ch + 1:]], -1), torch.cat([rec['x0'][..., :ch], rec['x0'][..., ch + 1:]], -1))
            rec['others_unchanged'] = bool(others)
            rec['out_diff_norm'] = float((torch.nn.functional.linear(x1, W).float() - torch.nn.functional.linear(rec['x0'], W).float()).norm())
            counts['shadow_gemv'] += 2
        h1 = mod.register_forward_pre_hook(before)
        reg_after = lambda: mod.register_forward_pre_hook(after)   # noqa: E731
    else:
        mlp = engine.layers[layer].mlp

        def before(_m, _a, out):
            o = out[0] if isinstance(out, tuple) else out
            rec['y0'] = o.detach().clone()

        def after(_m, _a, out):
            o = out[0] if isinstance(out, tuple) else out
            rec['u'] = (o.float() - rec['y0'].float())[0, -1].detach().clone()
        h1 = mlp.register_forward_hook(before)
        reg_after = lambda: mlp.register_forward_hook(after)       # noqa: E731
    try:
        with F.Hooks(model, F.A_LAYER, None, False), torch.inference_mode(), L.masked_injection(engine, cond, calib, [True]) as writes:
            h2 = reg_after()
            try:
                out = L.forward(model, [token], t, cache)
            finally:
                h2.remove()
    finally:
        h1.remove()
    assert len(writes) == 1 and writes[0]['positions'] == 1, writes
    counts['audited_positions'] += 1
    scale = calib['residual_scales'][str(layer)]
    if cond['kind'] == 'native':
        colnorm = float(engine.modules[layer].weight[:, cond['channel']].float().norm())
        da = rec['a1'] - rec['a0']
        assert rec['others_unchanged'], 'native needle changed another channel'
        row = {'pos': t, 'kind': 'native', 'requested_activation_delta': cond['dose'] * scale / float(engine.column_norms[str(layer)][cond['channel']]),
               'actual_activation_delta': da, 'a0': rec['a0'], 'column_norm_bf16_fp32': colnorm, 'norm': abs(da) * colnorm,
               'down_proj_out_diff_norm': rec['out_diff_norm']}
        vec = None
    else:
        u = rec['u']
        req = torch.tensor(cond['vector'], device=u.device, dtype=torch.float32) * (cond['dose'] * scale)
        row = {'pos': t, 'kind': 'direction', 'norm': float(u.norm()), 'requested_norm': float(req.norm()),
               'deviation_from_requested_norm': float((u - req).norm()), 'cos_with_requested': float(torch.nn.functional.cosine_similarity(u, req, dim=0)),
               'y0_norm': float(rec['y0'][0, -1].float().norm())}
        vec = u.to('cpu')
    return out.past_key_values, row, vec


def form_policy(engine, base, prefix, positions, active, cond, calib, counts):
    """Token-by-token formation over `positions` from a copy of `base`; the needle acts on positions in `active` only
    (P.form semantics; inactive positions use F.forward_tokens without a needle)."""
    cache = copy.deepcopy(base)
    rows, vecs = [], []
    for t in positions:
        if t in active:
            cache, row, vec = forward_audit(engine, cache, prefix[t], t, cond, calib, counts)
            rows.append(row)
            vecs.append(vec)
        else:
            cache, _ = F.forward_tokens(engine, cache, [prefix[t]], t, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(positions)
    norms = [r['norm'] for r in rows]
    summary = {'A': sum(norms), 'Q': sum(x * x for x in norms), 'P': max(norms), 'n_active': len(rows), 'dose': cond['dose']}
    return cache, {'summary': summary, 'rows': rows}, vecs


def form_clean(engine, base, prefix, positions, calib, counts):
    cache = P.form(engine, base, prefix, positions, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(positions)
    return cache


def check_arm(cT, donor, cc, types, G, qk_from_donor, v_from_donor, label):
    import torch
    hT = {'X': NRR.comp_sha_range(cT, types, ALLK, 0, SPLIT), 'S': comp_sha(cT, types, ('recurrent',)), 'KV': comp_sha(cT, types, ('kv',))}
    h = {'X': NRR.comp_sha_range(cc, types, ALLK, 0, SPLIT), 'S': comp_sha(cc, types, ('recurrent',)), 'KV': comp_sha(cc, types, ('kv',))}
    assert h == hT, ('arm touched non-conv state', label)
    for l in G:
        got, fT, fD = L._get(cc.layers[l], 'conv_states'), L._get(cT.layers[l], 'conv_states'), L._get(donor.layers[l], 'conv_states')
        assert torch.equal(got[:, :QK], (fD if qk_from_donor else fT)[:, :QK]), ('q/k source', label, l)
        assert torch.equal(got[:, QK:], (fD if v_from_donor else fT)[:, QK:]), ('V source', label, l)


def rel(a, b):
    return abs(a - b) / max(abs(a), abs(b))


def run_item(engine, item, context, calib, conds, qctok, output, stage, preflight=False):
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    qi = qc_items()
    broad, tail = qi[item['qc_broad_id']], qi[item['qc_tail_id']]
    seg_b = PK.label_tokens(tok, context, broad['boundary_text'], encode_text)
    seg_s = PK.label_tokens(tok, context, tail['boundary_text'], encode_text)
    prompt = seg_b['ids']
    assert prompt == seg_s['ids'] and not seg_b['straddling_tokens'] and not seg_s['straddling_tokens']
    assert (seg_b['b'], seg_s['b'], seg_b['n']) == (item['b_b'], item['b_s'], item['n'])
    tb = qctok['items'][broad['id']]
    assert exp.digest(prompt) == tb['prompt_token_sha256']
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    Bw = list(range(item['windows']['B'][0], item['windows']['B'][1] + 1))
    Nw = list(range(item['windows']['N'][0], item['windows']['N'][1] + 1))
    Ew = list(range(item['windows']['E20'][0], item['windows']['E20'][1] + 1))
    assert Bw == list(range(item['b_b'] + 1, n - 1)) and Nw == list(range(item['b_s'] + 1, n - 1))
    counts = {k: 0 for k in COUNT_KEYS}
    traj, tensors, gates, audits, hashes = {}, {}, {}, {}, {}
    q_shared, t2, d2 = shared_tokens(tok, broad)
    assert (q_shared, t2, list(d2)) == (tb['q_shared'], tb['second_tokens']['target'], tb['second_tokens']['distractors'])
    watch = [t2] + list(d2)
    code_tok = {broad['target']: t2, **dict(zip(broad['distractors'], d2))}

    def run(name, cache):
        F.assert_no_hooks(model)
        r, lg = generate(engine, cache, last, n, q_shared, watch, types, counts)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        tensors[name] = lg
        if r['ids'][0] == q_shared and len(r['ids']) > 1:
            assert r['diag']['watch'] == r['first']['step2'] and r['diag']['logits_sha256'] == r['first']['step2_logits_sha256'], ('diag != step 2', name)
        return r

    def prefill(b):
        F.assert_no_hooks(model)
        with torch.inference_mode():
            c = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
        counts['prefix_prefills'] += 1
        return c

    def same(name, r, o):
        assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'], ('replay != QC-01', name)
        assert r['first']['cache_sha256'] == o['first']['cache_sha256'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('replay cache', name)
        assert r['diag'] == o['diag'], ('replay diag', name)

    base_b = prefill(item['b_b'])
    hashes['base_b'] = comp_sha(base_b, types, ALLK, 0)
    C_b = form_clean(engine, base_b, prefix, Bw, calib, counts)
    hashes['C_b'] = comp_sha(C_b, types, ALLK, 0)
    vecs_keep = {}
    if stage in ('preflight', 'gformal'):
        qb, qt = qc_record(broad['id'])['trajectories'], qc_record(tail['id'])['trajectories']
        base_s = prefill(item['b_s'])
        hashes['base_s'] = comp_sha(base_s, types, ALLK, 0)
        C_s = form_clean(engine, base_s, prefix, Nw, calib, counts)
        hashes['C_s'] = comp_sha(C_s, types, ALLK, 0)
        same('C_b', run('C_b', C_b), qb['C_nat'])
        same('C_s', run('C_s', C_s), qt['C_nat'])
        for d, cond in conds.items():
            au = X.write_audit(engine, cond, calib)
            au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
            assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
            c1 = scaled(cond, 1.0)
            T_b, audits[f'B1|{d}'], vecs_keep[f'B1|{d}'] = form_policy(engine, base_b, prefix, Bw, set(Bw), c1, calib, counts)
            T_s, audits[f'Ts|{d}'], _ = form_policy(engine, base_s, prefix, Nw, set(Nw), c1, calib, counts)
            T_u, audits[f'N1|{d}'], vecs_keep[f'N1|{d}'] = form_policy(engine, base_b, prefix, Bw, set(Nw), c1, calib, counts)
            for nm, c in (('T_b', T_b), ('T_s', T_s), ('T_u', T_u)):
                hashes[f'{nm}|{d}'] = comp_sha(c, types, ALLK, 0)
            arms = {f'T_b|{d}|nat': T_b, f'T_b|{d}|V_b': conv_mix(T_b, C_b, G, 'T', 'C'), f'T_b|{d}|V_s': conv_mix(T_b, C_s, G, 'T', 'C'),
                    f'T_b|{d}|F_b': NRR.restore(T_b, C_b, types, '010'),
                    f'T_s|{d}|nat': T_s, f'T_s|{d}|V_s': conv_mix(T_s, C_s, G, 'T', 'C'), f'T_s|{d}|V_b': conv_mix(T_s, C_b, G, 'T', 'C'),
                    f'T_u|{d}|nat': T_u, f'T_u|{d}|V_b': conv_mix(T_u, C_b, G, 'T', 'C'), f'T_u|{d}|F_b': NRR.restore(T_u, C_b, types, '010')}
            for name, cc in arms.items():
                recv, _, arm = name.split('|')
                cT = {'T_b': T_b, 'T_s': T_s, 'T_u': T_u}[recv]
                if arm != 'nat':
                    donor = C_b if arm.endswith('_b') else C_s
                    check_arm(cT, donor, cc, types, G, arm.startswith('F'), True, name)
            for name, cc in arms.items():
                run(name, cc)
            same(f'T_b|{d}|nat', traj[f'T_b|{d}|nat'], qb[f'T_nat|{d}'])
            same(f'T_b|{d}|V_b', traj[f'T_b|{d}|V_b'], qb[f'T_V|{d}'])
            same(f'T_b|{d}|F_b', traj[f'T_b|{d}|F_b'], qb[f'T_F|{d}'])
            same(f'T_s|{d}|nat', traj[f'T_s|{d}|nat'], qt[f'T_nat|{d}'])
            same(f'T_s|{d}|V_s', traj[f'T_s|{d}|V_s'], qt[f'T_V|{d}'])
            if preflight and item['id'] == REBUILD_ITEM and d == OFF_DIR:
                C2 = form_clean(engine, base_b, prefix, Bw, calib, counts)
                T2, _, _ = form_policy(engine, base_b, prefix, Bw, set(Bw), c1, calib, counts)
                assert comp_sha(C2, types, ALLK, 0) == hashes['C_b'] and comp_sha(T2, types, ALLK, 0) == hashes[f'T_b|{d}'], 'rebuild differs'
                r1, r2 = run('REBUILD:C_b', C2), run(f'REBUILD:T_b|{d}|nat', T2)
                for a, b_ in ((r1, traj['C_b']), (r2, traj[f'T_b|{d}|nat'])):
                    assert a['ids'] == b_['ids'] and a['final_cache_sha256'] == b_['final_cache_sha256'] and a['diag'] == b_['diag'], 'rebuild trajectory'
                gates['rebuild'] = 'C_b and T_b(4146) rebuilt from the shared base: cache hashes, trajectories and diagnostics identical'
                del C2, T2
            del T_b, T_s, T_u, arms
        assert comp_sha(base_s, types, ALLK, 0) == hashes['base_s'], 'base_s modified'
        gates['replay_qc'] = ('C_b == QC broad C_nat; C_s == QC tail C_nat; T_b nat/V_b/F_b == QC broad T_nat/T_V/T_F; T_s nat/V_s == QC tail '
                              'T_nat/T_V (ids, first-step and cache hashes, diagnostics) with audit hooks installed')
        gates['assembly'] = 'every V arm: q/k from receiver, V block from the named donor, S/KV/shallow == receiver; F arms: conv == donor'
        del C_s, base_s
    if stage in ('preflight', 'sformal'):
        ref = None if stage == 'preflight' else g_record(item['id'])
        if ref is not None:
            assert ref['hashes']['base_b'] == hashes['base_b'] and ref['hashes']['C_b'] == hashes['C_b'], 'recomputed C_b differs from G'
        for d, cond in conds.items():
            # re-form B1 and N1 (no generation) for the within-unit dose comparisons; hashes must equal G
            if stage == 'sformal':
                c1 = scaled(cond, 1.0)
                T_b, audits[f'B1|{d}'], vecs_keep[f'B1|{d}'] = form_policy(engine, base_b, prefix, Bw, set(Bw), c1, calib, counts)
                T_u, audits[f'N1|{d}'], vecs_keep[f'N1|{d}'] = form_policy(engine, base_b, prefix, Bw, set(Nw), c1, calib, counts)
                assert comp_sha(T_b, types, ALLK, 0) == ref['hashes'][f'T_b|{d}'] and comp_sha(T_u, types, ALLK, 0) == ref['hashes'][f'T_u|{d}'], ('re-formed B1/N1 differ from G', d)
                del T_b, T_u
            for pol in NEW_POLICIES:
                spec = item['policies'][pol]
                win = {'B': Bw, 'N': Nw, 'E20': Ew}[spec['window']]
                cT, audits[f'{pol}|{d}'], vecs_keep[f'{pol}|{d}'] = form_policy(engine, base_b, prefix, Bw, set(win), scaled(cond, spec['a']), calib, counts)
                hashes[f'{pol}|{d}'] = comp_sha(cT, types, ALLK, 0)
                cv = conv_mix(cT, C_b, G, 'T', 'C')
                check_arm(cT, C_b, cv, types, G, False, True, f'{pol}|{d}|V_b')
                run(f'{pol}|{d}|nat', cT)
                run(f'{pol}|{d}|V_b', cv)
                del cT, cv
        gates['dose_audit'] = 'every needle position audited with read-only hooks around the frozen injection hook; native: other channels unchanged'
    assert comp_sha(base_b, types, ALLK, 0) == hashes['base_b'], 'base_b modified'
    # E1 vs N1 per-step vector comparison (report-only)
    steps = {}
    for d in DIRECTIONS:
        if f'E1|{d}' in audits and f'N1|{d}' in audits:
            e_rows, n_rows = audits[f'E1|{d}']['rows'], audits[f'N1|{d}']['rows']
            if e_rows[0]['kind'] == 'native':
                diffs = [abs(a['norm'] - b['norm']) / max(a['norm'], b['norm']) for a, b in zip(e_rows, n_rows)]
            else:
                ev, nv = vecs_keep[f'E1|{d}'], vecs_keep[f'N1|{d}']
                diffs = [float((a - b).norm()) / max(float(a.norm()), float(b.norm())) for a, b in zip(ev, nv)]
            steps[d] = {'max_rel_step_diff': max(diffs), 'mean_rel_step_diff': sum(diffs) / len(diffs)}
    if any(vecs_keep.values()):
        tensors['injected_vectors'] = {k: v for k, v in vecs_keep.items() if v and v[0] is not None}
    F.assert_no_hooks(model)
    gates['tokens'] = 'prompt ids equal the QC token audit; b_b, b_s, n equal the frozen plan; windows B/N/E20 as frozen'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'answer': broad['target'], 'distractors': list(broad['distractors']), 'code_tokens': code_tok, 'q_shared': q_shared,
            'second_tokens': {'target': t2, 'distractors': list(d2)}, 'item': broad, 'plan_text': item, 'hashes': hashes,
            'dose_audits': audits, 'e1_n1_steps': steps, 'calibration': calib, 'trajectories': traj, 'counts': counts, 'gates': gates,
            'b': item['b_b'], 'n': n, 'window': item['L']}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN, QC_INPUTS, QC_TOKENS, QC_DIR / 'qc_run.py', QC_DIR / 'qc_core.py', QC_DIR / 'qc_analysis.py', NQ_DIR / 'nq_run.py', NQ_DIR / 'nq_core.py', NQ_DIR / 'nq_analysis.py', NQR.INPUTS, NQR.TOKENS, SVQ_DIR / 'svq_run.py', SP_DIR / 'sp_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
    b3 = [w / 'receipt.json' for w in sorted(B3_FORMAL.glob('worker-*')) if w.is_dir()] + [B3_FORMAL / 'verification.json']
    xc = [w / 'receipt.json' for w in sorted(XC_FORMAL.glob('worker-*')) if w.is_dir()] + [XC_FORMAL / 'verification.json']
    sk = [w / 'receipt.json' for w in sorted(SK_FORMAL.glob('worker-*')) if w.is_dir()] + [SK_FORMAL / 'verification.json']
    nr = [w / 'receipt.json' for w in sorted(NR_FORMAL.glob('worker-*')) if w.is_dir()] + [NR_FORMAL / 'verification.json']
    sp = [w / 'receipt.json' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir()] + [SP_FORMAL / 'verification.json']
    sp += [w / f'calibrations/{c.name}' for w in sorted(SP_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    svq = [w / 'receipt.json' for w in sorted(SVQ_FORMAL.glob('worker-*')) if w.is_dir()] + [SVQ_FORMAL / 'verification.json']
    nq = [w / 'receipt.json' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir()] + [NQ_FORMAL / 'verification.json']
    nq += [w / f'calibrations/{c.name}' for w in sorted(NQ_FORMAL.glob('worker-*')) if w.is_dir() for c in sorted((w / 'calibrations').glob('*.json'))]
    qc = [w / 'receipt.json' for w in sorted(QC_FORMAL.glob('worker-*')) if w.is_dir()] + [QC_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + sp + svq + nq + qc + [p for p in B3R.frozen_paths() if p not in own]


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
    if stage in ('gformal', 'sformal'):
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    if stage == 'sformal':
        g = exp.read(G_FORMAL / 'verification.json')
        assert g['status'] == 'passed' and g['freeze_sha256'] == auth['freeze_sha256'] and g['stage'] == 'gformal'
        gate = exp.read(G_GATE)
        assert gate['status'] == 'passed' and gate['freeze_sha256'] == auth['freeze_sha256'], 'stage G gate not passed'
        assert auth['required_evidence'].get('analysis/g-gate-r01.json') == exp.sha(G_GATE)
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    rows = {r['id']: r for r in items()}
    qi = qc_items()
    contexts = {k: v for k, v in exp.contexts_for(engine.tokenizer, [qi[r['qc_broad_id']] for r in rows.values()]).items()}
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
        item = rows[u['item_id']]
        body, tensors = run_item(engine, item, contexts[item['id']], calib[rid], conds, qctok, output, stage, preflight=(stage == 'preflight'))
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
        assert B.dir_bytes(output) <= STORAGE_LIMIT // 2, 'storage budget exceeded'
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
    lock = open(f'/tmp/acupuncture-qcd-worker{worker}.lock', 'w')
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
        if r['stage'] in ('preflight', 'gformal'):
            want |= {'C_b', 'C_s'} | {f'{x}|{d}|{a}' for d in DIRECTIONS for x, arms in (('T_b', ('nat', 'V_b', 'V_s', 'F_b')), ('T_s', ('nat', 'V_s', 'V_b')), ('T_u', ('nat', 'V_b', 'F_b'))) for a in arms}
        if r['stage'] in ('preflight', 'sformal'):
            want |= {f'{p}|{d}|{a}' for p in NEW_POLICIES for d in DIRECTIONS for a in ('nat', 'V_b')}
        first = r['stage'] == 'preflight' and rec['item']['id'] == REBUILD_ITEM
        if first:
            want |= {'REBUILD:C_b', f'REBUILD:T_b|{OFF_DIR}|nat'}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        gs = ('tokens', 'calibration') + (('replay_qc', 'assembly') if r['stage'] != 'sformal' else ()) + (('dose_audit',) if r['stage'] != 'gformal' else ()) + (('rebuild',) if first else ())
        for g in gs:
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
            cmd = [sys.executable, '-u', str(HERE / 'qcd_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (len(PREFLIGHT_ITEMS) if stage == 'preflight' else 108), units
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
