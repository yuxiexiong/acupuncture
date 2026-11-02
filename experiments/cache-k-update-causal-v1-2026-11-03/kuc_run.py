"""KUC-01: which t1 update term carries the k change into later target choice (plan docs/cache-k-update-causal-plan-v1-2026-11-03.zh-CN.md;
CONTRACT r01).  Per (input, direction): original endpoints V, F, Rk, Ak, Ark (natural + C t2, replay gates); families R (V background,
shadow k = conv with -mu on the old k slots), A (F, +mu), Z (F, +r_post); cells 10 (shadow k in the erase term, both positions), 01 (shadow k
in the write term), 11 (both = full t1 k-node replacement).  Only at t1, only the 14 G layers; shadow conv never written back; everything after
t1 is free.  Engineering t1 references: custom update with no change on V and F; original kernel fed the shadow k on R/A/Z.
python kuc_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
KRD_DIR = HERE.parent / 'cache-k-repair-dependence-v1-2026-11-03'
KHC_DIR = HERE.parent / 'cache-k-history-carrier-v1-2026-11-03'
sys.path.insert(0, str(KRD_DIR))
sys.path.insert(0, str(HERE))
import krd_run as KRDR  # noqa: E402  (frozen KRD-01 runner, r02)

QSRR, QKDR = KRDR.QSRR, KRDR.QKDR
QKFR, QCOR, QSTR, QCDR, QCR, NQR, SVQ, NRR = KRDR.QKFR, KRDR.QCOR, KRDR.QSTR, KRDR.QCDR, KRDR.QCR, KRDR.NQR, KRDR.SVQ, KRDR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR, QCO_DIR, QKF_DIR = KRDR.FC_DIR, KRDR.SP_DIR, KRDR.SVQ_DIR, KRDR.NQ_DIR, KRDR.QC_DIR, KRDR.QCD_DIR, KRDR.QST_DIR, KRDR.QCO_DIR, KRDR.QKF_DIR
QKD_DIR, QKD_FORMAL, QKD_PRE, QSR_DIR, QSR_FORMAL = KRDR.QKD_DIR, KRDR.QKD_FORMAL, KRDR.QKD_PRE, KRDR.QSR_DIR, KRDR.QSR_FORMAL
KRD_FORMAL = KRD_DIR / 'runs/formal-r02'
B3R, V, P, PK, X = KRDR.B3R, KRDR.V, KRDR.P, KRDR.PK, KRDR.X
CF, CFK, LR, B = KRDR.CF, KRDR.CFK, KRDR.LR, KRDR.B
F, L, T1, exp, K = KRDR.F, KRDR.L, KRDR.T1, KRDR.exp, KRDR.K

PLAN_ID = 'KUC-01-K-UPDATE-CAUSAL-v1'
PLAN_DOCS = [REPO / 'docs/cache-k-update-causal-plan-v1-2026-11-03.zh-CN.md', REPO / 'docs/cache-kuc-self-check-v1-2026-11-03.zh-CN.md']
DESIGN, QC_INPUTS, QC_TOKENS = KRDR.DESIGN, KRDR.QC_INPUTS, KRDR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL, QKF_FORMAL = KRDR.QCD_G, KRDR.QST_FORMAL, KRDR.QCO_FORMAL, KRDR.QKF_FORMAL
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = KRDR.QC_FORMAL, KRDR.NQ_FORMAL, KRDR.SVQ_FORMAL, KRDR.SP_FORMAL, KRDR.NR_FORMAL, KRDR.B3_FORMAL, KRDR.XC_FORMAL, KRDR.SK_FORMAL
SPLIT, A_LAYERS, MAX_NEW, STOP = KRDR.SPLIT, KRDR.A_LAYERS, KRDR.MAX_NEW, KRDR.STOP
DIRECTIONS, OLD_DIRS, NEW_DIR = KRDR.DIRECTIONS, KRDR.OLD_DIRS, KRDR.NEW_DIR
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
ARMS_ALL, QKF_NAME = KRDR.ARMS, KRDR.QKF_NAME
ORIG = ('V', 'F', 'Rk', 'Ak', 'Ark')
FAMILIES = {'R': ('V', 'Rk'), 'A': ('F', 'Ak'), 'Z': ('F', 'Ark')}          # family: (background arm, original arm whose k edit the shadow uses)
CELLS = ('10', '01', '11')
QK = 4096
K_LO, K_HI = 2048, 4096
LIMITS = {'preflight': {'formations': 10, 'prefix_prefills': 2, 'formation_token_forwards': 265, 't1': 112, 'refs': 40, 'n_steps': 3472,
                        'c_t2': 112, 'decode_forwards': 3736, 'trajectories': 112, 'shadow': 1344, 'calibrations': 0},
          'formal': {'formations': 240, 'prefix_prefills': 48, 'formation_token_forwards': 6375, 't1': 2688, 'refs': 960, 'n_steps': 83328,
                     'c_t2': 2688, 'decode_forwards': 89664, 'trajectories': 2688, 'shadow': 32256, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.2 * 3600, 'formal': 2.0 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
ORACLE_TOL = 1e-5
ALLK = KRDR.ALLK
COUNT_KEYS = ('formations', 'prefix_prefills', 'formation_token_forwards', 't1', 'refs', 'n_steps', 'c_t2', 'decode_forwards',
              'trajectories', 'shadow')
PREFLIGHT_ITEMS = KRDR.PREFLIGHT_ITEMS
comp_sha, comp_sha_range, tensor_bytes_sha = KRDR.comp_sha, KRDR.comp_sha_range, KRDR.tensor_bytes_sha
gdn_module, kernel_identity, load_vectors, qkf_traj, conditions, items = KRDR.gdn_module, KRDR.kernel_identity, KRDR.load_vectors, KRDR.qkf_traj, KRDR.conditions, KRDR.items
qkd_records, margins, natural, fwd = KRDR.qkd_records, KRDR.margins, KRDR.natural, KRDR.fwd


def plan(stage, worker, n_workers):
    return QKDR.plan(stage, worker, n_workers)


def krd_records():
    out = {}
    for w in sorted(KRD_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'KRD record hash'
            rec = exp.read(w / rel)
            out[rec['text']] = rec
    return out


# ---------------------------------------------------------------- exact comparisons

def bit_equal(a, b):
    """Byte-level equality with the single frozen exception: elements whose bit patterns differ only because one is +0 and the other -0.
    Returns (ok, n_signed_zero).  Any other difference -> ok False."""
    import torch
    if a.shape != b.shape or a.dtype != b.dtype:
        return False, 0
    a, b = a.detach().contiguous(), b.detach().contiguous()
    iv = {2: torch.int16, 4: torch.int32, 8: torch.int64}[a.element_size()]
    ai, bi = a.view(iv), b.view(iv)
    diff = ai != bi
    n = int(diff.sum())
    if n == 0:
        return True, 0
    ok = bool(((a[diff] == 0) & (b[diff] == 0)).all())
    return ok, (n if ok else 0)


def cache_equal(c1, c2, types, G, mask_k_old=False):
    """Every cache tensor equal (bit_equal); if mask_k_old, G-layer conv k channels [2048, 4096) at positions 0..2 (old slots 1..3 after the t1
    shift) are excluded.  Returns (ok, n_signed_zero, n_masked_diff, first_failure)."""
    import torch
    nz = nm = 0
    for i, kind, f in L.component_tensors(c1, types):
        a, b = L._get(c1.layers[i], f), L._get(c2.layers[i], f)
        if mask_k_old and kind == 'conv' and i in G:
            keep = torch.ones_like(a, dtype=torch.bool)
            keep[:, K_LO:K_HI, 0:3] = False
            nm += int((a[~keep] != b[~keep]).sum())
            a, b = a[keep], b[keep]
        ok, z = bit_equal(a, b)
        if not ok:
            return False, nz, nm, (i, f)
        nz += z
    return True, nz, nm, None


# ---------------------------------------------------------------- t1 update-term controller

def custom_update(query, key_E, key_W, value, g, beta, initial_state, output_final_state, use_qk_l2norm_in_kernel, l2norm, oracle=False):
    """Original torch_recurrent_gated_delta_rule order with the erase term using key_E (both positions) and the write term using key_W:
    S_nat = D + kE (x) ((v - kE^T D) beta);  S1 = S_nat + (kW - kE) (x) (beta v);  o = S1^T q.  Returns (out, S1, oracle_err or None)."""
    import torch
    initial_dtype = query.dtype
    _, seq, _, dk = key_E.shape
    query, kE, kW, value, beta, decay = [x.transpose(1, 2).to(torch.float32, memory_format=torch.contiguous_format)
                                         for x in (query, key_E, key_W, value, beta, g)]
    if use_qk_l2norm_in_kernel:
        query = l2norm(query, dim=-1, eps=1e-6)
        kE = l2norm(kE, dim=-1, eps=1e-6)
        kW = l2norm(kW, dim=-1, eps=1e-6)
    query = query / (query.shape[-1] ** 0.5)
    S = initial_state.to(value)
    S_in = S
    out = torch.zeros_like(value)
    err = None
    for i in range(seq):
        q_t, e_t, w_t, v_t = query[:, :, i], kE[:, :, i], kW[:, :, i], value[:, :, i]
        decay_t = decay[:, :, i].exp()[..., None, None]
        S = S * decay_t
        beta_t = beta[:, :, i].unsqueeze(-1)
        kv_mem = (S * e_t.unsqueeze(-1)).sum(dim=-2)
        delta = (v_t - kv_mem) * beta_t
        S = S + e_t.unsqueeze(-1) * delta.unsqueeze(-2)
        S = S + (w_t - e_t).unsqueeze(-1) * (beta_t * v_t).unsqueeze(-2)
        out[:, :, i] = (S * q_t.unsqueeze(-1)).sum(dim=-2)
        if oracle:
            Dd = S_in.double() * decay[:, :, i].double().exp()[..., None, None]
            ed, wd, vd, bd, qd = e_t.double(), w_t.double(), v_t.double(), beta_t.double(), q_t.double()
            pd = (Dd * ed.unsqueeze(-1)).sum(-2)
            So = Dd - bd.unsqueeze(-1) * ed.unsqueeze(-1) * pd.unsqueeze(-2) + bd.unsqueeze(-1) * wd.unsqueeze(-1) * vd.unsqueeze(-2)
            oo = (So * qd.unsqueeze(-1)).sum(-2)
            eS = float((S.double() - So).abs().max() / max(1.0, float(So.abs().max())))
            eo = float((out[:, :, i].double() - oo).abs().max() / max(1.0, float(oo.abs().max())))
            err = max(eS, eo)
    S = S if output_final_state else None
    out = out.transpose(1, 2).contiguous().to(initial_dtype)
    return out, S, err


class UHook:
    """One t1 forward.  mode: 'cell' (code '10' / '01' / '11'), 'noop' (custom update, kE = kW = native k), 'ref_full' (original kernel fed the
    shadow k).  Shadow k per G layer: clone the pre-update conv buffer, apply the frozen k edit (QCOR.edit_block on channels [0, 4096) with the
    k-masked vector, as in QKF edited_arm) to the clone, run the same causal_conv1d_update on it with the same current input, then the module's
    split / reshape / repeat_interleave.  The clone is never written back."""

    def __init__(self, model, G, mode, code=None, vec=None, sign=None):
        assert mode in ('cell', 'noop', 'ref_full')
        self.model, self.G, self.mode, self.code, self.vec, self.sign = model, tuple(G), mode, code, vec, sign
        self.QM = gdn_module()
        self.orig_k = self.QM.torch_recurrent_gated_delta_rule
        self.orig_c = self.QM.causal_conv1d_update
        self.layer, self.mod, self.handles = None, None, []
        self.conv_calls, self.kern_calls, self.shadow, self.oracle = [], [], {}, {}

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
            if me.layer not in me.G or me.mode == 'noop':
                return me.orig_c(hidden_states, conv_state, weight, bias, activation)
            import torch
            Bc = conv_state.clone()
            out = me.orig_c(hidden_states, conv_state, weight, bias, activation)
            j = me.G.index(me.layer)
            blk, _ = QCOR.edit_block(Bc[:, :QK].clone(), me.vec[j], me.sign)
            B2 = torch.cat([blk, Bc[:, QK:]], dim=1).contiguous()
            out1 = me.orig_c(hidden_states, B2, weight, bias, activation)
            assert torch.equal(out1[:, :K_LO], out[:, :K_LO]) and torch.equal(out1[:, K_HI:], out[:, K_HI:]), 'shadow changed q/v channels'
            m = me.mod
            mixed = out1.transpose(1, 2)
            _, key1, _ = torch.split(mixed, [m.key_dim, m.key_dim, m.value_dim], dim=-1)
            b_, s_ = mixed.shape[0], mixed.shape[1]
            key1 = key1.reshape(b_, s_, -1, m.head_k_dim)
            if m.num_v_heads // m.num_k_heads > 1:
                key1 = key1.repeat_interleave(m.num_v_heads // m.num_k_heads, dim=2)
            me.shadow[me.layer] = key1
            me.conv_calls.append(me.layer)
            return out

        def kern(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer not in me.G:
                return me.orig_k(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                                 use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            assert query.shape[1] == 1
            me.kern_calls.append(me.layer)
            if me.mode == 'noop':
                o, S, _ = custom_update(query, key, key, value, g, beta, initial_state, output_final_state, use_qk_l2norm_in_kernel, me.QM.l2norm)
                return o, S
            k1 = me.shadow[me.layer]
            assert k1.shape == key.shape and k1.dtype == key.dtype and k1.device == key.device
            if me.mode == 'ref_full':
                return me.orig_k(query, k1, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                                 use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            kE = k1 if me.code[0] == '1' else key
            kW = k1 if me.code[1] == '1' else key
            o, S, err = custom_update(query, kE, kW, value, g, beta, initial_state, output_final_state, use_qk_l2norm_in_kernel, me.QM.l2norm,
                                      oracle=me.code in ('10', '01'))
            if err is not None:
                me.oracle[me.layer] = err
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
        assert sorted(self.kern_calls) == sorted(self.G), ('kernel hook calls', self.kern_calls)
        if self.mode != 'noop':
            assert sorted(self.conv_calls) == sorted(self.G), ('conv hook calls', self.conv_calls)
        if self.mode == 'cell' and self.code in ('10', '01'):
            assert set(self.oracle) == set(self.G) and max(self.oracle.values()) <= ORACLE_TOL, ('FP64 oracle', max(self.oracle.values()))


def t1(engine, cache, last, n, counts, kind, hook=None):
    """t1 forward (cache consumed) with an optional UHook; asserts both module functions restored and no hooks left."""
    import torch
    QM = gdn_module()
    oc, ok_ = QM.causal_conv1d_update, QM.torch_recurrent_gated_delta_rule
    if hook is not None:
        with hook:
            with torch.inference_mode():
                out = L.forward(engine.model, [last], n - 1, cache)
        hook.check()
        if hook.mode != 'noop':
            counts['shadow'] += len(hook.conv_calls)
    else:
        with torch.inference_mode():
            out = L.forward(engine.model, [last], n - 1, cache)
    assert QM.causal_conv1d_update is oc and QM.torch_recurrent_gated_delta_rule is ok_ is KRDR.QHOOK_ORIG[0], 'module function left patched'
    F.assert_no_hooks(engine.model)
    counts['decode_forwards'] += 1
    counts[kind] += 1
    z = out.logits[0, -1].float()
    assert torch.isfinite(z).all()
    return out.past_key_values, z


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    nz_total, oracle_max = 0, 0.0
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    qkd, krd = refs['qkd'][a], refs['krd'][a]
    qkd_t = torch.load(qkd['_tensor_path'], map_location='cpu')
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731

    def finish(c1, z1, x_, key):
        """natural trajectory + C t2 from a post-t1 cache (not consumed)."""
        _, zc = fwd(engine, copy.deepcopy(c1), fF, n, counts, 'c_t2')
        M, Mall = margins(zc, it, code_tok, comp)
        tensors[f'C|{key}|{d}'] = zc.to(torch.bfloat16).cpu()
        tensors[f't1|{key}|{d}'] = z1.to(torch.bfloat16).cpu()
        r, _ = natural(engine, copy.deepcopy(c1), x_, n, counts)
        r['text'] = dec(r['ids'])
        return {'x': x_, 't1_sha': F.th(z1), 'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'N': r}, zc

    for d in conds:
        s = info['scenario']
        kd = krd['directions'][d]
        fF = (refs['qkf'][a][f'F|{d}']['ids'] if d in OLD_DIRS else refs['qco'][a][f'F|{d}']['ids'])[0]
        assert fF not in STOP and fF == kd['fF']
        base, c1, z1s, res_o, vecd, hbase = {}, {}, {}, {}, {}, {}
        for arm in ORIG:
            b_, u, sign = ARMS_ALL[arm]
            qb = T[d] if b_ == 'T' else C
            vec = None if u is None else QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
            vecd[arm] = (vec, sign)
            cc, _ = QKFR.edited_arm(T[d], qb, C, G, vec, sign)
            QCOR.check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
            base[arm] = cc
            hbase[arm] = comp_sha(cc, types, ALLK, 0)
            c1[arm], z1 = t1(engine, copy.deepcopy(cc), info['last'], n, counts, 't1')
            z1s[arm] = z1
            ref = refs['qkf'][a][f'{QKF_NAME[arm]}|{d}'] if d in OLD_DIRS else qkd['c1343_trajectories'][arm]
            assert F.th(z1) == ref['first']['logits_sha256'] and comp_sha(c1[arm], types, ALLK, 0) == ref['first']['cache_sha256'], ('t1 != reference', arm, d)
            x_ = int(z1.argmax())
            assert x_ == ref['ids'][0] == kd['x'][arm]
            res, zc = finish(c1[arm], z1, x_, arm)
            assert res['N']['ids'] == ref['ids'] and res['N']['termination'] == ref['termination'], ('original trajectory != reference', arm, d)
            assert res['C']['M'] == qkd['arms'][d][arm]['M'] and torch.equal(zc.to(torch.bfloat16).cpu(), qkd_t[f'Ct2|{arm}|{d}']), ('C t2 != QKD', arm, d)
            res_o[arm] = res
        # engineering t1 references: custom update with no change == native (V, F)
        for arm in ('V', 'F'):
            cn, zn = t1(engine, copy.deepcopy(base[arm]), info['last'], n, counts, 'refs', hook=UHook(model, G, 'noop'))
            okz, z0 = bit_equal(zn, z1s[arm])
            okc, zc_, _, fail = cache_equal(cn, c1[arm], types, G)
            assert okz and okc, ('no-op custom update != native', arm, d, fail)
            nz_total += z0 + zc_
        new = {}
        for fam, (bg, src) in FAMILIES.items():
            vec, sign = vecd[src]
            cr, zr = t1(engine, copy.deepcopy(base[bg]), info['last'], n, counts, 'refs', hook=UHook(model, G, 'ref_full', vec=vec, sign=sign))
            for code in CELLS:
                hk = UHook(model, G, 'cell', code=code, vec=vec, sign=sign)
                cn, zn = t1(engine, copy.deepcopy(base[bg]), info['last'], n, counts, 't1', hook=hk)
                if hk.oracle:
                    oracle_max = max(oracle_max, max(hk.oracle.values()))
                if code == '11':
                    okz, z0 = bit_equal(zn, zr)
                    okc, zc_, _, fail = cache_equal(cn, cr, types, G)
                    assert okz and okc, ('11 != original kernel fed the shadow k', fam, d, fail)
                    nz_total += z0 + zc_
                    okz, z0 = bit_equal(zn, z1s[src])
                    okc, zc_, nmask, fail = cache_equal(cn, c1[src], types, G, mask_k_old=True)
                    assert okz and okc, ('11 t1 != original edited arm outside the old k slots', fam, d, fail)
                    nz_total += z0 + zc_
                    slot_diff = nmask
                res, _ = finish(cn, zn, int(zn.argmax()), f'{fam}{code}')
                if code == '11':
                    res['old_k_slot_elements_differing_from_original'] = slot_diff
                new[f'{fam}{code}'] = res
                del cn
            del cr
        for arm in ORIG:
            assert comp_sha(base[arm], types, ALLK, 0) == hbase[arm], ('pre-t1 source cache modified', arm, d)
        out[d] = {'fF': fF, 'orig': res_o, 'new': new}
        del base, c1
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    gates['replay'] = 'original endpoints: t1 logits/cache == QKF/QKD, natural trajectories == reference, C t2 M and bf16 logits == QKD'
    gates['noop'] = 'custom update with kE = kW = native k reproduces the native t1 logits and every cache tensor (V and F)'
    gates['full_node'] = 'cell 11 == original kernel fed the shadow k (t1 logits and every cache tensor)'
    gates['bridge'] = 'cell 11 == original edited arm at t1: logits and every cache tensor except G conv k channels at old-slot positions 0..2'
    gates['oracle'] = f'cells 10/01: FP32 S and o vs FP64 three-term formula, max relative error {oracle_max:.3g} <= {ORACLE_TOL}'
    gates['hooks'] = 'conv and kernel hooks fire once per G layer at t1 only; module functions restored; shadow buffer never written back'
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'signed_zero_exceptions': nz_total, 'oracle_max': oracle_max, 'kernel_identity': kernel_identity(), 'calibration': calib,
            'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, KRD_DIR / 'krd_run.py', KRD_DIR / 'freeze-r02.json',
         KRD_DIR / 'analysis/krd-readouts-r02.json', KHC_DIR / 'freeze-r01.json', QSR_DIR / 'qsr_run.py', QKD_DIR / 'qkd_run.py', QKDR.RPOST_C_MANIFEST,
         QKD_DIR / 'freeze-r02.json', QKF_DIR / 'qkf_run.py', QKFR.RPOST_MANIFEST, QCO_DIR / 'qco_run.py', QKFR.QCO_MANIFEST, QST_DIR / 'qst_core.py',
         SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    """Conservative formal estimate from the preflight worker: mean per-text seconds (preflight texts also run the engineering
    forwards) x 48 + per-worker model load x 2; bytes = preflight bytes / 2 x 48."""
    ws = [w for w in sorted(Path(pre_root).glob('worker-*')) if w.is_dir()]
    assert len(ws) == 1
    r = exp.read(ws[0] / 'receipt.json')
    secs = [exp.read(ws[0] / rel)['seconds'] for rel in r['record_hashes']]
    load = r['wall_seconds'] - sum(secs)
    n = len(items())
    fb = 0
    return {'per_text_seconds': sum(secs) / len(secs), 'load_seconds': load, 'device_seconds': sum(secs) / len(secs) * n + 2 * load,
            'bytes': (r['bytes'] - fb) / len(secs) * n, 'texts': n}


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
    vecs = load_vectors()
    refs = {'qkf': qkf_traj(), 'qco': QKFR.qco_traj(), 'qkd': qkd_records(), 'krd': krd_records()}
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
    lock = open(f'/tmp/acupuncture-kuc-worker{worker}.lock', 'w')
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
        assert set(rec['directions']) == set(DIRECTIONS)
        for d, x in rec['directions'].items():
            assert set(x['orig']) == set(ORIG) and set(x['new']) == {f'{fam}{c}' for fam in FAMILIES for c in CELLS}
        for g in ('replay', 'noop', 'full_node', 'bridge', 'oracle', 'hooks', 'calibration'):
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
            cmd = [sys.executable, '-u', str(HERE / 'kuc_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
