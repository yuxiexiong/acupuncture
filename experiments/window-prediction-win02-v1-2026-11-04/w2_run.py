"""WIN-02: formation window x recovery arms on the reserved needles L2/C5251, L3/C7666, L5/C2467 (-1) and random R0 at L0
(design v2; CONTRACT.zh-CN.md r01).  Adapted from the frozen WIN-01 runner: no S_deep, no B block.  Fact task = stage2 pipeline (single prefix forward with a position mask, L.decode 128, L.score);
code task = NCC pipeline (0..b forward, token-wise window formation, t1 + natural 32, y_full).  Imports never load a model.
python win_run.py freeze PATH | run --stage S --worker W --authorization A --output O | verify DIR | launch --stage S --authorization A --output O"""
import argparse
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
NCC_DIR = HERE.parent / 'cache-native-carrier-comparison-v1-2026-11-03'
S2_DIR = HERE.parent / 'early-state-localization-stage2-v2-2026-10-30'
sys.path.insert(0, str(NCC_DIR))
import ncc_run as R  # noqa: E402  (frozen NCC-01 runner; brings the NVB/LVK chain)
_spec = importlib.util.spec_from_file_location('win_stage2', S2_DIR / 'stage2.py')
st = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(S2_DIR))
_spec.loader.exec_module(st)
sys.path.insert(0, str(HERE))
import w2_core as W  # noqa: E402

