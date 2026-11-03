"""LVK-01: does the t1 local v (write-term value computed with the clean V conv history of the same input) reproduce the V-restoration
enhancement of the write-term k operation (plan docs/cache-local-v-k-plan-v1-2026-11-03.zh-CN.md; CONTRACT r01).  Background T; four cells
L(a, b): a = write-term value v0 (native) / v1 (shadow: V channels of the pre-update conv buffer replaced by C's, same current x); b = write-
term k k0 / k1 (KUC shadow: old k slots - mu).  Erase term always k0.  Only t1, 14 G layers.  By construction L10 / L11 equal the V / VW
backgrounds at t1 (only the G conv V channels' old slots differ afterwards): engineering bridge, not a finding.
Old panel (48 seen inputs): L00..L11 per direction (+ engineering V / VW t1 for the full-cache bridge); V / RVW from NVW records.
New panel (48 frozen held-out texts, same scenarios): L00..L11, V, VW, VE, VK, F per direction + clean C once per input.
python lvk_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
NVW_DIR = HERE.parent / 'cache-native-v-write-interaction-v1-2026-11-03'
sys.path.insert(0, str(NVW_DIR))
sys.path.insert(0, str(HERE))
import nvw_run as NVR  # noqa: E402  (frozen NVW-01 runner)

KUCR, KRDR, QSRR, QKDR = NVR.KUCR, NVR.KRDR, NVR.QSRR, NVR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = NVR.QKFR, NVR.QCOR, NVR.QSTR, NVR.QCDR, NVR.QCR, NVR.NQR, NVR.SVQ, NVR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = NVR.FC_DIR, NVR.SP_DIR, NVR.SVQ_DIR, NVR.NQ_DIR, NVR.QC_DIR, NVR.QCD_DIR, NVR.QST_DIR, NVR.QCO_DIR, NVR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE, QSR_DIR, QSR_FORMAL = NVR.QKD_DIR, NVR.QKD_FORMAL, NVR.QKD_PRE, NVR.QSR_DIR, NVR.QSR_FORMAL
KRD_DIR, KHC_DIR, KRD_FORMAL, KUC_DIR, KUC_FORMAL = NVR.KRD_DIR, NVR.KHC_DIR, NVR.KRD_FORMAL, NVR.KUC_DIR, NVR.KUC_FORMAL
NVW_FORMAL = NVW_DIR / 'runs/formal-r01'
B3R, V, P, PK, X = NVR.B3R, NVR.V, NVR.P, NVR.PK, NVR.X
CF, CFK, LR, B = NVR.CF, NVR.CFK, NVR.LR, NVR.B
F, L, T1, exp, K = NVR.F, NVR.L, NVR.T1, NVR.exp, NVR.K

PLAN_ID = 'LVK-01-LOCAL-V-WRITE-K-v1'
PLAN_DOCS = [REPO / 'docs/cache-local-v-k-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-local-v-k-self-check-v1-2026-11-03.zh-CN.md']
DESIGN, QC_INPUTS, QC_TOKENS = NVR.DESIGN, NVR.QC_INPUTS, NVR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = NVR.QCD_G, NVR.QST_FORMAL, NVR.QCO_FORMAL, NVR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = NVR.QC_FORMAL, NVR.NQ_FORMAL, NVR.SVQ_FORMAL, NVR.SP_FORMAL, NVR.NR_FORMAL, NVR.B3_FORMAL, NVR.XC_FORMAL, NVR.SK_FORMAL
HELDOUT = HERE.parent / 'cache-local-v-k-design-v1-2026-11-03/heldout-inputs-r01.json'
LEDGER = HERE / 'data/heldout-tokens-r01.json'
SPLIT, A_LAYERS, MAX_NEW, STOP = NVR.SPLIT, NVR.A_LAYERS, NVR.MAX_NEW, NVR.STOP
DIRECTIONS, OLD_DIRS, NEW_DIR = NVR.DIRECTIONS, NVR.OLD_DIRS, NVR.NEW_DIR
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ARMS_ALL, QKF_NAME = NVR.ARMS_ALL, NVR.QKF_NAME
QK, K_LO, K_HI = NVR.QK, NVR.K_LO, NVR.K_HI
LAYER0 = NVR.LAYER0
CELLS = ('00', '01', '10', '11')
OLD_PRE = ('NA-NQ01-ABC-A', 'NA-NQ02-ABC-B')
NEW_PRE = ('LVK-H-NA-NQ01-ABC-A', 'LVK-H-NA-NQ02-ABC-B')
LIMITS = {'preflight': {'formations': 20, 'prefix_prefills': 4, 'formation_token_forwards': 265 + 270, 't1': 106, 'refs': 64, 'n_steps': 106 * 31,
                        'c_t2': 106, 'decode_forwards': 106 + 106 * 31 + 106 + 64, 'trajectories': 106, 'shadow': 1680, 'calibrations': 0},
          'formal': {'formations': 480, 'prefix_prefills': 96, 'formation_token_forwards': 6375 + 6390, 't1': 2544, 'refs': 1536, 'n_steps': 2544 * 31,
                     'c_t2': 2544, 'decode_forwards': 2544 + 2544 * 31 + 2544 + 1536, 'trajectories': 2544, 'shadow': 40320, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.15 * 3600, 'formal': 1.5 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
ALLK = NVR.ALLK
COUNT_KEYS = NVR.COUNT_KEYS
PREFLIGHT_ITEMS = OLD_PRE + NEW_PRE
comp_sha, comp_sha_range, tensor_bytes_sha = NVR.comp_sha, NVR.comp_sha_range, NVR.tensor_bytes_sha
gdn_module, kernel_identity, load_vectors, qkf_traj, conditions, items = NVR.gdn_module, NVR.kernel_identity, NVR.load_vectors, NVR.qkf_traj, NVR.conditions, NVR.items
qkd_records, kuc_records, margins, natural, fwd, t1 = NVR.qkd_records, NVR.kuc_records, NVR.margins, NVR.natural, NVR.fwd, NVR.t1
bit_equal, cache_equal, UHook, custom_update, first_step, check_bg, to_key = NVR.bit_equal, NVR.cache_equal, NVR.UHook, NVR.custom_update, NVR.first_step, NVR.check_bg, NVR.to_key
V_LO = QK


def ledger():
    led = exp.read(LEDGER)
    assert led['status'] == 'passed' and led['heldout_sha256'] == exp.sha(HELDOUT)
    return led['items']


def all_units():
    old = [{'item_id': t['id'], 'base_id': t['plan']['base_id'], 'key': t['id'], 'panel': 'old'} for t in items()]
    new = [{'item_id': k, 'base_id': v['plan']['base_id'], 'key': k, 'panel': 'new'} for k, v in ledger().items()]
    return old + new


def plan(stage, worker, n_workers):
    rows = all_units()
    if stage == 'preflight':
        rows = [r for r in rows if r['item_id'] in PREFLIGHT_ITEMS]
        assert len(rows) == 4
        return rows
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [r for r in rows if r['base_id'] in mine]


def nvw_records():
    out = {}
    for w in sorted(NVW_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'NVW record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'NVW tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


def cache_equal_vmask(c1, c2, types, G):
    """As cache_equal, excluding G-layer conv V channels [4096, 8192) at positions 0..2 (old slots after the t1 shift)."""
    import torch
    nz = nm = 0
    for i, kind, f in L.component_tensors(c1, types):
        a, b = L._get(c1.layers[i], f), L._get(c2.layers[i], f)
        if kind == 'conv' and i in G:
            keep = torch.ones_like(a, dtype=torch.bool)
            keep[:, V_LO:, 0:3] = False
            nm += int((a[~keep] != b[~keep]).sum())
            a, b = a[keep], b[keep]
        ok, z = bit_equal(a, b)
        if not ok:
            return False, nz, nm, (i, f)
        nz += z
    return True, nz, nm, None


class LHook:
    """t1 forward.  mode 'cell' (a, b) or 'ref_v' (original kernel fed the shadow v).  Shadows from the pre-update conv buffer clone of this branch
    and this branch's current input x: v1 = V channels replaced by the clean C conv history; k1 = KUC edit of the old k slots.  Never written back."""

    def __init__(self, model, G, mode, a=0, b=0, vec=None, sign=None, cconv=None):
        assert mode in ('cell', 'ref_v')
        self.model, self.G, self.mode, self.a, self.b, self.vec, self.sign, self.cconv = model, tuple(G), mode, a, b, vec, sign, cconv
        self.need_v = mode == 'ref_v' or a == 1
        self.need_k = mode == 'cell' and b == 1
        self.QM = gdn_module()
        self.orig_k, self.orig_c = self.QM.torch_recurrent_gated_delta_rule, self.QM.causal_conv1d_update
        self.layer, self.mod, self.handles = None, None, []
        self.conv_calls, self.kern_calls, self.sv, self.sk, self.oracle, self.l0, self.stats = [], [], {}, {}, {}, {}, {}
        self.n_shadow = 0

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig_k and self.QM.causal_conv1d_update is self.orig_c
        for i, lay in enumerate(L.model_layers(self.model)):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(m, _a, i=i):
                    self.layer, self.mod = i, m
                self.handles.append(la.register_forward_pre_hook(pre))
        me = self

        def conv(hidden_states, conv_state, weight, bias=None, activation=None):
            if me.layer not in me.G:
                return me.orig_c(hidden_states, conv_state, weight, bias, activation)
            import torch
            Bc = conv_state.clone()
            out = me.orig_c(hidden_states, conv_state, weight, bias, activation)
            m = me.mod
            me.conv_calls.append(me.layer)
            if me.layer == LAYER0:
                me.l0['k0'] = to_key(out, m).clone()
            if me.need_v:
                B2 = torch.cat([Bc[:, :V_LO], me.cconv[me.layer][:, V_LO:]], dim=1).contiguous()
                o2 = me.orig_c(hidden_states, B2, weight, bias, activation)
                assert torch.equal(o2[:, :V_LO], out[:, :V_LO]), 'shadow v changed q/k channels'
                mixed = o2.transpose(1, 2)
                _, _, v1 = torch.split(mixed, [m.key_dim, m.key_dim, m.value_dim], dim=-1)
                me.sv[me.layer] = v1.reshape(mixed.shape[0], mixed.shape[1], -1, m.head_v_dim)
                me.n_shadow += 1
            if me.need_k:
                j = me.G.index(me.layer)
                blk, _ = QCOR.edit_block(Bc[:, :QK].clone(), me.vec[j], me.sign)
                B3 = torch.cat([blk, Bc[:, QK:]], dim=1).contiguous()
                o3 = me.orig_c(hidden_states, B3, weight, bias, activation)
                assert torch.equal(o3[:, :K_LO], out[:, :K_LO]) and torch.equal(o3[:, K_HI:], out[:, K_HI:]), 'shadow k changed q/v channels'
                me.sk[me.layer] = to_key(o3, m)
                me.n_shadow += 1
                if me.layer == LAYER0:
                    me.l0['k1'] = me.sk[me.layer].clone()
            return out

        def kern(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer not in me.G:
                return me.orig_k(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                                 use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            assert query.shape[1] == 1
            me.kern_calls.append(me.layer)
            if me.mode == 'ref_v':
                v1 = me.sv[me.layer]
                assert v1.shape == value.shape and v1.dtype == value.dtype
                return me.orig_k(query, key, v1, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                                 use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            va = me.sv[me.layer] if me.a else value
            kb = me.sk[me.layer] if me.b else key
            assert va.shape == value.shape and va.dtype == value.dtype and kb.shape == key.shape and kb.dtype == key.dtype
            o, S, err = custom_update(query, key, kb, va, g, beta, initial_state, output_final_state, use_qk_l2norm_in_kernel, me.QM.l2norm, oracle=True)
            me.oracle[me.layer] = err
            import torch
            f = lambda x: x.transpose(1, 2).to(torch.float32)[0, :, 0].double()   # noqa: E731
            v0d, vad = f(value), f(va)
            k0n = me.QM.l2norm(f(key).float(), dim=-1, eps=1e-6).double()
            kbn = me.QM.l2norm(f(kb).float(), dim=-1, eps=1e-6).double()
            bt = beta.to(torch.float32)[0, 0].double()
            me.stats[me.layer] = torch.stack([v0d.norm(dim=-1), vad.norm(dim=-1), (v0d * vad).sum(-1) / torch.clamp(v0d.norm(dim=-1) * vad.norm(dim=-1), min=1e-300),
                                              (k0n * kbn).sum(-1), bt * (kbn - k0n).norm(dim=-1) * vad.norm(dim=-1)], -1).float().cpu()
            return o, S
        self.QM.causal_conv1d_update = conv
        self.QM.torch_recurrent_gated_delta_rule = kern
        return self

    def __exit__(self, *exc):
        self.QM.causal_conv1d_update = self.orig_c
        self.QM.torch_recurrent_gated_delta_rule = self.orig_k
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self):
        assert sorted(self.kern_calls) == sorted(self.G) and sorted(self.conv_calls) == sorted(self.G), ('hook calls', self.kern_calls, self.conv_calls)
        if self.mode == 'cell':
            assert set(self.oracle) == set(self.G) and max(self.oracle.values()) <= KUCR.ORACLE_TOL, ('FP64 oracle', max(self.oracle.values()))


STAT_FIELDS = ('v0', 'va', 'cos_v0_va', 'cos_k0_kb', 'dW_k')


def t1L(engine, cache, last, n, counts, kind, hook):
    """t1 with an LHook (cache consumed)."""
    import torch
    QM = gdn_module()
    oc, ok_ = QM.causal_conv1d_update, QM.torch_recurrent_gated_delta_rule
    with hook:
        with torch.inference_mode():
            out = L.forward(engine.model, [last], n - 1, cache)
    hook.check()
    counts['shadow'] += hook.n_shadow
    assert QM.causal_conv1d_update is oc and QM.torch_recurrent_gated_delta_rule is ok_ is KRDR.QHOOK_ORIG[0], 'module function left patched'
    F.assert_no_hooks(engine.model)
    counts['decode_forwards'] += 1
    counts[kind] += 1
    z = out.logits[0, -1].float()
    assert torch.isfinite(z).all()
    return out.past_key_values, z


def form_new(engine, led, contexts, calib, conds, counts):
    """C and T(d) for a held-out input: same pipeline as QCOR.form_text (P.form, B1 window [b+1, n-2], write audit); hashes recorded."""
    import torch
    from control_engine import encode_text
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    it, pl = led['item'], led['plan']
    seg = PK.label_tokens(tok, contexts[it['id']], it['boundary_text'], encode_text)
    assert not seg['straddling_tokens'] and (seg['b'], seg['n']) == (pl['b'], pl['n']) and exp.digest(seg['ids']) == pl['prompt_token_sha256'], 'new input tokens != ledger'
    prompt = seg['ids']
    prefix, last, n = prompt[:-1], prompt[-1], len(prompt)
    Bw = list(range(pl['p'], pl['e'] + 1))
    F.assert_no_hooks(model)
    with torch.inference_mode():
        base = L.forward(model, list(prefix[:seg['b'] + 1]), 0, None).past_key_values
    counts['prefix_prefills'] += 1
    C = P.form(engine, base, prefix, Bw, None, calib)
    counts['formations'] += 1
    counts['formation_token_forwards'] += len(Bw)
    T = {}
    for d, cond in conds.items():
        au = X.write_audit(engine, cond, calib)
        au['rel_err'] = abs(au['nominal_write_norm'] - au['target_write_norm']) / au['target_write_norm']
        assert au['rel_err'] <= V.K.RULE['write_rel'], ('L0 write audit', d, au)
        T[d] = P.form(engine, base, prefix, Bw, cond, calib)
        counts['formations'] += 1
        counts['formation_token_forwards'] += len(Bw)
    q_shared, t2, d2 = QSTR.shared_tokens(tok, it)
    assert q_shared == led['tokens']['q_shared']
    info = {'item': it, 'q_shared': q_shared, 'last': last, 'n': n, 'scenario': pl['base_id'],
            'code_tokens': {it['target']: t2, **dict(zip(it['distractors'], d2))},
            'hashes': {'base_b': comp_sha(base, types, ALLK, 0), 'C_b': comp_sha(C, types, ALLK, 0), **{f'T_b|{d}': comp_sha(T[d], types, ALLK, 0) for d in conds}}}
    return C, T, info


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30) and G[0] == LAYER0
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids), 'stop ids != parser stop set'
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a = unit['item_id']
    panel = unit['panel']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    nz_total, oracle_max, vmask_diff = 0, 0.0, 0
    if panel == 'old':
        C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
        nvw = refs['nvw'][a]
        nvw_t = torch.load(nvw['_tensor_path'], map_location='cpu')
        fFs = {d: nvw['directions'][d]['fF'] for d in conds}
    else:
        led = refs['ledger'][a]
        C, T, info = form_new(engine, led, contexts, calib, conds, counts)
        fFs = {d: led['tokens']['q_shared'] for d in conds}
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731

    def finish(c1, z1, key, d, fF):
        _, zc = fwd(engine, copy.deepcopy(c1), fF, n, counts, 'c_t2')
        M, Mall = margins(zc, it, code_tok, comp)
        tensors[f'C|{key}|{d}'] = zc.to(torch.bfloat16).cpu()
        tensors[f't1|{key}|{d}'] = z1.to(torch.bfloat16).cpu()
        x_ = int(z1.argmax())
        r, _ = natural(engine, copy.deepcopy(c1), x_, n, counts)
        r['text'] = dec(r['ids'])
        return {'x': x_, 'first': first_step(z1, fF), 'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'N': r}, zc

    if panel == 'new':      # clean C once per input (task validity)
        fF0 = fFs[DIRECTIONS[0]]
        cC, zC = t1(engine, copy.deepcopy(C), info['last'], n, counts, 't1')
        out['C_clean'], _ = finish(cC, zC, 'C', 'all', fF0)
        del cC
    for d in conds:
        s = info['scenario']
        fF = fFs[d]
        assert fF not in STOP
        _, u, sign = ARMS_ALL['Rk']
        vec = QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        bV, _ = QKFR.edited_arm(T[d], T[d], C, G, None, 1)
        check_bg(bV, T[d], C, types, G, 'T', 'C')
        hbT, hbV = comp_sha(bT, types, ALLK, 0), comp_sha(bV, types, ALLK, 0)
        res, c1s, z1s, l0 = {}, {}, {}, {}
        # ---- L cells on T
        c1s['L00'], z1 = t1(engine, copy.deepcopy(bT), info['last'], n, counts, 't1')
        z1s['L00'] = z1
        res['L00'], zc00 = finish(c1s['L00'], z1, 'L00', d, fF)
        for code in ('01', '10', '11'):
            hk = LHook(model, G, 'cell', a=int(code[0]), b=int(code[1]), vec=vec, sign=sign, cconv=cconv)
            c, z = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
            oracle_max = max(oracle_max, max(hk.oracle.values()))
            tensors[f'stats|L{code}|{d}'] = torch.stack([hk.stats[l] for l in G])
            l0[code] = dict(hk.l0)
            c1s[f'L{code}'], z1s[f'L{code}'] = c, z
            res[f'L{code}'], _ = finish(c, z, f'L{code}', d, fF)
        assert bit_equal(l0['01']['k0'], l0['11']['k0'])[0] and bit_equal(l0['01']['k1'], l0['11']['k1'])[0], ('layer-13 k differs across v conditions', d)
        # ---- engineering references on T
        cn, zn = t1(engine, copy.deepcopy(bT), info['last'], n, counts, 'refs', hook=UHook(model, G, 'noop'))
        okz, z0 = bit_equal(zn, z1s['L00'])
        okc, zc0, _, fail = cache_equal(cn, c1s['L00'], types, G)
        assert okz and okc, ('no-op custom update != native (T)', d, fail)
        nz_total += z0 + zc0
        hk = LHook(model, G, 'ref_v', cconv=cconv)
        cn, zn = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 'refs', hk)
        okz, z0 = bit_equal(zn, z1s['L10'])
        okc, zc0, _, fail = cache_equal(cn, c1s['L10'], types, G)
        assert okz and okc, ('L10 != original kernel fed the shadow v', d, fail)
        nz_total += z0 + zc0
        # ---- V-background arms (old: t1 only for the bridge; new: full arms)
        if panel == 'old':
            cV, zV = t1(engine, copy.deepcopy(bV), info['last'], n, counts, 'refs')
            hk = UHook(model, G, 'cell', code='01', vec=vec, sign=sign)
            cVW, zVW = t1(engine, copy.deepcopy(bV), info['last'], n, counts, 'refs', hook=hk)
            oracle_max = max(oracle_max, max(hk.oracle.values()))
            for key, nk in (('L00', 'T'), ('L01', 'RTW'), ('L10', 'V'), ('L11', 'RVW')):
                assert bit_equal(z1s[key].to(torch.bfloat16).cpu(), nvw_t[f't1|{nk}|{d}'])[0], ('t1 != NVW', key, nk, d)
            for key, nk in (('L00', 'T'), ('L01', 'RTW')):
                na = nvw['directions'][d]['arms'][nk]
                assert res[key]['N']['ids'] == na['N']['ids'] and res[key]['C']['M'] == na['C']['M'], ('trajectory != NVW', key, nk, d)
                assert bit_equal(tensors[f'C|{key}|{d}'], nvw_t[f'C|{nk}|{d}'])[0], ('C t2 != NVW', key, nk, d)
            assert bit_equal(zV.to(torch.bfloat16).cpu(), nvw_t[f't1|V|{d}'])[0] and bit_equal(zVW.to(torch.bfloat16).cpu(), nvw_t[f't1|RVW|{d}'])[0], ('V/VW t1 != NVW', d)
        else:
            cV, zV = t1(engine, copy.deepcopy(bV), info['last'], n, counts, 't1')
            res['V'], _ = finish(cV, zV, 'V', d, fF)
            arms_v = {}
            for name, code in (('VW', '01'), ('VE', '10'), ('VK', '11')):
                hk = UHook(model, G, 'cell', code=code, vec=vec, sign=sign)
                c, z = t1(engine, copy.deepcopy(bV), info['last'], n, counts, 't1', hook=hk)
                oracle_max = max(oracle_max, max(hk.oracle.values())) if hk.oracle else oracle_max
                arms_v[name] = (c, z)
                res[name], _ = finish(c, z, name, d, fF)
            cVW, zVW = arms_v['VW']
            cn, zn = t1(engine, copy.deepcopy(bV), info['last'], n, counts, 'refs', hook=UHook(model, G, 'noop'))
            okz, z0 = bit_equal(zn, zV)
            okc, zc0, _, fail = cache_equal(cn, cV, types, G)
            assert okz and okc, ('no-op custom update != native (V)', d, fail)
            nz_total += z0 + zc0
            cr, zr = t1(engine, copy.deepcopy(bV), info['last'], n, counts, 'refs', hook=UHook(model, G, 'ref_full', vec=vec, sign=sign))
            okz, z0 = bit_equal(arms_v['VK'][1], zr)
            okc, zc0, _, fail = cache_equal(arms_v['VK'][0], cr, types, G)
            assert okz and okc, ('VK != original kernel fed the shadow k', d, fail)
            nz_total += z0 + zc0
            bF, _ = QKFR.edited_arm(T[d], C, C, G, None, 1)
            check_bg(bF, T[d], C, types, G, 'C', 'C')
            cF, zF = t1(engine, copy.deepcopy(bF), info['last'], n, counts, 't1')
            res['F'], _ = finish(cF, zF, 'F', d, fF)
            del arms_v, cF, bF, cr
        # ---- full-layer bridge: L10 == V, L11 == VW at t1 (only G conv V old slots may differ)
        for key, (cc_, zz_) in (('L10', (cV, zV)), ('L11', (cVW, zVW))):
            okz, z0 = bit_equal(z1s[key], zz_)
            okc, zc0, nm, fail = cache_equal_vmask(c1s[key], cc_, types, G)
            assert okz and okc, ('t1 bridge to V background failed', key, d, fail)
            nz_total += z0 + zc0
            vmask_diff += nm
            assert int(z1s[key].argmax()) == int(zz_.argmax())
        assert comp_sha(bT, types, ALLK, 0) == hbT and comp_sha(bV, types, ALLK, 0) == hbV, ('pre-t1 background cache modified', d)
        out[d] = {'fF': fF, 'arms': res}
        del c1s, cV, cVW, bT, bV
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['backgrounds'] = 'T / V (/ F) built from the same C/T formation; only the listed G conv slices from C; sources unchanged'
    gates['bridge_t1'] = 'L10 == V and L11 == VW at t1: logits and every cache tensor except G conv V channels at old-slot positions 0..2; same first token'
    gates['refs'] = 'no-op custom == native (T; V on new); L10 == original kernel fed shadow v; VK == original kernel fed shadow k (new)'
    gates['shadows'] = 'shadow v leaves q/k channels unchanged, shadow k leaves q/v unchanged; built from pre-update clones; never written back'
    gates['layer13'] = 'native and shadow k at layer 13 identical between L01 and L11'
    gates['oracle'] = f'selective updates vs FP64 three-term formula, max relative error {oracle_max:.3g} <= {KUCR.ORACLE_TOL}'
    gates['hooks'] = 'hooks once per G layer at t1 only; module functions restored; stop ids == parser'
    if panel == 'old':
        gates['nvw_bridge'] = 'L00/L01 == NVW T/RTW (t1, C t2 bf16, natural tokens, M); L10/L11 and V/VW t1 == NVW V/RVW t1 (bf16)'
    else:
        gates['new_input'] = 'held-out tokens == frozen ledger; shared first token == ledger; formation hashes recorded'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'panel': panel, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'signed_zero_exceptions': nz_total, 'oracle_max': oracle_max, 'vmask_elements_differing': vmask_diff, 'stat_fields': list(STAT_FIELDS),
            'formation_hashes': info.get('hashes'), 'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, HELDOUT, LEDGER,
         HERE.parent / 'cache-local-v-k-design-v1-2026-11-03/source-audit-r01.json', NVW_DIR / 'nvw_run.py', NVW_DIR / 'freeze-r01.json',
         NVW_DIR / 'analysis/nvw-readouts-r01.json', KUC_DIR / 'kuc_run.py', KUC_DIR / 'freeze-r01.json', KRD_DIR / 'krd_run.py', QSR_DIR / 'qsr_run.py',
         QKD_DIR / 'qkd_run.py', QKDR.RPOST_C_MANIFEST, QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST,
         QST_DIR / 'qst_core.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    qco = [w / 'receipt.json' for w in sorted(QCO_FORMAL.glob('worker-*')) if w.is_dir()] + [QCO_FORMAL / 'verification.json']
    qkf = [w / 'receipt.json' for w in sorted(QKF_FORMAL.glob('worker-*')) if w.is_dir()] + [QKF_FORMAL / 'verification.json']
    qkd = [w / 'receipt.json' for w in sorted(QKD_FORMAL.glob('worker-*')) if w.is_dir()] + [QKD_FORMAL / 'verification.json'] + [w / 'receipt.json' for w in sorted(QKD_PRE.glob('worker-*')) if w.is_dir()]
    qsr = [w / 'receipt.json' for w in sorted(QSR_FORMAL.glob('worker-*')) if w.is_dir()] + [QSR_FORMAL / 'verification.json']
    krd = [w / 'receipt.json' for w in sorted(KRD_FORMAL.glob('worker-*')) if w.is_dir()] + [KRD_FORMAL / 'verification.json']
    krd += [w / 'receipt.json' for w in sorted(KUC_FORMAL.glob('worker-*')) if w.is_dir()] + [KUC_FORMAL / 'verification.json']
    krd += [w / 'receipt.json' for w in sorted(NVW_FORMAL.glob('worker-*')) if w.is_dir()] + [NVW_FORMAL / 'verification.json']
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + qco + qkf + qkd + qsr + krd + [p for p in B3R.frozen_paths() if p not in own]


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
    man = exp.read(QKDR.RPOST_C_MANIFEST)
    assert man['status'] == 'passed' and exp.sha(QKDR.RPOST_C) == man['rpost_sha256'], 'QKD C1343 r_post != manifest'
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'] and ex['bytes'] <= STORAGE_LIMIT, ('preflight extrapolation exceeds the formal cap', ex)
    return auth


