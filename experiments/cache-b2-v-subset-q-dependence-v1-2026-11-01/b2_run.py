"""CFM-B2: do the frozen V subset H and its complement R change Q's output effect? (CONTRACT.zh-CN.md r01;
plan docs/cache-b2-v-subset-q-dependence-plan-v1-2026-11-01.zh-CN.md, a70b235.)

N background only (decoder-13 entry = archived T_native x_T, S=T, full-attention KV=T). Cells (q, h, r): Q = conv q/k
channels of all 14 G layers from donor q; V heads in H from donor h, in R from donor r. One first-step score per cell,
no prefix formation. Preflight adds two independently rebuilt no-op replays (000, 111) per input.

python b2_run.py freeze PATH | run ... | verify WORKER_DIR | launch ...
"""
import argparse
from contextlib import ExitStack
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
SEL = HERE.parent / 'cache-b2-v-subset-q-dependence-design-v1-2026-11-01/head-selection-r01.json'
FV_RESULTS = HERE.parent / 'cache-fv-local-path-v1-2026-11-01/results-r01.json'
sys.path.insert(0, str(CF_DIR))
sys.path.insert(0, str(HERE))
import conv_factor as CF  # noqa: E402
import cf_core as CFK  # noqa: E402
import b2_core as K  # noqa: E402

LR, CO, B = CF.LR, CF.CO, CF.B
F, L, T1, exp = B.F, B.L, B.T1, B.exp

PLAN_ID = 'CFM-B2-VSUBSET-Q-v1'
PLAN_DOC = REPO / 'docs/cache-b2-v-subset-q-dependence-plan-v1-2026-11-01.zh-CN.md'
CF_FORMAL = CF_DIR / 'runs/formal-r01'
SEL_SHA = '33f066082502858a9242c44db49faef4a18b5e970aab1866b88eabb45fbe4bca'
FV_SHA = '64946511014f8cbe9caa030707e77ce92f708277691e3c517dc3fc09c594ec66'
PREFLIGHT_ITEMS = ('VAR03-f0-required', 'VRL04-f0-required')
NOOP = ('000', '111')
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
LIMITS = {'preflight': {'prefixes': 0, 'scores': 20, 'templates': 1},
          'formal': {'prefixes': 0, 'scores': 96, 'templates': 2}}
STORAGE_LIMIT = 4 * 2 ** 30


def items():
    return CF.items()


def selection():
    assert exp.sha(SEL) == SEL_SHA, 'head selection file changed'
    s = exp.read(SEL)
    assert s['source_sha256'] == FV_SHA and exp.sha(FV_RESULTS) == FV_SHA, 'selection source changed'
    return s['items']


def plan(stage, worker, n_workers):
    rows = items()
    if stage == 'preflight':
        rows = [r for r in rows if r['id'] in PREFLIGHT_ITEMS]
        assert [r['id'] for r in rows] == list(PREFLIGHT_ITEMS)
    bases = list(dict.fromkeys(r['base_id'] for r in rows))
    mine = {b for k, b in enumerate(bases) if k % n_workers == worker}
    return [{'item_id': r['id'], 'base_id': r['base_id'], 'key': r['id']} for r in rows if r['base_id'] in mine]


def cf_assets(item_id):
    import torch
    for w in sorted(CF_FORMAL.glob('worker-*')):
        if not w.is_dir():
            continue
        r = exp.read(w / 'receipt.json')
        rel, trel = f'records/{item_id}.json', f'tensors/{item_id}.pt'
        if rel in r['record_hashes']:
            assert exp.sha(w / rel) == r['record_hashes'][rel] and exp.sha(w / trel) == r['tensor_hashes'][trel], 'CONV hashes'
            return exp.read(w / rel), torch.load(w / trel, map_location='cpu', weights_only=True), w / rel
    raise KeyError(item_id)


def conv_overrides(old, cell, H):
    return {f'{l}:conv_states': K.conv_cell(old['deep']['T'][f'{l}:conv_states'], old['deep']['C'][f'{l}:conv_states'], l, cell, H)
            for l in K.G}


