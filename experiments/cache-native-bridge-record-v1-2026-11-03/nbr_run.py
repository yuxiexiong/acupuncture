"""NBR-01: record-only replay of the NVB-01 eight main cells (no new conditions) to measure what the output-branch restoration changes in the
stored state differences and in how they are read at t2 (plan docs/cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md; CONTRACT r01).
Per input x direction x cell: t1 with the frozen NVB NHook (bit-equal to NVB formal t1 logits), t1 inputs recorded; C-route t2 with a read-only
capture (bit-equal to NVB formal C logits); one gradient forward (dM/d kernel output per G layer, total derivative via zero leaves).
Per direction: endpoint state differences and their norms / cosines across backgrounds, local-formula residual, t2 D/E/W per cell, same-q
cross reads, gradients.  python nbr_run.py freeze PATH | run ... | verify WORKER_DIR | launch ..."""
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
NVB_DIR = HERE.parent / 'cache-native-bridge-v1-2026-11-03'
sys.path.insert(0, str(NVB_DIR))
sys.path.insert(0, str(HERE))
import nvb_run as NVBR  # noqa: E402  (frozen NVB-01 runner, freeze r02)
import nbr_core as NB  # noqa: E402

LVKR, SRUR = NVBR.LVKR, NVBR.SRUR
KRDR, QKFR, QCDR, QCR, QKDR = NVBR.KRDR, NVBR.QKFR, NVBR.QCDR, NVBR.QCR, NVBR.QKDR
B, CFK, F, L, T1, exp = NVBR.B, NVBR.CFK, NVBR.F, NVBR.L, NVBR.T1, NVBR.exp
NVB_FORMAL = NVB_DIR / 'runs/formal-r01'

PLAN_ID = 'NBR-01-NATIVE-BRIDGE-RECORD-v1'
PLAN_DOCS = [REPO / 'docs/cache-native-bridge-record-plan-v1-2026-11-03.zh-CN.md']
STOP, DIRECTIONS, G14, MAIN, ARMS_ALL = NVBR.STOP, NVBR.DIRECTIONS, NVBR.G14, NVBR.MAIN, NVBR.ARMS_ALL
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
PREFLIGHT_ITEMS = NVBR.PREFLIGHT_ITEMS
DEW_TOL = 1e-5
GRAD_M_TOL = 0.05
COUNT_KEYS = ('formations', 'prefix_prefills', 'formation_token_forwards', 't1', 'c_t2', 'grad', 'decode_forwards', 'shadow')
ALLK = NVBR.ALLK


def _limits(n_in, tokens):
    per = {'t1': 32, 'c_t2': 32, 'grad': 32}
    lim = {k: v * n_in for k, v in per.items()}
    lim['decode_forwards'] = lim['t1'] + lim['c_t2'] + lim['grad']
    lim['shadow'] = 10 * len(G14) * 4 * n_in
    lim.update({'formations': 5 * n_in, 'prefix_prefills': n_in, 'formation_token_forwards': tokens, 'calibrations': 0})
    return lim


