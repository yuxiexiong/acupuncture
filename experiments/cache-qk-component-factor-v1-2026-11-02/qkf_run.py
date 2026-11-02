"""QKF-01: q/k components of the validated common offset (plan docs/cache-qk-component-factor-plan-v1-2026-11-02.zh-CN.md; CONTRACT r01).
Per input i, direction d in {N4146, N1210, R0} (receiver T(i,d), G conv V from C(i), S/KV/shallow from T): V, F and
R_{u,h} (q/k = Q_T - m_h u), A_{u,h} (q/k = Q_C + m_h u) for u in {mu, pre, post}, h in {q, k, qk}; plus C and T_nat.
mu, r_pre: frozen QCO offsets; r_post: r_pre scaled per layer x component x head so that the first-read old-slot conv
contribution matches mu (qkf_rpost.py, frozen before any new output).  Edits only q/k slots [1,4).  A read-only observer saves the
first read-out in_proj_qkv q/k output (x_now) of the 14 G layers.
python qkf_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
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
QCO_DIR = HERE.parent / 'cache-common-offset-v1-2026-11-02'
sys.path.insert(0, str(QCO_DIR))
sys.path.insert(0, str(HERE))
import qco_run as QCOR  # noqa: E402  (frozen QCO-01 runner: form_text, edit_block, check_edit, offsets, QST chain)

QSTR, QCDR, QCR, NQR, SVQ, NRR = QCOR.QSTR, QCOR.QCDR, QCOR.QCR, QCOR.NQR, QCOR.SVQ, QCOR.NRR
FC_DIR, SP_DIR, SVQ_DIR, NQ_DIR, QC_DIR, QCD_DIR, QST_DIR = QCOR.FC_DIR, QCOR.SP_DIR, QCOR.SVQ_DIR, QCOR.NQ_DIR, QCOR.QC_DIR, QCOR.QCD_DIR, QCOR.QST_DIR
B3R, V, P, PK, X = QCOR.B3R, QCOR.V, QCOR.P, QCOR.PK, QCOR.X
CF, CFK, LR, B = QCOR.CF, QCOR.CFK, QCOR.LR, QCOR.B
F, L, T1, exp, K = QCOR.F, QCOR.L, QCOR.T1, QCOR.exp, QCOR.K

PLAN_ID = 'QKF-01-QK-COMPONENT-FACTOR-v1'
PLAN_DOCS = [REPO / 'docs/cache-qk-component-factor-plan-v1-2026-11-02.zh-CN.md', REPO / 'docs/cache-qkf-self-check-v1-2026-11-02.zh-CN.md']
DESIGN = QCOR.DESIGN
QC_INPUTS, QC_TOKENS = QCOR.QC_INPUTS, QCOR.QC_TOKENS
QCD_G, QST_FORMAL, QCO_FORMAL = QCOR.QCD_G, QCOR.QST_FORMAL, QCO_DIR / 'runs/formal-r01'
QCO_OFFSETS_PT, QCO_MANIFEST = QCOR.OFFSETS_PT, QCOR.OFFSETS_MANIFEST
RPOST_PT = HERE / 'runs/rpost-r01/rpost.pt'
RPOST_MANIFEST = HERE / 'analysis/rpost-manifest-r01.json'
QC_FORMAL, NQ_FORMAL, SVQ_FORMAL, SP_FORMAL, NR_FORMAL, B3_FORMAL, XC_FORMAL, SK_FORMAL = QCOR.QC_FORMAL, QCOR.NQ_FORMAL, QCOR.SVQ_FORMAL, QCOR.SP_FORMAL, QCOR.NR_FORMAL, QCOR.B3_FORMAL, QCOR.XC_FORMAL, QCOR.SK_FORMAL
SPLIT = 13
DIRECTIONS = ('N_L00_C4146_D-1', 'N_L00_C1210_D-1', 'R0_L00_D-1')
PREFLIGHT_ITEMS = ('NA-NQ01-ABC-A', 'NA-NQ02-ABC-B')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
STOP = QCOR.STOP
LIMITS = {'preflight': {'formations': 8, 'trajectories': 140, 'decode_forwards': 4480, 'diagnostics': 140, 'calibrations': 0},
          'formal': {'formations': 192, 'trajectories': 3072, 'decode_forwards': 98304, 'diagnostics': 3072, 'calibrations': 0}}
GPU_CAP_S = {'preflight': 0.25 * 3600, 'formal': 1.5 * 3600}
STORAGE_LIMIT = 12 * 2 ** 30
QK, HALF = QCOR.QK, 2048
EDIT_SLOTS = QCOR.EDIT_SLOTS
PRE_TOL = 0.05
POST_TOL = 0.06          # per head (DECISIONS D3: exact CPU simulation of the BF16 write before any output; worst 5.03%)
VECS, MASKS = ('mu', 'pre', 'post'), ('q', 'k', 'qk')
SCI_ARMS = ('V', 'F') + tuple(f'{s}_{u}_{h}' for s in ('R', 'A') for u in VECS for h in MASKS)
QCO_REF = {'V': 'V', 'F': 'F', 'R_mu_qk': 'R', 'A_mu_qk': 'A', 'R_pre_qk': 'R_rand', 'A_pre_qk': 'A_rand'}
OFF_DIR = 'N_L00_C4146_D-1'
ALLK = ('recurrent', 'kv', 'conv')
COUNT_KEYS = ('formations', 'trajectories', 'decode_forwards', 'diagnostics', 'prefix_prefills', 'formation_token_forwards')
comp_sha = NRR.comp_sha
shared_tokens, generate = QCOR.shared_tokens, QCOR.generate


def conditions():
    c = QCOR.conditions()
    return {d: c[d] for d in DIRECTIONS}


def items():
    return QCOR.items()


plan = QCOR.plan


def mask_vec(u, h):
    """u: [14, 4096, 3]; keep the q half [0, 2048), the k half [2048, 4096) or both."""
    v = u.clone()
    if h == 'q':
        v[:, HALF:, :] = 0
    elif h == 'k':
        v[:, :HALF, :] = 0
    return v


def load_vectors():
    import torch
    man = exp.read(QCO_MANIFEST)
    assert exp.sha(QCO_OFFSETS_PT) == man['offsets_sha256'], 'QCO offsets != manifest'
    rp = exp.read(RPOST_MANIFEST)
    assert rp['status'] == 'passed' and exp.sha(RPOST_PT) == rp['rpost_sha256'], 'r_post != manifest'
    off, post = torch.load(QCO_OFFSETS_PT), torch.load(RPOST_PT)
    return {'mu': off['mu'], 'pre': off['r'], 'post': post['r_post']}


def qco_traj():
    out = {}
    for w in sorted(QCO_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        for rel, dg in r['record_hashes'].items():
            assert exp.sha(w / rel) == dg, 'QCO record hash'
            rec = exp.read(w / rel)
            out[rec['text']] = rec['trajectories']
    return out


def edited_arm(recv, qk_base, v_src, G, vec, sign):
    """As QCOR.edited_arm, also returning the actually written change [14, 4096, 3] (float32, CPU)."""
    import torch
    c = copy.deepcopy(recv)
    deltas = []
    for j, l in enumerate(G):
        fq, fv = L._get(qk_base.layers[l], 'conv_states'), L._get(v_src.layers[l], 'conv_states')
        q = fq[:, :QK].clone()
        if vec is not None:
            q2, _ = QCOR.edit_block(q, vec[j], sign)
            deltas.append((q2[0, :, EDIT_SLOTS].float() - q[0, :, EDIT_SLOTS].float()).to('cpu'))
            q = q2
        else:
            deltas.append(torch.zeros(QK, 3))
        L._set(c.layers[l], 'conv_states', torch.cat([q, fv[:, QK:]], dim=1).contiguous())
    return c, torch.stack(deltas)


def head_contrib(delta, Wc):
    """Old-slot first-read conv contribution per head: delta [14, 4096, 3], Wc [14, 4096, 3] -> [14, 2, 16] norms."""
    y = (Wc * delta.double()).sum(-1)
    return y.reshape(14, 2, 16, 128).norm(dim=-1)


def run_item(engine, unit, contexts, calib, conds, qctok, output, stage, vecs=None, qco=None):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
    layers = L.model_layers(model)
    Wc = torch.stack([layers[l].linear_attn.conv1d.weight[:QK, 0, :3].detach().double().cpu() for l in G])
    a = unit['item_id']
    counts = {k: 0 for k in COUNT_KEYS}
    traj, tensors, gates, checks = {}, {}, {}, {}
    C, T, info = QCOR.form_text(engine, a, contexts, calib, conds, qctok, counts)
    hC = comp_sha(C, types, ALLK, 0)
    hT = {d: comp_sha(T[d], types, ALLK, 0) for d in conds}
    old = qco[a]

    def run(name, cache):
        F.assert_no_hooks(model)
        cap, handles = {}, []
        for j, l in enumerate(G):
            def hook(_m, _i, out, j=j):
                if j not in cap:
                    cap[j] = out[0, -1, :QK].detach().to('cpu').clone()
            handles.append(layers[l].linear_attn.in_proj_qkv.register_forward_hook(hook))
        try:
            r, lg = generate(engine, cache, info['last'], info['n'], info['q_shared'], info['watch'], types, counts)
        finally:
            for h in handles:
                h.remove()
        F.assert_no_hooks(model)
        assert len(cap) == len(G), ('observer missed a layer', name)
        counts['trajectories'] += 1
        r['text'] = tok.decode(r['ids'], skip_special_tokens=False)
        traj[name] = r
        tensors[name] = {**lg, 'xnow': torch.stack([cap[j] for j in range(len(G))])}
        if r['ids'][0] == info['q_shared'] and len(r['ids']) > 1:
            assert r['diag']['watch'] == r['first']['step2'] and r['diag']['logits_sha256'] == r['first']['step2_logits_sha256'], ('diag != step 2', name)
        return r

    def same(name, r, o):
        assert r['ids'] == o['ids'] and r['first']['logits_sha256'] == o['first']['logits_sha256'], ('replay != QCO', name)
        assert r['first']['cache_sha256'] == o['first']['cache_sha256'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('replay cache', name)
        assert r['diag'] == o['diag'], ('replay diag', name)

    same('C', run('C|-', C), old['C|-'])
    for d in conds:
        same(f'T_nat|{d}', run(f'T_nat|{d}', T[d]), old[f'T_nat|{d}'])
        s = info['scenario']
        delta = {}
        for arm in SCI_ARMS:
            if arm in ('V', 'F'):
                qb, vec, sign = (T[d] if arm == 'V' else C), None, 1
            else:
                side, u, h = arm.split('_')
                qb, sign = (T[d], -1) if side == 'R' else (C, 1)
                vec = mask_vec(vecs[u][f'{s}|{d}'].float(), h)
            cc, dl = edited_arm(T[d], qb, C, G, vec, sign)
            QCOR.check_edit(T[d], qb, C, cc, types, G, vec is not None, f'{arm}|{d}')
            delta[arm] = dl
            r = run(f'{arm}|{d}', cc)
            if arm in QCO_REF:
                same(f'{arm}|{d}', r, old[f'{QCO_REF[arm]}|{d}'])
            del cc
        if stage == 'preflight':
            zero = torch.zeros(len(G), QK, 3)
            for arm, qb, ref in (('R_zero', T[d], f'V|{d}'), ('A_zero', C, f'F|{d}')):
                cc, dl = edited_arm(T[d], qb, C, G, zero, -1 if arm == 'R_zero' else 1)
                assert float(dl.abs().sum()) == 0.0, ('zero edit wrote something', arm, d)
                r = run(f'{arm}|{d}', cc)
                o = traj[ref]
                assert r['ids'] == o['ids'] and r['first'] == o['first'] and r['diag'] == o['diag'] and r['final_cache_sha256'] == o['final_cache_sha256'], ('zero no-op differs', arm, d)
                del cc
            gates['noop'] = 'zero edits write nothing and reproduce V/F trajectories, diagnostics and caches exactly'
        ck = {}
        for side in ('R', 'A'):
            for h in MASKS:
                dm, dp, dq = delta[f'{side}_mu_{h}'], delta[f'{side}_pre_{h}'], delta[f'{side}_post_{h}']
                nm, npre = float(dm.double().norm()), float(dp.double().norm())
                pre_ok = (nm == npre == 0.0) or abs(nm - npre) / max(nm, npre) <= PRE_TOL
                hm, hp = head_contrib(dm, Wc), head_contrib(dq, Wc)
                rel = torch.where(torch.maximum(hm, hp) > 0, (hm - hp).abs() / torch.maximum(hm, hp), torch.zeros_like(hm))
                comps = [0, 1] if h == 'qk' else ([0] if h == 'q' else [1])
                relc = rel[:, comps, :]
                post_ok = bool((relc <= POST_TOL).all())
                ck[f'{side}_{h}'] = {'pre_total_norm_mu': nm, 'pre_total_norm_rpre': npre, 'pre_ok': pre_ok,
                                     'post_head_rel_max': float(relc.max()), 'post_heads_over_tol': int((relc > POST_TOL).sum()), 'post_ok': post_ok}
        checks[d] = ck
    gates['replay_qco'] = 'C, T_nat, V, F, R_mu_qk, A_mu_qk, R_pre_qk, A_pre_qk == QCO formal (ids, first-step and cache hashes, diagnostics)'
    gates['sources'] = 'every arm: V block == C(a), q/k slot 0 == base, S/KV/shallow == T(a,d); unedited q/k == base'
    gates['observer'] = 'read-only in_proj_qkv hook captured the first read-out q/k output (x_now) for all 14 G layers; replays prove it is read-only'
    assert comp_sha(C, types, ALLK, 0) == hC and all(comp_sha(T[d], types, ALLK, 0) == hT[d] for d in conds), 'donor modified'
    assert comp_sha(info['base'], types, ALLK, 0) == info['g']['hashes']['base_b'], 'base modified'
    F.assert_no_hooks(model)
    gates['calibration'] = 'NQ-01 saved scenario calibration (source hash in receipt)'
    body = {'text': a, 'scenario': info['scenario'], 'item': info['item'], 'code_tokens': info['code_tokens'], 'q_shared': info['q_shared'],
            'hashes': {'C': hC, **{f'T|{d}': hT[d] for d in conds}}, 'edit_checks': checks, 'calibration': calib, 'trajectories': traj,
            'counts': counts, 'gates': gates}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', DESIGN, QC_INPUTS, QC_TOKENS, QCO_DIR / 'qco_run.py', QCO_DIR / 'qco_core.py', QCO_DIR / 'qco_offsets.py', QCO_MANIFEST, QST_DIR / 'qst_run.py', QST_DIR / 'qst_core.py', QCD_DIR / 'qcd_run.py', QC_DIR / 'qc_run.py', NQ_DIR / 'nq_run.py', SVQ_DIR / 'svq_run.py', FC_DIR / 'fc_core.py'] + PLAN_DOCS
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
    return own + b3 + xc + sk + nr + sp + svq + nq + qcd + qst + qco + [p for p in B3R.frozen_paths() if p not in own]


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
    man = exp.read(RPOST_MANIFEST)
    assert man['status'] == 'passed' and man['freeze_sha256'] == auth['freeze_sha256'] and exp.sha(RPOST_PT) == man['rpost_sha256']
    assert auth['required_evidence'].get('analysis/rpost-manifest-r01.json') == exp.sha(RPOST_MANIFEST)
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
    vecs = load_vectors()
    qco = qco_traj()
    for u in units:
        started = time.monotonic()
        rid = f"{u['base_id']}-ABC-A"
        if rid not in calib:
            calib[rid], csha = QCR.nq_calibration(rid)
            receipt.setdefault('calibration_sources', {})[rid] = csha
        body, tensors = run_item(engine, u, contexts, calib[rid], conds, qctok, output, stage, vecs=vecs, qco=qco)
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
    lock = open(f'/tmp/acupuncture-qkf-worker{worker}.lock', 'w')
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
        arms = SCI_ARMS + (('R_zero', 'A_zero') if r['stage'] == 'preflight' else ())
        want = {'C|-'} | {f'{x}|{d}' for d in DIRECTIONS for x in ('T_nat',) + arms}
        assert set(rec['trajectories']) == want, set(rec['trajectories']) ^ want
        for g in ('replay_qco', 'sources', 'observer', 'calibration') + (('noop',) if r['stage'] == 'preflight' else ()):
            assert rec['gates'][g], g
        assert set(rec['edit_checks']) == set(DIRECTIONS)
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
            cmd = [sys.executable, '-u', str(HERE / 'qkf_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