def run_item(engine, item, prompt, token_set, old, cf_rec, cft, template, a_tok, H, preflight=False):
    import torch
    model = engine.model
    types = L.layer_types(model)
    G = B.g_layers(types, CF.SPLIT)
    assert G == K.G
    device = next(model.parameters()).device
    last, n = prompt[-1], len(prompt)
    x_t = old['score_extras']['T_native'][f'{CF.SPLIT}:in']
    counts = {'prefixes': 0, 'scores': 0}
    gates, res, logits = {}, {}, {}
    # static: endpoint cells equal the CONV whole-segment assembly; mixed cells differ from T only in chosen slices
    for cell in K.CELLS:
        ov = conv_overrides(old, cell, H)
        if cell in K.ENDPOINT:
            qd, vd = ('T' if cell[0] == '1' else 'C'), ('T' if cell[1] == '1' else 'C')
            for l in G:
                key = f'{l}:conv_states'
                assert torch.equal(ov[key], CFK.assemble(old['deep'][qd][key], old['deep'][vd][key])), ('endpoint assembly', cell, l)
    gates['static'] = 'endpoint cells equal the CONV q/k|V segment assembly in every G layer; H/R partition of 448 heads'
    jobs = list(K.CELLS) + ([f'{c}r' for c in NOOP] if preflight else [])
    rec, cnt = B.Recorder(model, G, CF.SPLIT), CF.Counter(model, G)
    with ExitStack() as st:
        e = st.enter_context(LR.Entry(model, x_t))
        st.enter_context(rec)
        st.enter_context(cnt)
        expected = F.hook_counts(model)
        for job in jobs:
            cell = job[:3]
            spec = {'id': job, 'S': 'T', 'Q': 'T' if cell[0] == '1' else 'C', 'V': 'T', 'K': 'T'}
            cache, _ = CF.build(template, old, spec, types, device, conv_overrides(old, cell, H))
            cnt.key = job
            before = e.hits
            r, z = B.score(engine, cache, last, n, rec, job, token_set, expected)
            cnt.key = None
            counts['scores'] += 1
            assert cnt.hits.get(job, {}) == {i: 1 for i in G} and cnt.chunk.get(job, 0) == 0, ('kernel hits', job)
            assert e.hits - before == 1, ('entry hits', job)
            assert torch.equal(rec.extra[job][f'{CF.SPLIT}:in'].cpu(), x_t), ('entry', job)
            res[job] = {'score': r, 'readout': CFK.readout(z, a_tok)}
            logits[job] = z
    for cell, cid in K.ENDPOINT.items():
        assert res[cell]['score']['logits_sha256'] == cf_rec['cells'][cid]['score']['logits_sha256'], ('endpoint replay', cell, cid)
        for i in G:
            assert LR.rows_equal({k: v.cpu() for k, v in rec.rows[cell][i].items() if hasattr(v, 'cpu')},
                                 cft['drivers'][cid][i], CF.DRIVER_FIELDS), ('endpoint drivers', cell, i)
    gates['replay'] = '000/100/011/111 logits bitwise == CONV N:CC/N:TC/N:CT/N:TT, all 14 G-layer drivers bitwise'
    l0 = K.G[0]
    for cell in K.CELLS:
        v = rec.rows[cell][l0]['v'].cpu()
        for j in range(K.NV):
            ref = rec.rows[f'{cell[0]}11' if K.donor_of(l0, j, cell, H) == 'T' else f'{cell[0]}00'][l0]['v'].cpu()
            assert torch.equal(v[j], ref[j]), ('per-head V layout at layer 13', cell, j)
    gates['layout'] = 'layer 13 (shared entry): every value head of every cell equals its donor endpoint bitwise'
    gates['kernel'] = 'each score: 14 G recurrent kernels once, chunk never, entry hook once, layer-13 entry == x_T'
    if preflight:
        for c in NOOP:
            assert res[f'{c}r']['score']['logits_sha256'] == res[c]['score']['logits_sha256'], ('no-op replay', c)
        gates['preflight_noop'] = 'independently rebuilt 000 and 111 replays bitwise'
    body = {'a_token': a_tok, 'H': sorted([list(x) for x in H]), 'cells': res, 'counts': counts, 'gates': gates,
            'token_set': sorted(token_set)}
    tensors = {'logits': logits,
               'drivers': {k: B.to_cpu({i: {f: v for f, v in rec.rows[k][i].items() if hasattr(v, 'detach')} for i in G}) for k in rec.rows},
               'extras': {k: B.to_cpu(rec.extra[k]) for k in rec.extra}}
    return body, tensors


# ---------------------------------------------------------------- freeze, authorization, workers

def frozen_paths():
    own = sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py')) + \
        [HERE / 'CONTRACT.zh-CN.md', HERE / 'DECISIONS.zh-CN.md', PLAN_DOC, SEL, FV_RESULTS]
    cf_run = [w / 'receipt.json' for w in sorted(CF_FORMAL.glob('worker-*')) if w.is_dir()] + [CF_FORMAL / 'verification.json']
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
    sel = selection()
    rows = {r['id']: r for r in items()}
    contexts = exp.contexts_for(engine.tokenizer, list(rows.values()))
    receipt['kernel_identity'] = T1.kernel_identity()
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
        H, _ = K.partition(sel[item['id']]['H'])
        a_tok = cf_rec['a_token']
        if template is None:
            template = LR.make_template(engine, prompt[0])
            totals['templates'] += 1
        token_set = list(tok['stop_ids']) + list(tok['items'][item['id']]['nonstop'])
        started = time.monotonic()
        body, tensors = run_item(engine, item, prompt, token_set, old, cf_rec, cft, template, a_tok, H, preflight=(stage == 'preflight'))
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
    lock = open(f'/tmp/acupuncture-cfm-b2-worker{worker}.lock', 'w')
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
    want = set(K.CELLS) | ({f'{c}r' for c in NOOP} if r['stage'] == 'preflight' else set())
    for rel in r['record_hashes']:
        rec = exp.read(path / rel)
        assert set(rec['cells']) == want, set(rec['cells']) ^ want
        for g in ('static', 'replay', 'layout', 'kernel'):
            assert rec['gates'][g], g
        if r['stage'] == 'preflight':
            assert rec['gates']['preflight_noop']
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
            cmd = [sys.executable, '-u', str(HERE / 'b2_run.py'), 'run', '--stage', stage, '--worker', str(w),
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
