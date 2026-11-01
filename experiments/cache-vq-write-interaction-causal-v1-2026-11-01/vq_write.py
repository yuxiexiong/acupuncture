"""CFM-VQ-WRITE-L13-v1 (stage B1): does the layer-13 V x Q write interaction change the output interaction?
(CONTRACT.zh-CN.md r01; plan docs/cache-vq-write-interaction-causal-plan-v1-2026-11-01.zh-CN.md r2.)

Per input and background b in {M_T (entry x_C), N (entry x_T)}: TT base cache (S=T, K=T, F all T = CONV M:TTT / N:TT),
cells R (no patch), DEL (layer-13 core - I13), RAND0/RAND1 (core - per-head norm-matched random). I13 comes from the
CONV-FACTOR formal-r01 layer-13 drivers of the four corners. Preflight adds zero / add-back / recorder-off per background.
No prefix formation; one first-step score per cell.

python vq_write.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
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
CF_DIR = HERE.parent / 'cache-conv-factor-v1-2026-11-01'
sys.path.insert(0, str(CF_DIR))
sys.path.insert(0, str(HERE))
import conv_factor as CF  # noqa: E402  (frozen CONV-FACTOR runner: cache build, Counter, LR/CO/B chain)
import cf_core as CFK  # noqa: E402
import vqw_core as K  # noqa: E402

LR, CO, B = CF.LR, CF.CO, CF.B
F, L, T1, exp = B.F, B.L, B.T1, B.exp

PLAN_ID = 'CFM-VQ-WRITE-L13-v1'
PLAN_DOC = REPO / 'docs/cache-vq-write-interaction-causal-plan-v1-2026-11-01.zh-CN.md'
CF_FORMAL = CF_DIR / 'runs/formal-r01'
LAYER = 13
CELLS = ('R', 'DEL', 'RAND0', 'RAND1')
EXTRA = ('zero', 'addback', 'recorder_off')
BASE = {'M_T': 'M:TTT', 'N': 'N:TT'}
PREFLIGHT_ITEMS = ('VAR03-f0-required', 'VRL04-f0-required')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'prefixes': 0, 'scores': 28, 'templates': 1},
          'formal': {'prefixes': 0, 'scores': 96, 'templates': 2}}
STORAGE_LIMIT = 4 * 2 ** 30


def items():
    return CF.items()


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


# ---------------------------------------------------------------- CONV-FACTOR sources

def cf_assets(item_id):
    """(record, tensors) of CONV-FACTOR formal-r01 for one input, sha-checked against the worker receipt."""
    import torch
    for w in sorted(CF_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel, trel = f'records/{item_id}.json', f'tensors/{item_id}.pt'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel], 'CONV record hash'
            assert exp.sha(w / trel) == r['tensor_hashes'][trel], 'CONV tensor hash'
            return exp.read(w / rel), torch.load(w / trel, map_location='cpu', weights_only=True), w / rel
    raise KeyError(item_id)


def interaction_inputs(old, cft, bg):
    rows = {c: {k: v for k, v in cft['drivers'][cid][LAYER].items() if hasattr(v, 'double')}
            for c, cid in K.BG_CELLS[bg].items()}
    s_t = old['deep']['T'][f'{LAYER}:recurrent_states'][0]
    I, checks = K.i13(rows, s_t)
    return I, checks, rows['TT']['core']


# ---------------------------------------------------------------- one input

def run_item(engine, item, prompt, token_set, old, rec_old, cf_rec, cft, template, a_tok, preflight=False):
    import torch
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, CF.SPLIT)
    assert G == B.G_REAL
    device = next(model.parameters()).device
    last, n = prompt[-1], len(prompt)
    item_id = item['id']
    x_t = old['score_extras']['T_native'][f'{LAYER}:in']
    spec_by = {c['id']: c for c in CF.cells()}
    counts = {'prefixes': 0, 'scores': 0}
    gates, res, logits, deltas, prec, src = {}, {}, {}, {}, {}, {}

    for bg in ('M_T', 'N'):
        I, chk, core_tt = interaction_inputs(old, cft, bg)
        assert chk['g_beta_z_shared'] and chk['qk_depend_only_on_Q'] and chk['v_depends_only_on_V'], ('corner dependence', bg, chk)
        assert chk['product_identity_ok'] and chk['read_interaction_ok'] and chk['core_recon_ok'], ('I13 algebra', bg, chk)
        d = {'DEL': I, 'RAND0': K.random_like(item_id, 0, I), 'RAND1': K.random_like(item_id, 1, I)}
        p = {k: K.precision(core_tt, v) for k, v in d.items()}
        assert all(v['ok'] for v in p.values()), ('patch precision gate', bg, {k: {kk: vv for kk, vv in v.items() if kk != 'new_core'} for k, v in p.items()})
        deltas[bg], prec[bg] = d, p
        src[bg] = {k: v for k, v in chk.items()}
        src[bg]['I13_norm'] = float(I.norm())
    gates['source_algebra'] = ('four-corner layer-13 g/beta/z shared, q/k depend only on Q, v only on V; four-corner I13 == '
                               'product form; read-term interaction ~0; core reconstruction <= 1.05 x BF16 floor; '
                               'patch precision gates (overall <=5%, per-head <=1.05 floor, unresolved energy <=2%) for DEL and both RAND')

    def group(bg):
        spec = spec_by[BASE[bg]]
        rec, cnt, patch = B.Recorder(model, G, CF.SPLIT), CF.Counter(model, G), LR.Patch(model)
        with ExitStack() as st:
            e = st.enter_context(LR.Entry(model, x_t)) if bg == 'N' else None
            st.enter_context(rec)
            st.enter_context(cnt)
            st.enter_context(patch)
            expected = F.hook_counts(model)
            todo = [(c, deltas[bg].get(c), False) for c in CELLS]
            if preflight:
                todo += [('zero', torch.zeros_like(deltas[bg]['DEL']), False), ('addback', deltas[bg]['DEL'], True)]
            for c, dlt, ab in todo:
                key = f'{bg}:{c}'
                cache, _ = CF.build(template, old, spec, types, device)
                patch.set(key, None if dlt is None else dlt.to(device), ab)
                cnt.key = key
                before = e.hits if e else 0
                r, z = B.score(engine, cache, last, n, rec, key, token_set, expected)
                cnt.key = None
                counts['scores'] += 1
                assert cnt.hits.get(key, {}) == {i: 1 for i in G}, ('G kernel hits', key)
                assert cnt.chunk.get(key, 0) == 0, ('chunk kernel', key)
                assert patch.info[key]['hits'] == 1, ('layer-13 patch hits', key)
                if e:
                    assert e.hits - before == 1, ('entry hits', key)
                res[key] = {'score': r, 'readout': CFK.readout(z, a_tok), 'patch': patch.info[key]}
                logits[key] = z
        return rec, cnt, patch

    recs = {bg: group(bg) for bg in ('M_T', 'N')}

    # ---- replay and no-side-effect gates
    for bg in ('M_T', 'N'):
        rec, cnt, patch = recs[bg]
        ref = f'{bg}:R'
        assert res[ref]['score']['logits_sha256'] == cf_rec['cells'][BASE[bg]]['score']['logits_sha256'], ('R replay of CONV', bg)
        for i in G:
            assert LR.rows_equal({k: v.cpu() for k, v in rec.rows[ref][i].items() if hasattr(v, 'cpu')},
                                 cft['drivers'][BASE[bg]][i], CF.DRIVER_FIELDS), ('R drivers vs CONV', bg, i)
        core_ref = rec.rows[ref][LAYER]['core']
        for c in CELLS[1:]:
            key = f'{bg}:{c}'
            pinfo = res[key]['patch']
            assert torch.equal(rec.rows[key][LAYER]['core'], core_ref), ('pre-patch core differs', key)
            assert torch.equal(rec.extra[key][f'{LAYER}:in'], rec.extra[ref][f'{LAYER}:in']), ('layer-13 entry differs', key)
            assert pinfo['s_new_sha256'] == res[ref]['patch']['s_new_sha256'], ('s_new changed', key)
            want = core_ref.clone()
            want[...] = prec[bg][c]['new_core'].to(device=core_ref.device).reshape(core_ref.shape)
            full = want.unsqueeze(0).unsqueeze(0)
            assert pinfo['core_out_sha256'] == F.th(full), ('GPU patched core differs from the CPU-checked core', key)
        if bg == 'N':
            for key in [f'N:{c}' for c in CELLS]:
                assert torch.equal(rec.extra[key][f'{LAYER}:in'].cpu(), x_t), ('N entry', key)
    gates['replay_and_patch'] = ('R logits bitwise == CONV TT (M:TTT / N:TT) with all 14 G-layer drivers; DEL/RAND: one '
                                 'layer-13 patch, pre-patch core / layer-13 entry / s_new == R, GPU patched core sha == '
                                 'the CPU precision-checked core; 14 G kernels once each, chunk never; N entry once per score')
    if preflight:
        for bg in ('M_T', 'N'):
            for c in ('zero', 'addback'):
                key = f'{bg}:{c}'
                assert res[key]['patch']['bitwise_unchanged'], ('core changed', key)
                assert res[key]['score']['logits_sha256'] == res[f'{bg}:R']['score']['logits_sha256'], ('logits changed', key)
        F.assert_no_hooks(model)
        r_off, _ = F.score(engine, CF.build(template, old, spec_by[BASE['M_T']], types, device)[0], last, n, keep_logits=False)
        counts['scores'] += 1
        assert r_off['logits_sha256'] == res['M_T:R']['score']['logits_sha256'], 'M_T recorder-off'
        with LR.Entry(model, x_t) as e2, torch.inference_mode():
            out = L.forward(model, [last], n - 1, copy.deepcopy(CF.build(template, old, spec_by[BASE['N']], types, device)[0]))
        counts['scores'] += 1
        assert e2.hits == 1 and F.th(out.logits[0, -1].float()) == res['N:R']['score']['logits_sha256'], 'N recorder-off'
        res['M_T:recorder_off'] = {'logits_sha256': r_off['logits_sha256']}
        res['N:recorder_off'] = {'logits_sha256': F.th(out.logits[0, -1].float())}
        gates['preflight_inert'] = 'zero patch and FP64 add-back leave core and logits bitwise; recorder-off references bitwise'

    corners = {bg: {c: cf_rec['cells'][cid]['readout'] for c, cid in K.BG_CELLS[bg].items()} for bg in ('M_T', 'N')}
    body = {'a_token': a_tok, 'cells': res, 'corners_from_conv': corners,
            'source_checks': src, 'precision': {bg: {k: {kk: vv for kk, vv in v.items() if kk != 'new_core'} for k, v in p.items()} for bg, p in prec.items()},
            'seeds': {str(j): str(K.seed_of(item_id, j)) for j in (0, 1)}, 'token_set': sorted(token_set), 'counts': counts, 'gates': gates}
    tensors = {'logits': logits, 'deltas': deltas,
               'drivers13': {k: B.to_cpu({f: v for f, v in recs[bg][0].rows[k][LAYER].items() if hasattr(v, 'detach')})
                             for bg in recs for k in recs[bg][0].rows},
               'extras': {k: B.to_cpu(recs[bg][0].extra[k]) for bg in recs for k in recs[bg][0].extra},
               'module_out': {k: B.to_cpu(v) for bg in recs for k, v in recs[bg][1].extra.items()},
               'patch_extra': {k: B.to_cpu(v) for bg in recs for k, v in recs[bg][2].extra.items()}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC]
    cf_run = []
    for w in sorted(CF_FORMAL.glob('worker-*')):
        if w.is_dir():
            cf_run.append(w / 'receipt.json')
    cf_run += [CF_FORMAL / 'verification.json', CF_DIR / 'freeze-r03.json']
    return own + cf_run + [p for p in CF.frozen_paths() if p not in own]


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
    assert auth['cpu_receipt_path'] in auth['required_evidence']
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    if stage == 'formal':
        rel = auth['preflight_verification_path']
        assert rel in auth['required_evidence']
        pre = exp.read(HERE / rel)
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
    return auth


def check_limits(counts, stage):
    lim = LIMITS[stage]
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units):
    from control_engine import encode_text
    seg = exp.read(F.SEGMENTS)['items']
    tok = exp.read(B.TOKENS)
    d = CF.design()
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    totals = {'prefixes': 0, 'scores': 0, 'templates': 0}
    template = None
    for u in units:
        item = rows[u['item_id']]
        prompt = encode_text(engine.tokenizer, contexts[item['id']])
        assert exp.digest(prompt) == seg[item['id']]['prompt_token_sha256']
        rec_old, old = CO.load_old(item['id'])
        cf_rec, cft, cf_rel = cf_assets(item['id'])
        assert rec_old['prompt_token_sha256'] == exp.digest(prompt) == cf_rec['prompt_token_sha256']
        a_tok = d['clean_candidate_ids'][item['id']]
        assert a_tok == cf_rec['a_token']
        if template is None:
            template = LR.make_template(engine, prompt[0])
            totals['templates'] += 1
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, item, prompt, token_set, old, rec_old, cf_rec, cft, template, a_tok, preflight=(stage == 'preflight'))
        del old, cft
        for k in ('prefixes', 'scores'):
            totals[k] += body['counts'][k]
        check_limits(totals, stage)
        tpath = output / f'tensors/{u["key"]}.pt'
        receipt['tensor_hashes'][str(tpath.relative_to(output))] = T1.save_tensors(tpath, tensors)
        del tensors
        rec = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'unit': u, 'item': item,
               'prompt_token_sha256': exp.digest(prompt), 'conv_record': str(cf_rel.relative_to(REPO)), **body,
               'seconds': time.monotonic() - started, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
        L._store(output, receipt, f'records/{u["key"]}.json', rec)
        assert B.dir_bytes(output) <= STORAGE_LIMIT // MAX_WORKERS['formal'], 'storage budget exceeded'
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals}, immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], worker % 2
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-cfm-vqw-worker{worker}.lock', 'w')
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
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units)
        receipt['integrity'] = engine.verify_unchanged()
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
    expected = {f'records/{u["key"]}.json' for u in units}
    assert set(r['record_hashes']) == expected
    assert set(r['tensor_hashes']) == {f'tensors/{u["key"]}.pt' for u in units}
    for rel, digest in list(r['tensor_hashes'].items()) + list(r['record_hashes'].items()):
        assert exp.sha(path / rel) == digest, rel
    want = {f'{bg}:{c}' for bg in BASE for c in CELLS}
    if r['stage'] == 'preflight':
        want |= {f'{bg}:{c}' for bg in BASE for c in EXTRA}
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('source_algebra', 'replay_and_patch'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight':
            assert rec['gates']['preflight_inert']
    check_limits(r['model_calls'], r['stage'])
    assert r['integrity']['hooks_removed'] is True
    assert r['integrity']['target_weight_sha256_after'] == exp.read(path / 'metadata.json')['target_weight_sha256_before']
    assert exp.read(path / 'exit.json')['returncode'] == 0
    if r['stage'] == 'preflight':
        assert exp.read(path / 'preflight.json')['status'] == 'passed'
    return {'status': 'passed', 'stage': r['stage'], 'units': len(expected), 'freeze_sha256': r['freeze_sha256'],
            'wall_seconds': r['wall_seconds'], 'model_calls': r['model_calls'], 'bytes': r['bytes']}


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
            cmd = [sys.executable, '-u', str(HERE / 'vq_write.py'), 'run', '--stage', stage, '--worker', str(w),
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
        calls = {k: sum(x['model_calls'][k] for x in results) for k in ('prefixes', 'scores', 'templates')}
        check_limits(calls, stage)
        assert units == (12 if stage == 'formal' else len(PREFLIGHT_ITEMS)), units
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