L, exp, NC, F, X_, T1 = R.L, R.exp, R.NC, R.F, R.LVKR.X, R.T1
P, PK = R.LVKR.P, R.LVKR.PK
NCC_FORMAL = NCC_DIR / 'runs/formal-r01'
S2_RUNS = {'g_development-r01': 'g_development', 'g_history-r01': 'g_history'}
PLAN_ID = 'WIN-02-WINDOW-PREDICTION-v1'
WIN01_DIR = HERE.parent / 'window-recovery-win01-v1-2026-11-04'
PLAN_DOCS = [REPO / 'docs/cache-mechanism-win02-prediction-plan-v1-2026-11-04.zh-CN.md']
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_FACT = ('RD01',)
PREFLIGHT_CODE = tuple(R.PREFLIGHT_ITEMS)
WRITE_REL = 0.01
GPU_CAP_S = {'preflight': 0.5 * 3600, 'formal': 7.0 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
PER_ITEM = 1 + len(W.NEEDLES) * len(W.WINDOWS) * len(W.ARMS) + len(W.NEEDLES)   # 53


def needle_condition(d, source):
    """Native needles: the stage2 / engine condition dict; R0: the frozen XCHAN direction via the NCC chain."""
    if d == W.RANDOM:
        c = dict(R.conditions()[d])
        assert c['kind'] == 'direction' and c['layer'] == 0 and c['dose'] == -1.0 and c['direction_id'] == 'R0'
        return c
    c = st.engine_condition(d) if source == 'fact' else {'id': d, 'kind': 'native', 'layer': W.NEEDLE_LAYER[d], 'channel': W.NATIVE[d], 'dose': -1.0}
    assert c['kind'] == 'native' and c['layer'] == W.NEEDLE_LAYER[d] and c['channel'] == W.NATIVE[d] and c['dose'] == -1.0
    return c


def tokens_ledger():
    return exp.read(HERE / 'prep/tokens.json')


def fact_units():
    tok = tokens_ledger()
    out = []
    for run in S2_RUNS:
        for iid, x in tok['items'].items():
            if x['panel'] == run and x['fact_version'] == 0:
                out.append({'task': 'fact', 'panel': run, 'base_id': x['base_id'], 'f0': iid, 'f1': iid.replace('-f0-', '-f1-'),
                            'aligned': bool(tok['pairs'][iid]['diff_all_in_fact']), 'key': f'fact-{x["base_id"]}'})
    return sorted(out, key=lambda u: (u['panel'], u['base_id']))


def code_units():
    rows = [r for r in R.LVKR.all_units() if r['panel'] == 'new']
    return [{'task': 'code', 'item_id': r['item_id'], 'base_id': r['base_id'], 'key': f'code-{r["item_id"]}'} for r in rows]


def plan(stage, worker, n_workers):
    fu, cu = fact_units(), code_units()
    if stage == 'preflight':
        return [u for u in fu if u['base_id'] in PREFLIGHT_FACT] + [u for u in cu if u['item_id'] in PREFLIGHT_CODE]
    mine = [u for k, u in enumerate(fu) if k % n_workers == worker]
    bases = list(dict.fromkeys(u['base_id'] for u in cu))
    mine += [u for u in cu if bases.index(u['base_id']) % n_workers == worker]
    return mine


def fields_of(cache, types):
    return [(i, f) for i, _k, f in L.component_tensors(cache, types)]


def cache_sha(cache, types):
    return exp.digest([L.tensor_hash(L._get(cache.layers[i], f)) for i, f in fields_of(cache, types)])


def build_arm(recv, donor, arm, types, b, torch):
    tg = W.arm_targets(arm, types, b)
    if not tg:
        return recv, tg
    Xc = W.replace(recv, donor, tg, L._get, L._set, copy.deepcopy)
    W.check_replace(Xc, recv, donor, tg, fields_of(recv, types), L._get, torch.equal)
    for name in ('_seen_tokens', 'seen_tokens'):
        if hasattr(recv, name):
            assert getattr(Xc, name) == getattr(recv, name), ('cache bookkeeping', name)
    return Xc, tg


def shallow_equal(Tc, Cc, types, layer, torch):
    for i, f in fields_of(Tc, types):
        if i <= layer:
            assert torch.equal(L._get(Tc.layers[i], f), L._get(Cc.layers[i], f)), ('layer <= needle layer differs', i, f)


def kv_prefix_equal(A, Bc, types, b, torch):
    for l in W.attn_layers(types):
        for f in ('keys', 'values'):
            a, c = L._get(A.layers[l], f), L._get(Bc.layers[l], f)
            assert torch.equal(a[:, :, :b + 1], c[:, :, :b + 1]), ('KV positions 0..b differ', l, f)


def write_audit(engine, cond, reference):
    au = X_.write_audit(engine, cond, reference)
    au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
    assert au['rel_err'] <= WRITE_REL, ('write audit', cond['id'], au)
    return au


# ---------------------------------------------------------------- fact task (stage2 pipeline)

def s2_record(run, item_id, cid, code):
    name = f'{item_id}__clean__all-CCC.json' if cid == 'clean' else f'{item_id}__{cid}__all-{code}.json'
    hits = list((S2_DIR / 'runs' / run).glob(f'worker-*/records/{name}'))
    assert len(hits) == 1, name
    return exp.read(hits[0]), hits[0]


def fact_gen(engine, cache, last, n, cands, counts, stage):
    gen = L.decode(engine.model, cache, last, n, engine.stop_ids, hash_all=stage == 'preflight')
    scores = [L.score(engine.model, cache, last, n, c) for c in cands]
    counts['generations'] += 1
    counts['candidate_reads'] += len(scores)
    tok = engine.tokenizer
    first = gen['readouts'][0]
    return {'token_ids': gen['token_ids'], 'end_reason': gen['end_reason'], 'first': {k: first[k] for k in ('token', 'stop_advantage', 'logits_sha256', 'top5')},
            'first_step_stop': gen['token_ids'][0] in engine.stop_ids, 'n_generated': len(gen['token_ids']),
            'answer_text': tok.decode(gen['token_ids'], skip_special_tokens=True), 'raw_text': tok.decode(gen['token_ids'], skip_special_tokens=False),
            'candidates': [s['loglikelihood'] for s in scores], 'seconds': gen['seconds']}


def bridge_fact(rec, old):
    assert rec['token_ids'] == old['generation']['token_ids'], 'stage2 bridge: tokens'
    assert rec['first']['logits_sha256'] == old['generation']['readouts'][0]['logits_sha256'], 'stage2 bridge: t1 logits'
    assert rec['candidates'] == [c['loglikelihood'] for c in old['candidates']], 'stage2 bridge: candidates'


def run_fact_pair(engine, unit, stage, counts):
    import torch
    from control_engine import encode_text, exact_pair
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    ledger = tokens_ledger()
    rows = st.items_for(S2_RUNS[unit['panel']])
    by_id = {r['id']: r for r in rows}
    ctx = st.exp.contexts_for(tok, rows)
    refs, versions, gates = {}, {}, {'bridges': [], 'structure': [], 'write': []}
    for v in ('f0', 'f1'):
        iid = unit[v]
        item, lg = by_id[iid], ledger['items'][iid]
        context = ctx[iid]
        prompt = encode_text(tok, context)
        assert prompt == lg['ids'], 'tokens != prep ledger'
        prefix, last, n, b = prompt[:-1], prompt[-1], len(prompt), lg['b']
        assert n == lg['n'] and n - 1 == lg['stage2_width']
        rid = item['reference_id']
        if rid not in refs:
            refs[rid] = engine.calibrate([ctx[rid]])[0]
            counts['calibrations'] += 1
        reference = refs[rid]
        cands = [exact_pair(tok, context, c)[1] for c in item['choices']]
        Cc, _ = L._clean_cache(engine, prefix)
        hC = cache_sha(Cc, types)
        out = {'C': fact_gen(engine, Cc, last, n, cands, counts, stage)}
        old, _p = s2_record(unit['panel'], iid, 'clean', 'CCC')
        bridge_fact(out['C'], old)
        gates['bridges'].append(f'{iid} C == stage2 CCC')
        tcaches = {}
        for d in W.NEEDLES:
            cond = needle_condition(d, 'fact')
            gates['write'].append({'item': iid, 'needle': d, **write_audit(engine, cond, reference)})
            out[d] = {}
            for w in W.WINDOWS:
                mask = W.window_mask(w, n, b)
                Tc, writes, _decay = L._build_T(engine, cond, reference, prefix, mask)
                assert writes and all(r['positions'] == sum(mask) and r['width'] == n - 1 for r in writes), ('mask audit', writes)
                counts['formations'] += 1
                shallow_equal(Tc, Cc, types, cond['layer'], torch)
                if w == 'W_post':
                    kv_prefix_equal(Tc, Cc, types, b, torch)
                tcaches[(d, w)] = Tc
                hT = cache_sha(Tc, types)
                res = {}
                arms = W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())
                for arm in arms:
                    Xc, tg = build_arm(Tc, Cc, arm, types, b, torch)
                    res[arm] = fact_gen(engine, Xc, last, n, cands, counts, stage)
                    if w == 'W_all' and arm in W.STAGE2_CODE and d != W.RANDOM:
                        old, _p = s2_record(unit['panel'], iid, d, W.STAGE2_CODE[arm])
                        bridge_fact(res[arm], old)
                        gates['bridges'].append(f'{iid} {d} W_all {arm} == stage2 {W.STAGE2_CODE[arm]}')
                    del Xc
                if stage == 'preflight' and w == 'W_all':
                    tg = W.arm_targets('R+KV_all', types, b)
                    Xs = W.replace(Tc, Tc, tg, L._get, L._set, copy.deepcopy)
                    assert cache_sha(Xs, types) == hT, 'self-swap changed the cache'
                    g = L.decode(model, Xs, last, n, engine.stop_ids, max_new_tokens=1, attentions=False)
                    g0 = L.decode(model, Tc, last, n, engine.stop_ids, max_new_tokens=1, attentions=False)
                    assert g['readouts'][0]['logits_sha256'] == g0['readouts'][0]['logits_sha256'], 'self-swap t1'
                    counts['engineering'] += 2
                assert cache_sha(Tc, types) == hT, ('receiver modified', d, w)
                out[d][w] = res
            kv_prefix_equal(tcaches[(d, 'W_pre')], tcaches[(d, 'W_all')], types, b, torch)
        gates['structure'].append(f'{iid}: layers <= needle == C; W_post KV[0..b] == C; W_pre KV[0..b] == W_all KV[0..b]')
        assert cache_sha(Cc, types) == hC, 'donor modified'
        versions[v] = {'item_id': iid, 'n': n, 'b': b, 'window_positions': {w: sum(W.window_mask(w, n, b)) for w in W.WINDOWS},
                       'reference_sha256': exp.digest(reference), 'results': out}
        del tcaches
        torch.cuda.empty_cache()
    return {'task': 'fact', 'unit': unit, 'versions': versions, 'gates': gates, 'kernel_identity': R.kernel_identity()}, {}