LIMITS = {'preflight': _limits(2, 270), 'formal': _limits(48, 6390)}
GPU_CAP_S = {'preflight': 0.1 * 3600, 'formal': 0.6 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
comp_sha, gdn_module, kernel_identity, load_vectors, conditions, items = NVBR.comp_sha, NVBR.gdn_module, NVBR.kernel_identity, NVBR.load_vectors, NVBR.conditions, NVBR.items
margins, fwd, t1L, form_new, ledger, bit_equal, check_bg, plan = NVBR.margins, NVBR.fwd, NVBR.t1L, NVBR.form_new, NVBR.ledger, NVBR.bit_equal, NVBR.check_bg, NVBR.plan


def nvb_records():
    out = {}
    for w in sorted(NVB_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'NVB record hash'
            rec = exp.read(w / rel)
            assert exp.sha(w / rec['tensor_file']) == r['tensor_hashes'][rec['tensor_file']], 'NVB tensor hash'
            rec['_tensor_path'] = str(w / rec['tensor_file'])
            out[rec['text']] = rec
    return out


class RecHook(NVBR.NHook):
    """NVB NHook plus a recorder of the raw t1 kernel inputs (key, value, beta) per G layer; computation unchanged."""

    def __enter__(self):
        super().__enter__()
        inner = self.QM.torch_recurrent_gated_delta_rule
        self.t1in = {}
        me = self

        def rec(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.layer in me.G:
                me.t1in[me.layer] = (key.detach().clone(), value.detach().clone(), beta.detach().clone())
            return inner(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                         use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
        self.QM.torch_recurrent_gated_delta_rule = rec
        return self


class CapHook:
    """t2 read-only: original kernel; records raw (query, key, value, g, beta) and the output per G layer.  mode 'grad' adds a zero leaf to
    the output of each G layer (values unchanged) so that dM/d(output) is the total derivative."""

    def __init__(self, model, G, mode='cap'):
        assert mode in ('cap', 'grad')
        self.model, self.G, self.mode = model, tuple(G), mode
        self.QM = gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.orig_c = self.QM.causal_conv1d_update
        self.layer, self.handles, self.calls, self.inp, self.out, self.eps = None, [], [], {}, {}, {}

    def __enter__(self):
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig and self.QM.causal_conv1d_update is self.orig_c
        for i, lay in enumerate(L.model_layers(self.model)):
            la = getattr(lay, 'linear_attn', None)
            if la is not None:
                def pre(_m, _a, i=i):
                    self.layer = i
                self.handles.append(la.register_forward_pre_hook(pre))
        me = self

        def kern(query, key, value, g=None, beta=None, initial_state=None, output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            if me.mode == 'grad' and initial_state is not None:
                # the cache later overwrites its state tensor in place; give autograd a private copy (DEVIATIONS D1)
                initial_state = initial_state.detach().clone()
            o, S = me.orig(query, key, value, g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                           use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            if me.layer not in me.G:
                return o, S
            import torch
            assert query.shape[1] == 1 and use_qk_l2norm_in_kernel
            me.calls.append(me.layer)
            if me.mode == 'cap':
                me.inp[me.layer] = tuple(x.detach().clone() for x in (query, key, value, g, beta))
                me.out[me.layer] = o.detach().clone()
                return o, S
            e = torch.zeros_like(o, requires_grad=True)
            me.eps[me.layer] = e
            return o + e, S
        self.QM.torch_recurrent_gated_delta_rule = kern
        if self.mode == 'grad':
            def conv(hidden_states, conv_state, weight, bias=None, activation=None):
                return me.orig_c(hidden_states, conv_state.detach().clone(), weight, bias, activation)
            self.QM.causal_conv1d_update = conv
        return self

    def __exit__(self, *exc):
        self.QM.torch_recurrent_gated_delta_rule = self.orig
        self.QM.causal_conv1d_update = self.orig_c
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self):
        assert sorted(self.calls) == sorted(self.G), ('t2 hook calls', self.calls)


def grad_forward(engine, cache, tok, n, counts, G, types, it, code_tok, comp):
    """Gradient of M w.r.t. each G-layer t2 kernel output (copy of the cache made into ordinary tensors).  Returns (M, z, {l: grad})."""
    import torch
    c = copy.deepcopy(cache)
    for i, _k, f in L.component_tensors(c, types):
        L._set(c.layers[i], f, L._get(c.layers[i], f).clone())
    hk = CapHook(engine.model, G, 'grad')
    with hk:
        with torch.enable_grad():
            out = L.forward(engine.model, [tok], n, c)
            z = out.logits[0, -1].float()
            M = z[code_tok[it['target']]] - z[code_tok[comp]]
            gr = torch.autograd.grad(M, [hk.eps[l] for l in G])
    hk.check()
    assert gdn_module().torch_recurrent_gated_delta_rule is KRDR.QHOOK_ORIG[0] and gdn_module().causal_conv1d_update is hk.orig_c
    F.assert_no_hooks(engine.model)
    counts['decode_forwards'] += 1
    counts['grad'] += 1
    gd = {l: x.detach().float().transpose(1, 2)[:, :, 0].clone() for l, x in zip(G, gr)}      # [1, H, dv]
    assert all(torch.isfinite(x).all() for x in gd.values())
    return float(M.detach()), z.detach(), gd


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, refs=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, NVBR.SPLIT)
    assert tuple(G) == G14
    assert tuple(STOP) == tuple(CFK.STOP) == tuple(engine.stop_ids)
    KRDR.QHOOK_ORIG[0] = gdn_module().torch_recurrent_gated_delta_rule
    l2norm = gdn_module().l2norm
    a_id = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    tensors, gates, out = {}, {}, {}
    acc = {'dew': 0.0, 'gradM': 0.0, 'nz': 0}
    led, lv, nv = refs['ledger'][a_id], refs['lvk'][a_id], refs['nvb'][a_id]
    nv_t = torch.load(nv['_tensor_path'], map_location='cpu')
    C, T, info = form_new(engine, led, contexts, calib, conds, counts)
    assert info['hashes'] == lv['formation_hashes'], 'formation hashes != LVK'
    hC, hT = comp_sha(C, types, ALLK, 0), {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    it, code_tok, n = info['item'], info['code_tokens'], info['n']
    comp = it['first_listed'] if it['target'] != it['first_listed'] else it['listed_codes'][1]
    cconv = {l: L._get(C.layers[l], 'conv_states').clone() for l in G}
    for d in conds:
        s = info['scenario']
        fF = led['tokens']['q_shared']
        _, u, sign = ARMS_ALL['Rk']
        vec = QKFR.mask_vec(vecs[u][f'{s}|{d}'].float(), 'k')
        bT, _ = QKFR.edited_arm(T[d], T[d], T[d], G, None, 1)
        check_bg(bT, T[d], C, types, G, 'T', 'T')
        hbT = comp_sha(bT, types, ALLK, 0)
        S, t1in, rd, cells = {}, {}, {}, {}
        for cell in MAIN:
            hk = RecHook(model, G, int(cell[0]), int(cell[1]), int(cell[2]), vec=vec, sign=sign, cconv=cconv)
            c1, z1 = t1L(engine, copy.deepcopy(bT), info['last'], n, counts, 't1', hk)
            assert bit_equal(z1.to(torch.bfloat16).cpu(), nv_t[f't1|{cell}|{d}'])[0], ('t1 != NVB formal', cell, d)
            S[cell] = {l: L._get(c1.layers[l], 'recurrent_states').clone() for l in G}
            if cell[1] == '1' and cell[2] == '1':
                t1in[cell] = {l: (hk.t1in[l], hk.sk[l], hk.sv[l]) for l in G}
            # C route, read-only capture
            cap = CapHook(model, G, 'cap')
            _, zc = fwd(engine, copy.deepcopy(c1), fF, n, counts, 'c_t2', hook=cap)
            assert bit_equal(zc.to(torch.bfloat16).cpu(), nv_t[f'C|{cell}|{d}'])[0], ('C t2 != NVB formal', cell, d)
            M, Mall = margins(zc, it, code_tok, comp)
            rd[cell] = {}
            for j, l in enumerate(G):
                query, key, value, g, beta = cap.inp[l]
                assert torch.equal(S[cell][l], L._get(c1.layers[l], 'recurrent_states'))
                qn, kn, vv, al, bt, kq = NB.reader(query, key, value, g, beta, l2norm)
                D, E, W = NB.dew(S[cell][l], qn, kn, vv, al, bt, kq)
                o_ru, _, pre, _, _ = SRUR.read_use(query, key, value, g, beta, S[cell][l], S[cell][l], 0, 0, l2norm)
                assert bit_equal(o_ru, cap.out[l])[0], ('replicated read != original t2 output', cell, l, d)
                ref = pre[:, :, 0].double()
                err = float(((D + E + W) - ref).abs().max() / max(1.0, float(ref.abs().max())))
                acc['dew'] = max(acc['dew'], err)
                rd[cell][l] = {'qn': qn, 'al': al, 'D': D, 'E': E, 'W': W, 'o': ref}
            Mg, zg, gd = grad_forward(engine, c1, fF, n, counts, G, types, it, code_tok, comp)
            acc['gradM'] = max(acc['gradM'], abs(Mg - M))
            for k_, arr in (('D', 'D'), ('E', 'E'), ('W', 'W'), ('o', 'o'), ('q', 'qn')):
                tensors[f'{k_}|{cell}|{d}'] = torch.stack([rd[cell][l][arr][0].float().cpu() for l in G])         # [14, H, dv|dk]
            tensors[f'g|{cell}|{d}'] = torch.stack([gd[l][0].cpu() for l in G])
            tensors[f'al|{cell}|{d}'] = torch.stack([rd[cell][l]['al'][0].float().cpu() for l in G])
            cells[cell] = {'M': M, 'M_all': Mall, 'M_grad': Mg, 'grad_logit_maxdiff': float((zg - zc).abs().max())}
            del c1
        # layer 13: the stored state does not depend on c (same inputs) -> bit-equal
        for ab in ('00', '01', '10', '11'):
            assert torch.equal(S['0' + ab][G[0]], S['1' + ab][G[0]]), ('layer-13 state depends on c', ab, d)
        # endpoint state differences, local residuals, same-q cross reads
        st, xr = [], {}
        for l in G:
            Ls = {}
            for c in '01':
                (key, value, beta), k1, v1 = t1in[f'{c}11'][l]
                k0n = l2norm(key.transpose(1, 2).float(), dim=-1, eps=1e-6)[:, :, 0]
                k1n = l2norm(k1.transpose(1, 2).float(), dim=-1, eps=1e-6)[:, :, 0]
                Ls[c] = NB.local_I(beta.transpose(1, 2).float()[:, :, 0], k0n, k1n, value.transpose(1, 2).float()[:, :, 0],
                                   v1.transpose(1, 2).float()[:, :, 0])
            row, dd = NB.state_stats(S, l, Ls['0'], Ls['1'])
            st.append(row.cpu())
            for cs in '01':
                for cq in '01':
                    r0 = rd[f'{cq}00'][l]
                    xr.setdefault(f'XI|{cs}|{cq}', []).append(NB.read(dd[f'I{cs}'], r0['qn'], r0['al'])[0].float().cpu())
                    for b in '01':
                        rb = rd[f'{cq}0{b}'][l]
                        xr.setdefault(f'XA|{cs}|{cq}|{b}', []).append(NB.read(dd[f'Sa{cs}_b{b}'], rb['qn'], rb['al'])[0].float().cpu())
                    for a in '01':
                        ra = rd[f'{cq}{a}0'][l]
                        xr.setdefault(f'XB|{cs}|{cq}|{a}', []).append(NB.read(dd[f'Sb{cs}_a{a}'], ra['qn'], ra['al'])[0].float().cpu())
        tensors[f'state|{d}'] = torch.stack(st)                                                                     # [14, H, F]
        for k_, v_ in xr.items():
            tensors[f'{k_}|{d}'] = torch.stack(v_)
        assert comp_sha(bT, types, ALLK, 0) == hbT
        out[d] = {'fF': fF, 'cells': cells}
        del S, t1in, rd, bT
        torch.cuda.empty_cache()
    assert hC == comp_sha(C, types, ALLK, 0) and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    F.assert_no_hooks(model)
    assert acc['dew'] <= DEW_TOL and acc['gradM'] <= GRAD_M_TOL, acc
    gates['replay'] = 'formation hashes == LVK; 8 cells x t1 bf16 logits and C-route t2 bf16 logits == NVB formal (freeze r02)'
    gates['layer13'] = 'stored layer-13 state identical between c = 0 and c = 1 for every (a, b)'
    gates['dew'] = f'replicated t2 read == original output (bit); D + E + W vs pre-cast FP32 output max {acc["dew"]:.3g} <= {DEW_TOL}'
    gates['grad'] = f'gradient forward |M_grad - M| max {acc["gradM"]:.3g} <= {GRAD_M_TOL}; gradients finite'
    gates['hooks'] = 't1 NVB NHook + input recorder; t2 read-only capture; gradient forward zero leaves; module functions restored'
    body = {'text': a_id, 'panel': 'new', 'scenario': info['scenario'], 'item': it, 'code_tokens': code_tok, 'competitor': comp, 'directions': out,
            'dew_max': acc['dew'], 'gradM_max': acc['gradM'], 'state_fields': list(NB.FIELDS), 'kernel_identity': kernel_identity(),
            'calibration': calib, 'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers (as NVB-01)

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md'] + PLAN_DOCS
    nvb = [NVB_DIR / 'freeze-r02.json', NVB_DIR / 'DEVIATIONS.zh-CN.md', NVB_DIR / 'analysis/nvb-readouts-r01.json', NVB_FORMAL / 'verification.json']
    nvb += [w / 'receipt.json' for w in sorted(NVB_FORMAL.glob('worker-*')) if w.is_dir()]
    return own + nvb + [p for p in NVBR.frozen_paths() if p not in own and p not in nvb]


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
    by = sum((ws[0] / x['tensor_file']).stat().st_size for x in recs) / len(recs)
    return {'per_text_seconds': sec, 'load_seconds': load, 'device_seconds': 48 * sec + 2 * load, 'bytes': 48 * by, 'texts': 48}


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
    import threading
    import torch
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calib = {}
    vecs = load_vectors()
    refs = {'lvk': SRUR.lvk_records(), 'ledger': ledger(), 'nvb': nvb_records()}
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
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-nbr-worker{worker}.lock', 'w')
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
        assert set(rec['directions']) == set(DIRECTIONS) and all(set(v['cells']) == set(MAIN) for v in rec['directions'].values())
        for g in ('replay', 'layer13', 'dew', 'grad', 'hooks'):
            assert rec['gates'][g], g
        assert rec['dew_max'] <= DEW_TOL and rec['gradM_max'] <= GRAD_M_TOL
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
            cmd = [sys.executable, '-u', str(HERE / 'nbr_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