def extrapolate(pre_root):
    """Formal estimate from the preflight worker, per panel: mean per-text seconds (old / new preflight texts) x 48 each + per-worker model load
    x 2; bytes likewise per panel."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    recs = [exp.read(ws[0] / rel) for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    per = {}
    for pn in ('old', 'new'):
        xs = [x for x in recs if x['panel'] == pn]
        per[pn] = {'seconds': sum(x['seconds'] for x in xs) / len(xs),
                   'bytes': sum((ws[0] / x['tensor_file']).stat().st_size for x in xs) / len(xs)}
    dev = 48 * (per['old']['seconds'] + per['new']['seconds']) + 2 * load
    return {'per_panel': per, 'load_seconds': load, 'device_seconds': dev, 'bytes': 48 * (per['old']['bytes'] + per['new']['bytes']), 'texts': 96}


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    qctok = exp.read(QC_TOKENS)
    vecs = load_vectors()
    refs = {'nvw': nvw_records(), 'ledger': ledger()}
    thr = None
    import threading
    hb = {'totals': dict(totals), 'units_done': 0, 'stop': False}
    def beat():
        while not hb['stop']:
            try:
                exp.write(output / 'heartbeat.json', {'at': exp.utc(), 'pid': os.getpid(), 'units_done': hb['units_done'], 'units': len(units),
                                                     'model_calls': hb['totals'], 'device_seconds': time.monotonic() - gpu['t0'], 'bytes': B.dir_bytes(output)})
            except OSError:
                pass
            for _ in range(60):
                if hb['stop']:
                    break
                time.sleep(1)
    th = threading.Thread(target=beat, daemon=True)
    th.start()
    try:
        out = _execute_units(engine, stage, output, receipt, units, gpu, contexts, conds, totals, calib, qctok, vecs, refs, thr, hb, torch)
    finally:
        hb['stop'] = True
        th.join()
    return out


def _execute_units(engine, stage, output, receipt, units, gpu, contexts, conds, totals, calib, qctok, vecs, refs, thr, hb, torch):
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = QCR.nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        body, tensors = run_item(engine, u, contexts, calib[rid], conds, qctok, output, stage, vecs=vecs, refs=refs)
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
        hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
        elapsed = time.monotonic() - gpu['t0']
        assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
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
    lock = open(f'/tmp/acupuncture-lvk-worker{worker}.lock', 'w')
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
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in r['record_hashes'].items():
        assert exp.sha(path / rel) == digest, rel
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        rel_t = rec['tensor_file']
        assert exp.sha(path / rel_t) == r['tensor_hashes'][rel_t], rel_t
        assert set(rec['directions']) == set(DIRECTIONS) | ({'C_clean'} if rec['panel'] == 'new' else set())
        for d in DIRECTIONS:
            want = {'L00', 'L01', 'L10', 'L11'} | ({'V', 'VW', 'VE', 'VK', 'F'} if rec['panel'] == 'new' else set())
            assert set(rec['directions'][d]['arms']) == want
        for g in ('backgrounds', 'bridge_t1', 'refs', 'shadows', 'layer13', 'oracle', 'hooks', 'calibration') + (('nvw_bridge',) if rec['panel'] == 'old' else ('new_input',)):
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
            cmd = [sys.executable, '-u', str(HERE / 'lvk_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
        assert units == (len(PREFLIGHT_ITEMS) if stage == 'preflight' else 96), units
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