# ---------------------------------------------------------------- code task (NCC pipeline)

def run_code_item(engine, unit, contexts, calib, conds, refs, stage, counts):
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = R.B.g_layers(types, R.NVBR.SPLIT)
    assert tuple(G) == R.G14 == W.G14
    assert tuple(R.STOP) == tuple(R.CFK.STOP) == tuple(engine.stop_ids)
    R.KRDR.QHOOK_ORIG[0] = R.gdn_module().torch_recurrent_gated_delta_rule
    a_id = unit['item_id']
    led, ncc = refs['ledger'][a_id], refs['ncc'][a_id]
    ncc_t = torch.load(ncc['_tensor_path'], map_location='cpu')
    it, pl = led['item'], led['plan']
    seg = PK.label_tokens(tok, contexts[it['id']], it['boundary_text'], encode_text)
    assert not seg['straddling_tokens'] and (seg['b'], seg['n']) == (pl['b'], pl['n']) and exp.digest(seg['ids']) == pl['prompt_token_sha256']
    prompt = seg['ids']
    prefix, last, n, b = prompt[:-1], prompt[-1], len(prompt), seg['b']
    assert (pl['p'], pl['e']) == (b + 1, n - 2)
    Bw = list(range(pl['p'], pl['e'] + 1))
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base_c = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    Cc = P.form(engine, base_c, prefix, Bw, None, calib)
    counts['formations'] += 1
    assert R.comp_sha(Cc, types, R.NVBR.ALLK, 0) == ncc['formation_hashes']['C_b'], 'C formation hash != NCC'
    f = led['tokens']['q_shared']
    tensors, out, gates = {}, {}, {'bridges': [], 'structure': [], 'write': []}
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731

    def go(cache, key):
        c1, z1 = R.t1(engine, copy.deepcopy(cache), last, n, counts, 't1')
        fs = NC.first_step(z1, f, set(R.STOP))
        r, _z2 = R.natural(engine, c1, fs['winner'], n, counts)
        r['text'] = dec(r['ids'])
        y = R.yf(r['text'], r['termination'], it)
        tensors[f't1|{key}'] = z1.to(torch.bfloat16).cpu()
        return {**fs, 'x': fs['winner'], 'N': r, 'Y': y, 'cat': NC.category(fs['first_is_f'], fs['first_stop'], r['text'], it['listed_codes'])}, z1

    out['C'], zC = go(Cc, 'C')
    assert R.bit_equal(zC.to(torch.bfloat16).cpu(), ncc_t['t1|C'])[0] and out['C']['N']['ids'] == ncc['results']['C']['N']['ids'], 'C != NCC'
    gates['bridges'].append('C t1 bf16 + natural tokens == NCC C (== CGV G1 C)')
    hC = R.comp_sha(Cc, types, R.NVBR.ALLK, 0)
    for d in W.NEEDLES:
        cond = needle_condition(d, 'code')
        assert cond['id'] == d
        gates['write'].append({'needle': d, **write_audit(engine, cond, calib)})
        with L.masked_injection(engine, cond, calib, [True] * (b + 1)) as wr:
            with torch.inference_mode():
                base_n = L.forward(model, list(prefix[:b + 1]), 0, None).past_key_values
        assert wr and all(r_['positions'] == b + 1 and r_['width'] == b + 1 for r_ in wr), ('mask audit', wr)
        counts['prefix_prefills'] += 1
        F.assert_no_hooks(model)
        Tw = {'W_post': P.form(engine, base_c, prefix, Bw, cond, calib),
              'W_all': P.form(engine, base_n, prefix, Bw, cond, calib),
              'W_pre': P.form(engine, base_n, prefix, Bw, None, calib)}
        counts['formations'] += 3
        if d == 'N_L00_C4146_D-1':
            assert R.comp_sha(Tw['W_post'], types, R.NVBR.ALLK, 0) == ncc['formation_hashes'][f'T_b|{d}'], 'L0 W_post T formation hash != NCC'
        for w, Tc in Tw.items():
            shallow_equal(Tc, Cc, types, cond['layer'], torch)
        kv_prefix_equal(Tw['W_post'], Cc, types, b, torch)
        kv_prefix_equal(Tw['W_pre'], Tw['W_all'], types, b, torch)
        out[d] = {}
        for w in W.WINDOWS:
            bT, _ = R.QKFR.edited_arm(Tw[w], Tw[w], Tw[w], G, None, 1)
            R.check_bg(bT, Tw[w], Cc, types, G, 'T', 'T')
            hb = R.comp_sha(bT, types, R.NVBR.ALLK, 0)
            res = {}
            arms = W.ARMS + ((W.ATTR_ARM,) if w == 'W_all' else ())
            for arm in arms:
                Xc, tg = build_arm(bT, Cc, arm, types, b, torch)
                res[arm], z1 = go(Xc, f'{d}|{w}|{arm}')
                if d == 'N_L00_C4146_D-1' and w == 'W_post' and arm in ('T', 'S_deep'):
                    na = {'T': 'T', 'S_deep': 'TS'}[arm]
                    assert R.bit_equal(z1.to(torch.bfloat16).cpu(), ncc_t[f't1|{d}|{na}'])[0] and res[arm]['N']['ids'] == ncc['results'][d][na]['N']['ids'], ('!= NCC', arm)
                    gates['bridges'].append(f'L0 W_post {arm} t1 bf16 + natural tokens == NCC {na}')
                del Xc
            if stage == 'preflight' and w == 'W_all':
                tg = W.arm_targets('R+KV_all', types, b)
                Xs = W.replace(bT, bT, tg, L._get, L._set, copy.deepcopy)
                assert R.comp_sha(Xs, types, R.NVBR.ALLK, 0) == hb, 'self-swap changed the cache'
                _c, zs = R.t1(engine, Xs, last, n, counts, 'engineering')
                assert R.bit_equal(zs.to(torch.bfloat16).cpu(), tensors[f't1|{d}|W_all|T'])[0], 'self-swap t1 != T'
            assert R.comp_sha(bT, types, R.NVBR.ALLK, 0) == hb, ('receiver modified', d, w)
            out[d][w] = res
            del bT
        del Tw, base_n
        torch.cuda.empty_cache()
    assert R.comp_sha(Cc, types, R.NVBR.ALLK, 0) == hC, 'donor modified'
    F.assert_no_hooks(model)
    gates['structure'].append('layers <= needle == C; W_post KV[0..b] == C; W_pre KV[0..b] == W_all KV[0..b]')
    body = {'task': 'code', 'unit': unit, 'scenario': pl['base_id'], 'item': it, 'f': f, 'n': n, 'b': b,
            'window_positions': {w: sum(W.window_mask(w, n, b)) for w in W.WINDOWS}, 'results': out, 'calibration': calib,
            'ncc_record_sha256': ncc['_record_sha256'], 'kernel_identity': R.kernel_identity(), 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

COUNT_KEYS = ('generations', 'candidate_reads', 'calibrations', 'formations', 'prefix_prefills', 'engineering',
              't1', 'n_steps', 'trajectories', 'decode_forwards', 'formation_token_forwards', 'shadow')


def limits(stage):
    units = plan(stage, 0, 1)
    nf = sum(1 for u in units if u['task'] == 'fact')
    nc = sum(1 for u in units if u['task'] == 'code')
    return {'generations': nf * 2 * PER_ITEM, 't1': nc * PER_ITEM + (len(W.NEEDLES) * nc if stage == 'preflight' else 0)}


def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md',
           HERE / 'prep/tokens.json'] + PLAN_DOCS
    ext = [WIN01_DIR / 'freeze-r01.json', WIN01_DIR / 'win_core.py', NCC_DIR / 'freeze-r01.json', NCC_FORMAL / 'verification.json', S2_DIR / 'freeze-r01.json', S2_DIR / 'stage2.py',
           S2_DIR / 'reading/development-r01/RULE.txt']
    ext += [w / 'receipt.json' for w in sorted(NCC_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + ext + [p for p in R.frozen_paths() if p not in own and p not in ext]


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
    assert len(auth['gpu_map']) == auth['maximum_workers'] and all(int(g) in (0, 1) for g in auth['gpu_map']), 'gpu_map'
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    ki = R.kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def extrapolate(pre_root):
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    sec = {t: [x['seconds'] for x in recs if x['task'] == t] for t in ('fact', 'code')}
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    by = {t: [(ws[0] / rel).stat().st_size + ((ws[0] / x['tensor_file']).stat().st_size if x.get('tensor_file') else 0)
              for x, rel in zip(recs, r['record_hashes']) if x['task'] == t] for t in ('fact', 'code')}
    mean = lambda v: sum(v) / len(v)   # noqa: E731
    dev = 24 * mean(sec['fact']) + 48 * mean(sec['code']) + 2 * load
    return {'fact_unit_seconds': mean(sec['fact']), 'code_unit_seconds': mean(sec['code']), 'load_seconds': load,
            'device_seconds': dev, 'bytes': 24 * mean(by['fact']) + 48 * mean(by['code'])}


def execute(engine, stage, output, receipt, units, gpu):
    import threading
    import torch
    tok = engine.tokenizer
    qi = R.QCDR.qc_items()
    contexts = exp.contexts_for(tok, [qi[t['plan']['qc_broad_id']] for t in R.items()])
    contexts.update(exp.contexts_for(tok, [v['item'] for v in R.ledger().values()]))
    conds = R.conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(R.CFK.STOP)
    F.hook_baseline(engine.model)
    refs = {'ledger': R.ledger(), 'ncc': R._load(NCC_FORMAL)}
    totals = {k: 0 for k in COUNT_KEYS}
    calib = {}
    hb = {'units_done': 0, 'stop': False}

    def beat():
        while not hb['stop']:
            try:
                exp.write(output / 'heartbeat.json', {'at': exp.utc(), 'pid': os.getpid(), 'units_done': hb['units_done'], 'units': len(units),
                                                     'counts': dict(totals), 'device_seconds': time.monotonic() - gpu['t0']})
            except OSError:
                pass
            for _ in range(60):
                if hb['stop']:
                    break
                time.sleep(1)
    th = threading.Thread(target=beat, daemon=True)
    th.start()
    lim = limits(stage)
    try:
        for u in units:
            started = time.monotonic()
            from collections import defaultdict
            counts = defaultdict(int)
            if u['task'] == 'fact':
                body, tensors = run_fact_pair(engine, u, stage, counts)
            else:
                rid = f"{u['base_id']}-ABC-A"
                if rid not in calib:
                    calib[rid], csha = R.QCR.nq_calibration(rid)
                    receipt.setdefault('calibration_sources', {})[rid] = csha
                body, tensors = run_code_item(engine, u, contexts, calib[rid], conds, refs, stage, counts)
            for k in COUNT_KEYS:
                totals[k] += counts.get(k, 0)
            assert totals['generations'] <= lim['generations'] and totals['t1'] <= lim['t1'], (totals, lim)
            if tensors:
                rel_t = f'tensors/{u["key"]}.pt'
                (output / 'tensors').mkdir(exist_ok=True)
                assert not (output / rel_t).exists()
                torch.save(tensors, output / rel_t)
                receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
                body['tensor_file'] = rel_t
            rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, **body, 'counts': dict(counts),
                   'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            L._store(output, receipt, f'records/{u["key"]}.json', rec)
            exp.write(output / 'receipt.json', receipt)
            assert R.B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
            hb['units_done'] += 1
            elapsed = time.monotonic() - gpu['t0']
            assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
    finally:
        hb['stop'] = True
        th.join()
    receipt['model_calls'] = totals
    receipt['bytes'] = R.B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals,
                                               'bytes': receipt['bytes']}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], int(auth['gpu_map'][worker])
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-win02-worker{worker}.lock', 'w')
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
        receipt['summary'] = execute(engine, stage, output, receipt, units, {'id': gpu, 't0': started, 'n_workers': n_workers})
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
        rec = exp.read(path / rel)
        if rec['task'] == 'code':
            assert exp.sha(path / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']]
            assert set(rec['results']) == {'C'} | set(W.NEEDLES)
            for d in W.NEEDLES:
                assert set(rec['results'][d]) == set(W.WINDOWS)
                for w in W.WINDOWS:
                    assert set(rec['results'][d][w]) == set(W.ARMS) | ({W.ATTR_ARM} if w == 'W_all' else set())
        else:
            for v in ('f0', 'f1'):
                res = rec['versions'][v]['results']
                for d in W.NEEDLES:
                    for w in W.WINDOWS:
                        assert set(res[d][w]) == set(W.ARMS) | ({W.ATTR_ARM} if w == 'W_all' else set())
                assert 'B' not in rec
        assert rec['gates']['bridges'] and rec['gates']['structure'] and rec['gates']['write']
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
            cmd = [sys.executable, '-u', str(HERE / 'w2_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        want = len(plan(stage, 0, 1))
        assert units == want, (units, want)
        gpu_s = sum(x['wall_seconds'] for x in results)
        assert gpu_s <= GPU_CAP_S[stage], ('device-time cap exceeded', gpu_s)
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                  'workers': results, 'units': units, 'verified_at': exp.utc()}, immutable=True)
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
