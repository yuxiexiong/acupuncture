"""NMT-01: does the per-layer-per-head magnitude distribution of the SIT state increment reproduce its source effect in a fixed
receiver? (plan docs/cache-increment-norm-match-v2-2026-11-03/PLAN.zh-CN.md; CONTRACT r01).  LVK new panel (48 seen inputs), 4 directions.
Per input x direction: the 8 NVB cells at t1 (frozen NVB NHook + read-only write-key recorder; t1 and C-route t2 bit-equal to NVB formal),
the 4 SIT cross cells rebuilt with the frozen SIT transplant (C-route t2 bit-equal to SIT formal), then after t1 and before t2, in all 14
G layers, receiver B(r,0,b) gets S(r,0,b) + X with
  UP (r=0,1): dS(0,b) n1/n0     DN (r=0,1): dS(1,b) n0/n1     [layer 13 copied directly]
  UPG (r=0, C only): dS(0,b) N1(b)/N0(b)      RND_j (r=0, C only, j<5): n1 k_hat_b rho_j^T
FP64 sum, one cast to float32; nothing else changed; t2 onward no hook.  C route: frozen fF, margin M; N route (UP/DN only): receiver's own
t1 token, greedy, at most 32 tokens.  python nmt_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
SIT_DIR = HERE.parent / 'cache-state-increment-transfer-v1-2026-11-03'
sys.path.insert(0, str(SIT_DIR))
sys.path.insert(0, str(HERE))
import sit_run as SITR  # noqa: E402  (frozen SIT-01 runner, freeze r01)
import nmt_core as NC  # noqa: E402

NVBR = SITR.NVBR
LVKR, SRUR, KRDR, QKFR, QCDR, QCR = NVBR.LVKR, NVBR.SRUR, NVBR.KRDR, NVBR.QKFR, NVBR.QCDR, NVBR.QCR
B, CFK, F, L, T1, exp = NVBR.B, NVBR.CFK, NVBR.F, NVBR.L, NVBR.T1, NVBR.exp
SIT_FORMAL, NBR_DIR = SIT_DIR / 'runs/formal-r01', HERE.parent / 'cache-native-bridge-record-v1-2026-11-03'

PLAN_ID = 'NMT-01-INCREMENT-NORM-MATCH-v2'
PLAN_DOCS = [REPO / 'docs/cache-increment-norm-match-v2-2026-11-03' / f'{n}.zh-CN.md' for n in ('PLAN', 'SELF_CHECK')]
STOP, DIRECTIONS, G14, MAIN, ARMS_ALL, MAX_NEW = NVBR.STOP, NVBR.DIRECTIONS, NVBR.G14, NVBR.MAIN, NVBR.ARMS_ALL, NVBR.MAX_NEW
SIT_CELLS = SITR.NEW_CELLS                                   # '010','011','100','101'  (r s b)
K_RND = 5
MAIN_NEW = tuple(f'{a}|{r}|{b}' for a in ('UP', 'DN') for r in '01' for b in '01')
SEC_NEW = tuple(f'UPG|0|{b}' for b in '01') + tuple(f'RND{j}|0|{b}' for j in range(K_RND) for b in '01')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEMS = NVBR.PREFLIGHT_ITEMS
TOL = 1e-6
RANK1_TOL = 1e-4
COUNT_KEYS = ('formations', 'prefix_prefills', 'formation_token_forwards', 't1', 'c_t2', 'sit_c_t2', 'new_c_t2', 'n_steps',
              'trajectories', 'decode_forwards', 'shadow')


def _limits(n_in, tokens):
    per = {'t1': 8 * 4, 'c_t2': 8 * 4, 'sit_c_t2': 4 * 4, 'new_c_t2': (len(MAIN_NEW) + len(SEC_NEW)) * 4, 'trajectories': len(MAIN_NEW) * 4}
    lim = {k: v * n_in for k, v in per.items()}
    lim['n_steps'] = lim['trajectories'] * (MAX_NEW - 1)
    lim['decode_forwards'] = lim['t1'] + lim['c_t2'] + lim['sit_c_t2'] + lim['new_c_t2'] + lim['n_steps']
    lim['shadow'] = 10 * len(G14) * 4 * n_in
    lim.update({'formations': 5 * n_in, 'prefix_prefills': n_in, 'formation_token_forwards': tokens, 'calibrations': 0})
    return lim


LIMITS = {'preflight': _limits(2, 270), 'formal': _limits(48, 6390)}
GPU_CAP_S = {'preflight': 0.12 * 3600, 'formal': 1.2 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
comp_sha, gdn_module, kernel_identity, load_vectors, conditions, items = NVBR.comp_sha, NVBR.gdn_module, NVBR.kernel_identity, NVBR.load_vectors, NVBR.conditions, NVBR.items
margins, fwd, t1L, form_new, ledger, bit_equal, check_bg, plan = NVBR.margins, NVBR.fwd, NVBR.t1L, NVBR.form_new, NVBR.ledger, NVBR.bit_equal, NVBR.check_bg, NVBR.plan
natural, s_only_equal, first_step = NVBR.natural, NVBR.s_only_equal, NVBR.first_step


def sit_records():
    out = {}
    for w in sorted(SIT_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'SIT record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'SIT tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            rec['_record_sha256'] = dg
            out[rec['text']] = rec
    return out


class KeyHook(NVBR.NHook):
    """Frozen NVB NHook plus a read-only recorder of the unit write key k_hat_b = l2norm(k_b) per G layer (k_b = shadow k1 if b else k0),
    exactly as the frozen custom update normalises it.  Computation unchanged."""

    def __enter__(self):
        super().__enter__()
        inner = self.QM.torch_recurrent_gated_delta_rule
        self.khat = {}
        me = self

        def rec(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer in me.G:
                import torch
                kb = me.sk[me.layer] if me.b else key
                me.khat[me.layer] = me.QM.l2norm(kb.transpose(1, 2).to(torch.float32), dim=-1, eps=1e-6)[:, :, 0].detach().clone()
            return inner(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                         use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
        self.QM.torch_recurrent_gated_delta_rule = rec
        return self


def rho_seed(item, d, layer, j):
    return int.from_bytes(hashlib.sha256(f'NMT-RND|{NC.SEED}|{item}|{d}|{layer}|{j}'.encode()).digest()[:8], 'little') & (2 ** 63 - 1)


def make_rho(item, d, layer, j, H, dv):
    import torch
    gen = torch.Generator(device='cpu').manual_seed(rho_seed(item, d, layer, j))
    z = torch.randn((H, dv), generator=gen, dtype=torch.float64)
    return z / z.norm(dim=-1, keepdim=True)


def build_arms(S, khat0, G, item, d):
    """X[arm_key][layer] (FP64 [1,H,dk,dv]) for arm keys 'UP|b', 'DN|b', 'UPG|b', 'RND{j}|b'; plus engineering stats.
    Raises NC.Unmatchable on the forbidden zero case."""
    import torch
    dS = {(s, b): {l: (S[f'{s}1{b}'][l].double() - S[f'{s}0{b}'][l].double()) for l in G} for s in '01' for b in '01'}
    n = {(s, b): {l: NC.head_norms(dS[(s, b)][l]) for l in G} for s in '01' for b in '01'}
    X, st = {}, {'scale_err': 0.0, 'cos_err': 0.0, 'upg_err': 0.0, 'rnd_err': 0.0, 'rank1': 0.0, 'coef': {}, 'zero_blocks': 0, 'rho_sha': {}}
    for b in '01':
        for arm, src, tgt in (('UP', '0', '1'), ('DN', '1', '0')):
            key = f'{arm}|{b}'
            X[key], coefs = {}, []
            for l in G:
                if l == G[0]:
                    assert torch.equal(dS[('0', b)][l], dS[('1', b)][l]), ('layer-13 increments differ between sources', b)
                    X[key][l] = dS[(src, b)][l].clone()
                    continue
                x, c = NC.scale_blocks(dS[(src, b)][l], n[(src, b)][l], n[(tgt, b)][l])
                X[key][l] = x
                nz = n[(tgt, b)][l] > 0
                st['zero_blocks'] += int((~nz).sum())
                got = NC.head_norms(x)
                if bool(nz.any()):
                    st['scale_err'] = max(st['scale_err'], float(((got[nz] - n[(tgt, b)][l][nz]).abs() / n[(tgt, b)][l][nz]).max()))
                    xs, ss = x.double()[0].flatten(-2)[nz], dS[(src, b)][l].double()[0].flatten(-2)[nz]
                    cos = (xs * ss).sum(-1) / (xs.norm(dim=-1) * ss.norm(dim=-1))
                    st['cos_err'] = max(st['cos_err'], float((1 - cos).abs().max()))
                coefs.append(c)
            cc = torch.cat(coefs)
            st['coef'][key] = {'median': float(cc.median()), 'max': float(cc.max()), 'min': float(cc.min())}
        N0 = float(torch.sqrt(sum((n[('0', b)][l] ** 2).sum() for l in G)))
        N1 = float(torch.sqrt(sum((n[('1', b)][l] ** 2).sum() for l in G)))
        if N0 == 0 and N1 > 0:
            raise NC.Unmatchable('global source norm zero')
        g = 0.0 if N0 == 0 else N1 / N0
        X[f'UPG|{b}'] = {l: dS[('0', b)][l] * g for l in G}
        tot = float(torch.sqrt(sum((NC.head_norms(X[f'UPG|{b}'][l]) ** 2).sum() for l in G)))
        st['upg_err'] = max(st['upg_err'], abs(tot - N1) / N1 if N1 > 0 else tot)
        st['coef'][f'UPG|{b}'] = g
        for l in G:
            st['rank1'] = max(st['rank1'], NC.rank1_residual(dS[('0', b)][l], khat0[b][l]))
        for j in range(K_RND):
            key = f'RND{j}|{b}'
            X[key] = {}
            h = hashlib.sha256()
            for l in G:
                H_, dv = dS[('0', b)][l].shape[1], dS[('0', b)][l].shape[3]
                rho = make_rho(item, d, l, j, H_, dv)
                h.update(rho.numpy().tobytes())
                x = NC.rnd_block(n[('1', b)][l], khat0[b][l], rho)
                X[key][l] = x
                nz = n[('1', b)][l] > 0
                if bool(nz.any()):
                    got = NC.head_norms(x)
                    st['rnd_err'] = max(st['rnd_err'], float(((got[nz] - n[('1', b)][l][nz]).abs() / n[('1', b)][l][nz]).max()))
            st['rho_sha'][key] = h.hexdigest()
    for j in range(K_RND):
        assert st['rho_sha'][f'RND{j}|0'] == st['rho_sha'][f'RND{j}|1'], ('random direction differs between b', j)
    isd = {arm: NC.is_descriptor(X[f'{arm}|0'], X[f'{arm}|1'], dS[(tgt, '0')], dS[(tgt, '1')])
           for arm, tgt in (('UP', '1'), ('DN', '0'), ('UPG', '1'))}
    isd.update({f'RND{j}': NC.is_descriptor(X[f'RND{j}|0'], X[f'RND{j}|1'], dS[('1', '0')], dS[('1', '1')]) for j in range(K_RND)})
    return X, st, isd


def apply_X(base_cache, S, r, b, Xl, G, types):
    """Deep copy of receiver B(r,0,b) with S(r,0,b) + X (FP64 sum, one cast).  Returns (cache, max L2 relative cast error)."""
    import torch
    Y = copy.deepcopy(base_cache)
    err = 0.0
    for l in G:
        cur = L._get(Y.layers[l], 'recurrent_states')
        assert torch.equal(cur, S[f'{r}0{b}'][l]), ('receiver state != recorded S(r,0,b)', l)
        exact = S[f'{r}0{b}'][l].double() + Xl[l]
        new = exact.to(cur.dtype).contiguous()
        en = float(exact.norm())
        e = float((new.double() - exact).norm()) / en if en > 0 else float(new.double().abs().max())
        err = max(err, e)
        L._set(Y.layers[l], 'recurrent_states', new)
    return Y, err


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, NVBR.SPLIT)
    assert tuple(G) == G14
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids), 'stop ids != parser stop set'
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    a_id = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    acc = {'cast': 0.0, 'nz': 0, 'oracle': 0.0, 'dserr': 0.0, 'scale_err': 0.0, 'cos_err': 0.0, 'upg_err': 0.0, 'rnd_err': 0.0, 'rank1': 0.0,
           'zero_blocks': 0}
    led, lv, nv, sv = refs['ledger'][a_id], refs['lvk'][a_id], refs['nvb'][a_id], refs['sit'][a_id]
    nv_t = torch.load(nv['_tensor_path'], map_location='cpu')
    sv_t = torch.load(sv['_tensor_path'], map_location='cpu')
    C, T, info = form_new(engine, led, contexts, calib, conds, counts)
    assert info['hashes'] == lv['formation_hashes'], 'formation hashes != LVK'
    hC, hT = comp_sha(C, types, NVBR.ALLK, 0), {d: comp_sha(T[d], types, NVBR.ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    dec = lambda ids: tok.decode(ids, skip_special_tokens=False)   # noqa: E731
    for d in conds:
        s_ = info['scenario']
        fF = led['tokens']['q_shared']
        assert fF not in STOP
        _, u, sign = ARMS_ALL['Rk']
        vec = QKFR.mask_vec(vecs[u][f'{s_}|{d}'].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        hbT = comp_sha(bT, types, NVBR.ALLK, 0)
        nvd, svd = nv['directions'][d], sv['directions'][d]
        c1, z1, S, old, khat0 = {}, {}, {}, {}, {}
        # ---- 8 NVB cells at t1 (frozen NHook + key recorder), bit-equal to NVB formal
        for cell in MAIN:
            hk = KeyHook(model, G, int(cell[0]), int(cell[1]), int(cell[2]), vec=vec, sign=sign, cconv=cconv)
            c1[cell], z1[cell] = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
            acc['oracle'] = max(acc['oracle'], max(hk.oracle.values()))
            if hk.dserr:
                acc['dserr'] = max(acc['dserr'], max(hk.dserr.values()))
            assert bit_equal(z1[cell].to(torch.bfloat16).cpu(), nv_t[f't1|{cell}|{d}'])[0], ('t1 != NVB formal', cell, d)
            S[cell] = {l: L._get(c1[cell].layers[l], 'recurrent_states').clone() for l in G}
            assert all(S[cell][l].dtype == torch.float32 for l in G), ('recurrent state dtype', cell)
            if cell[0] == '0' and cell[1] == '1':
                khat0[cell[2]] = {l: hk.khat[l] for l in G}
        for c_ in '01':
            for b_ in '01':
                x0, x1 = f'{c_}0{b_}', f'{c_}1{b_}'
                okz, z0 = bit_equal(z1[x0], z1[x1])
                ok, zc0, dl, fail = s_only_equal(c1[x0], c1[x1], types, G)
                assert okz and ok and dl, ('storage-only bridge', x0, x1, d, fail, dl)
                acc['nz'] += z0 + zc0
        for ab in ('00', '01', '10', '11'):
            assert torch.equal(S['0' + ab][G[0]], S['1' + ab][G[0]]), ('layer-13 state depends on c', ab, d)
        hS = {cell: SITR.state_sha(S[cell], G) for cell in MAIN}
        # ---- C route of the 8 old cells, bit-equal to NVB formal
        for cell in MAIN:
            _, zc = fwd(engine, copy.deepcopy(c1[cell]), fF, n, counts, 'c_t2')
            M, Mall = margins(zc, it, code_tok, comp)
            assert bit_equal(zc.to(torch.bfloat16).cpu(), nv_t[f'C|{cell}|{d}'])[0] and M == nvd['cells'][cell]['C']['M'], ('C t2 != NVB', cell, d)
            old[cell] = {'M': M, 'x': int(z1[cell].argmax())}
            assert old[cell]['x'] == nvd['cells'][cell]['x'], ('t1 token != NVB', cell, d)
        # ---- 4 SIT cross cells rebuilt with the frozen SIT transplant, bit-equal to SIT formal
        cross = {}
        for cell in SIT_CELLS:
            r, s, b_ = cell
            X_, e, _ch = SITR.build_transplant(c1[f'{r}0{b_}'], S, r, s, b_, G, types)
            _, zc = fwd(engine, X_, fF, n, counts, 'sit_c_t2')
            M, _ = margins(zc, it, code_tok, comp)
            assert bit_equal(zc.to(torch.bfloat16).cpu(), sv_t[f'C|{cell}|{d}'])[0] and M == svd['new'][cell]['C']['M'], ('C t2 != SIT', cell, d)
            cross[cell] = {'M': M}
        # ---- new arms
        X, st, isd = build_arms(S, khat0, G, a_id, d)
        for k in ('scale_err', 'cos_err', 'upg_err', 'rnd_err', 'rank1'):
            acc[k] = max(acc[k], st[k])
        acc['zero_blocks'] += st['zero_blocks']
        new = {}
        for cell in MAIN_NEW + SEC_NEW:
            arm, r, b_ = cell.split('|')
            Y_, e = apply_X(c1[f'{r}0{b_}'], S, r, b_, X[f'{arm}|{b_}'], G, types)
            acc['cast'] = max(acc['cast'], e)
            ok, zc0, dl, fail = s_only_equal(c1[f'{r}0{b_}'], Y_, types, G)
            assert ok, ('arm changed a non-S cache tensor', cell, d, fail)
            acc['nz'] += zc0
            if arm in ('UP', 'DN'):
                assert torch.equal(L._get(Y_.layers[G[0]], 'recurrent_states'), S[f'{r}1{b_}'][G[0]]), ('layer-13 arm != B(r,1,b)', cell, d)
            hY = comp_sha(Y_, types, NVBR.ALLK, 0)
            _, zc = fwd(engine, copy.deepcopy(Y_), fF, n, counts, 'new_c_t2')
            M, Mall = margins(zc, it, code_tok, comp)
            tensors[f'C|{cell}|{d}'] = zc.to(torch.bfloat16).cpu()
            rec = {'C': {'M': M, 'M_all': Mall, 't2_sha': F.th(zc)}, 'changed_layers': dl}
            if cell in MAIN_NEW:
                x_ = old[f'{r}0{b_}']['x']
                rN, z2 = natural(engine, copy.deepcopy(Y_), x_, n, counts)
                rN['text'] = dec(rN['ids'])
                if z2 is not None:
                    tensors[f'N|{cell}|{d}'] = z2.to(torch.bfloat16)
                rec.update({'N': rN, 'x': x_, 'first': first_step(z1[f'{r}0{b_}'], fF)})
            assert comp_sha(Y_, types, NVBR.ALLK, 0) == hY, ('arm cache modified by C / N copies', cell, d)
            new[cell] = rec
            del Y_
        assert all(SITR.state_sha(S[cell], G) == hS[cell] for cell in MAIN), ('recorded source states modified', d)
        for cell in MAIN:
            assert all(torch.equal(L._get(c1[cell].layers[l], 'recurrent_states'), S[cell][l]) for l in G), ('t1 cache modified', cell, d)
        assert comp_sha(bT, types, NVBR.ALLK, 0) == hbT, ('pre-t1 background cache modified', d)
        out[d] = {'fF': fF, 'old': old, 'cross': cross, 'new': new, 'coef': st['coef'], 'rho_sha': st['rho_sha'], 'IS': isd,
                  'nvb_record_sha256': nv['_record_sha256'], 'sit_record_sha256': sv['_record_sha256']}
        del c1, S, X, bT
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, NVBR.ALLK, 0) and all(comp_sha(T[d], types, NVBR.ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    assert acc['cast'] <= TOL and acc['scale_err'] <= TOL and acc['cos_err'] <= TOL and acc['upg_err'] <= TOL and acc['rnd_err'] <= TOL, acc
    assert acc['rank1'] <= RANK1_TOL and acc['oracle'] <= NVBR.ORACLE_TOL and acc['dserr'] <= NVBR.ORACLE_TOL, acc
    gates['replay'] = 'formation hashes == LVK; 8 NVB cells: t1 bf16 logits, t1 token, C t2 bf16 logits / M == NVB formal'
    gates['sit_bridge'] = '4 SIT cross cells rebuilt with the frozen SIT transplant: C t2 bf16 logits and M == SIT formal'
    gates['storage_layer13'] = 'storage-only bridges; layer-13 state identical for c = 0/1; layer-13 increments identical for both sources'
    gates['scaling'] = (f'UP/DN block norm rel. err max {acc["scale_err"]:.3g}, 1-cos max {acc["cos_err"]:.3g}; UPG total norm {acc["upg_err"]:.3g}; '
                        f'RND norm {acc["rnd_err"]:.3g} (all <= {TOL}); RND rho shared across b; k_hat rank-1 residual {acc["rank1"]:.3g} <= {RANK1_TOL}; '
                        f'zero target blocks {acc["zero_blocks"]}')
    gates['transplant'] = f'only G-layer S differs from the receiver; FP64 sum, one cast, L2 rel. err max {acc["cast"]:.3g} <= {TOL}; layer-13 UP/DN == B(r,1,b)'
    gates['isolation'] = 'source states, t1 caches, pre-t1 background, C / T unchanged; separate deep copies; t2 onward no hook'
    gates['nvb_oracle'] = f'NVB NHook FP64 oracle {acc["oracle"]:.3g}, state identity {acc["dserr"]:.3g} <= {NVBR.ORACLE_TOL}'
    body = {'text': a_id, 'panel': 'new', 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'eng': acc, 'signed_zero_exceptions': acc['nz'], 'kernel_identity': kernel_identity(), 'calibration': calib, 'counts': counts,
            'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers (as SIT-01)

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    own += [HERE / 'readiness/first-order-ref-r01.json']
    sit = [SIT_DIR / 'freeze-r01.json', SIT_DIR / 'DEVIATIONS.zh-CN.md', SIT_DIR / 'analysis/sit-readouts-r01.json', SIT_FORMAL / 'verification.json']
    sit += [w / 'receipt.json' for w in sorted(SIT_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + sit + [p for p in SITR.frozen_paths() if p not in own and p not in sit]


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
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    ki = kernel_identity()
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
    load = r['wall_seconds'] - sum(x['seconds'] for x in recs)
    sec = sum(x['seconds'] for x in recs) / len(recs)
    by = sum((ws[0] / x['tensor_file']).stat().st_size + (ws[0] / rel).stat().st_size for x, rel in zip(recs, r['record_hashes'])) / len(recs)
    return {'per_text_seconds': sec, 'load_seconds': load, 'device_seconds': 48 * sec + 2 * load, 'bytes': 48 * by, 'texts': 48}


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts.get(k, 0) <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    qi = QCDR.qc_items()
    contexts = exp.contexts_for(engine.tokenizer, [qi[t['plan']['qc_broad_id']] for t in items()])
    contexts.update(exp.contexts_for(engine.tokenizer, [v['item'] for v in ledger().values()]))
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    import threading
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    vecs = load_vectors()
    refs = {'lvk': SRUR.lvk_records(), 'ledger': ledger(), 'nvb': SITR.nvb_records(), 'sit': sit_records()}
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
        for u in units:
            started = time.monotonic()
            rid = f"{u['base_id']}-ABC-A"
            if rid not in calib:
                calib[rid], csha = QCR.nq_calibration(rid)
                receipt.setdefault('calibration_sources', {})[rid] = csha
            body, tensors = run_item(engine, u, contexts, calib[rid], conds, None, output, stage, vecs=vecs, refs=refs)
            for k in COUNT_KEYS:
                totals[k] += body['counts'][k]
            check_limits(totals, stage)
            rel_t = f'tensors/{u["key"]}.pt'
            (output / 'tensors').mkdir(exist_ok=True)
            assert not (output / rel_t).exists()
            torch.save(tensors, output / rel_t)
            receipt['tensor_hashes'][rel_t] = exp.sha(output / rel_t)
            body['tensor_file'] = rel_t
            rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': {'id': u['item_id']}, **body,
                   'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            L._store(output, receipt, f'records/{u["key"]}.json', rec)
            exp.write(output / 'receipt.json', receipt)
            assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
            hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
            elapsed = time.monotonic() - gpu['t0']
            assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
    finally:
        hb['stop'] = True
        th.join()
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
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
    lock = open(f'/tmp/acupuncture-nmt-worker{worker}.lock', 'w')
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
        assert exp.sha(path / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']]
        assert set(rec['directions']) == set(DIRECTIONS)
        for dd in rec['directions'].values():
            assert set(dd['old']) == set(MAIN) and set(dd['cross']) == set(SIT_CELLS) and set(dd['new']) == set(MAIN_NEW + SEC_NEW)
        for g in ('replay', 'sit_bridge', 'storage_layer13', 'scaling', 'transplant', 'isolation', 'nvb_oracle'):
            assert rec['gates'][g], g
        e = rec['eng']
        assert e['cast'] <= TOL and e['scale_err'] <= TOL and e['cos_err'] <= TOL and e['upg_err'] <= TOL and e['rnd_err'] <= TOL and e['rank1'] <= RANK1_TOL
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
            cmd = [sys.executable, '-u', str(HERE / 'nmt_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
