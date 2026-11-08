"""NGC-01 frozen implementation. No queue, no auto-launch.

assets: CPU-only provenance/freeze. run: explicit renewed authorization required.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time
import traceback

import ngc_core as K

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
PLAN = REPO / 'docs/cache-native-gain-plan-v1-2026-11-08.zh-CN.md'
LVK = HERE.parent / 'cache-local-v-k-v1-2026-11-03'
REVISION = '851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value, immutable=False):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if immutable:
        with p.open('x') as f:
            f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    else:
        tmp = p.with_suffix(p.suffix+'.tmp')
        tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        tmp.replace(p)


def runtime():
    sys.path.insert(0, str(LVK))
    import lvk_run as V
    sys.path.insert(0, str(V.T1.SOURCE))
    import control_engine  # source identity only; importing does not instantiate a model
    assert V.DIRECTIONS == K.DIRECTIONS and tuple(V.STOP) == (248044, 248046)
    return V, control_engine


def references(V):
    refs, paths = {}, []
    for w in sorted((LVK/'runs/formal-r01').glob('worker-*')):
        if not w.is_dir():
            continue
        receipt = read(w/'receipt.json')
        assert receipt['status'] == 'completed'
        paths.append(w/'receipt.json')
        for rel, digest in receipt['record_hashes'].items():
            if Path(rel).name.startswith('LVK-H-'):
                p = w/rel
                assert sha(p) == digest
                r = read(p)
                assert r['text'] not in refs
                refs[r['text']] = r
                paths.append(p)
    assert set(refs) == set(V.ledger()) and len(refs) == 48
    return refs, paths


def check_manifest(path):
    m = read(path)
    for rel, digest in m['files'].items():
        assert sha(REPO/rel) == digest, ('frozen file changed', rel)
    for p, digest in m['external_sources'].items():
        assert sha(p) == digest, ('environment source changed', p)
    return m


def authorize(path, stage):
    """Must fail BEFORE runtime import/model loading when user has cancelled GPU use."""
    a = read(path)
    if not a.get('gpu_authorized', False):
        raise PermissionError('GPU authorization disabled: user requested GPU Ready only; no queue or model run')
    assert a['experiment'] == HERE.name and stage in a['allowed_stages'] and a['user_instruction']
    assert a['maximum_workers'] == 1 and time.time() < a['expires_unix']
    freeze = HERE/a['freeze_path']
    assert sha(freeze) == a['freeze_sha256']
    check_manifest(freeze)
    cpu = HERE/a['cpu_receipt_path']
    assert sha(cpu) == a['cpu_receipt_sha256'] and read(cpu)['status'] == 'passed'
    assert read(cpu)['upstream_kernel_tested'] and read(cpu)['model_forwards'] == 0
    for name,digest in read(cpu)['source_hashes'].items():
        assert sha(HERE/name) == digest, ('CPU-tested source changed',name)
    prior = [read(HERE/p) for p in a.get('prior_preflight_receipts', [])]
    assert len(prior) <= (1 if stage == 'preflight' else 2)
    spent = sum(r['wall_seconds'] for r in prior)
    if stage == 'formal':
        v = read(HERE/a['preflight_verification_path'])
        assert v['status'] == 'passed' and v['stage'] == 'preflight'
        assert v['freeze_sha256'] == a['freeze_sha256']
        assert v['formal_seconds_estimate'] <= K.CAP_SECONDS['formal']
        assert v['formal_bytes_estimate'] <= 8*2**30
        assert v['receipt_path'] in a['prior_preflight_receipts']
        assert sha(HERE/v['receipt_path']) == v['receipt_sha256']
    assert spent+K.CAP_SECONDS[stage] <= 7200
    return a


class GainHook:
    def __init__(self, V, model, target=None):
        self.V, self.model, self.target = V, model, target
        self.QM = V.gdn_module()
        self.orig = self.QM.torch_recurrent_gated_delta_rule
        self.handles, self.calls, self.records = [], [], {}
        self.layer = None

    def __enter__(self):
        for i, layer in enumerate(self.V.L.model_layers(self.model)):
            m = getattr(layer, 'linear_attn', None)
            if m is not None:
                def pre(_m, _a, i=i):
                    self.layer = i
                self.handles.append(m.register_forward_pre_hook(pre))
        def kernel(query, key, value, g=None, beta=None, initial_state=None,
                   output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            args = dict(g=g, beta=beta, initial_state=initial_state, output_final_state=output_final_state,
                        use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            if self.layer not in K.G:
                return self.orig(query, key, value, **args)
            self.calls.append(self.layer)
            target = None if self.target is None else self.target[K.G.index(self.layer)]
            o, s, r = K.update(self.orig, self.QM.l2norm, query, key, value, target=target, **args)
            self.records[self.layer] = r
            return o, s
        self.QM.torch_recurrent_gated_delta_rule = kernel
        return self

    def __exit__(self, *exc):
        self.QM.torch_recurrent_gated_delta_rule = self.orig
        for h in self.handles:
            h.remove()
        self.handles = []
        return False

    def check(self):
        assert tuple(self.calls) == K.G
        assert self.QM.torch_recurrent_gated_delta_rule is self.orig and not self.handles


def assets(output):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU readiness must hide CUDA'
    V, _ = runtime()
    import torch
    ledger = V.ledger()
    refs, paths = references(V)
    assert sum(5*x['plan']['L'] for x in ledger.values()) == 6390
    assert sum(x['plan']['b']+1 for x in ledger.values()) == 1467
    assert set(K.PRE) <= set(ledger)
    assert 2*sum(5*ledger[i]['plan']['L'] for i in K.PRE) <= 600
    ki = V.kernel_identity()
    assert not any(ki[x] for x in ('fla', 'kernels', 'causal_conv1d'))
    assert V.exp.model_spec()['revision'] == REVISION
    paths += [V.HELDOUT, V.LEDGER, V.T1.SOURCE/'contract.json', PLAN, HERE/'CONTRACT.zh-CN.md']
    # Static explicit freeze: later reports do not change the frozen file set.
    paths += list(HERE.glob('*.py'))
    for w in sorted(V.NQ_FORMAL.glob('worker-*')):
        paths += list((w/'calibrations').glob('*.json'))
    conditions = V.conditions()
    assert tuple(conditions) == K.DIRECTIONS
    for s in sorted({x['plan']['base_id'] for x in ledger.values()}):
        V.QCR.nq_calibration(s+'-ABC-A')
    model_assets = V.exp.model_assets()
    for module in tuple(sys.modules.values()):
        p = getattr(module, '__file__', None)
        if p and Path(p).is_file() and Path(p).resolve().is_relative_to(REPO) and Path(p).suffix == '.py':
            paths.append(Path(p).resolve())
    # Historical freeze supplies data dependencies (including the frozen random vector).
    old = read(LVK/'freeze-r01.json')['files']
    paths += [REPO/p for p in old if not p.startswith('docs/') and not p.endswith('.py')]
    files = {str(p.relative_to(REPO)): sha(p) for p in sorted(set(paths))}
    externals = {str(Path(V.gdn_module().__file__).resolve()): sha(V.gdn_module().__file__)}
    import transformers.cache_utils as cache_utils
    externals[str(Path(cache_utils.__file__).resolve())] = sha(cache_utils.__file__)
    for p, h in files.items():
        if p in old:
            assert h == old[p], ('historical LVK source drift', p)
    assert not torch.cuda.is_initialized()
    value = {'status': 'passed', 'kind': 'CPU assets and source freeze', 'model_forwards': 0,
             'cuda_initialized': False, 'revision': REVISION, 'kernel_identity': ki,
             'model_assets': model_assets, 'files': files, 'external_sources': externals,
             'items': len(ledger), 'reference_records': len(refs),
             'preflight_formation_tokens': 2*sum(5*ledger[i]['plan']['L'] for i in K.PRE),
             'preflight_prefix_tokens': 2*sum(ledger[i]['plan']['b']+1 for i in K.PRE)}
    write(output, value, immutable=True)
    print(json.dumps({'status': 'passed', 'files': len(files), 'model_forwards': 0}))


def run(stage, gpu, authorization, output):
    auth = authorize(authorization, stage)
    assert 0 <= gpu <= 1
    # A run command never queues or shares a busy device implicitly.
    procs = subprocess.check_output(['nvidia-smi',f'--id={gpu}','--query-compute-apps=pid','--format=csv,noheader,nounits'],text=True).strip()
    free = int(subprocess.check_output(['nvidia-smi',f'--id={gpu}','--query-gpu=memory.free','--format=csv,noheader,nounits'],text=True).strip())
    assert not procs and free >= 24576, 'GPU not idle/insufficient memory; no automatic queue'
    V, C = runtime()
    import torch
    output = Path(output).resolve()
    assert output.is_relative_to(HERE/'runs')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    receipt = {'status': 'running', 'stage': stage, 'pid': os.getpid(), 'gpu': gpu,
               'freeze_sha256': auth['freeze_sha256'], 'authorization_sha256': sha(authorization),
               'files': {}, 'counts': {k: 0 for k in V.COUNT_KEYS}, 'completed_items': {}, 'started_unix': time.time()}
    write(output/'authorization.json', auth, immutable=True)
    write(output/'receipt.json', receipt)
    stop = threading.Event()
    def timeout(_signum, _frame):
        raise TimeoutError('NGC device wall-time cap reached')
    signal.signal(signal.SIGALRM, timeout)
    signal.alarm(K.CAP_SECONDS[stage])
    def heartbeat():
        while not stop.wait(60):
            write(output/'heartbeat.json', {'pid': os.getpid(), 'wall_seconds': time.monotonic()-started,
                                          'counts': dict(receipt['counts']), 'items': dict(receipt['completed_items'])})
    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        source = read(V.T1.SOURCE/'contract.json')['source']
        engine = C.ControlEngine(source['model_path'], V.exp.model_spec(), f'cuda:{gpu}')
        V.exp.metadata_check(engine)
        write(output/'metadata.json', engine.metadata, immutable=True)
        receipt['load_seconds'] = time.monotonic()-started
        V.F.hook_baseline(engine.model)
        V.KRDR.QHOOK_ORIG[0] = V.gdn_module().torch_recurrent_gated_delta_rule
        assert tuple(V.B.g_layers(V.L.layer_types(engine.model), V.SPLIT)) == K.G
        assert list(engine.stop_ids) == list(V.STOP)
        ledger = V.ledger()
        ids = list(K.PRE) if stage == 'preflight' else sorted(ledger)
        scenarios = {i: ledger[i]['plan']['base_id'] for i in ids}
        contexts = V.exp.contexts_for(engine.tokenizer, [ledger[i]['item'] for i in ids])
        refs, _ = references(V)
        conds = V.conditions()
        gains, results, phase_seconds = {}, {}, {}
        for phase in ('reference', 'intervention'):
            phase_start = time.monotonic()
            if phase == 'intervention':
                r, means = K.profiles(gains, scenarios)
                profile_file = output/'profiles.pt'
                torch.save({'profiles': r, 'observed_means': means, 'scenarios': scenarios,
                            'reference_gains': gains}, profile_file)
                receipt['files']['profiles.pt'] = sha(profile_file)
                write(output/'profiles-lock.json', {'sha256': sha(profile_file), 'before_intervention': True}, immutable=True)
            for i in ids:
                before = time.monotonic()
                calibration, _ = V.QCR.nq_calibration(scenarios[i]+'-ABC-A')
                counts = {k: 0 for k in V.COUNT_KEYS}
                c, ts, info = V.form_new(engine, ledger[i], contexts, calibration, conds, counts)
                assert info['hashes'] == refs[i]['formation_hashes'], ('formation drift', i)
                tensors, arms = {}, {}
                if phase == 'reference':
                    jobs = [('C', c, None)] + [(d, ts[d], None) for d in K.DIRECTIONS]
                    gains[i] = {}
                else:
                    jobs = []
                    for d in K.DIRECTIONS:
                        for bg, cache, native in (('T', ts[d], gains[i][d]), ('C', c, gains[i]['C'])):
                            p, u = K.targets(native, r[scenarios[i], d], bg)
                            jobs.extend([(f'{bg}-P|{d}', cache, p), (f'{bg}-U|{d}', cache, u)])
                for name, cache, target in jobs:
                    hook = GainHook(V, engine.model, target)
                    c1, z1 = V.fwd(engine, copy.deepcopy(cache), info['last'], info['n']-1, counts, 't1', hook)
                    tensors['internals|'+name] = hook.records
                    if phase == 'reference':
                        gain = torch.stack([hook.records[l]['gain_actual'][0] for l in K.G])
                        gains[i][name] = gain
                        if stage == 'preflight':
                            ih = GainHook(V, engine.model, gain)
                            ci, zi = V.fwd(engine, copy.deepcopy(cache), info['last'], info['n']-1, counts, 'refs', ih)
                            assert V.bit_equal(zi, z1)[0]
                            assert V.cache_equal(ci, c1, V.L.layer_types(engine.model), K.G)[0]
                            del ci, zi
                    comp = info['item']['first_listed'] if info['item']['target'] != info['item']['first_listed'] else info['item']['listed_codes'][1]
                    _, zc = V.fwd(engine, copy.deepcopy(c1), info['q_shared'], info['n'], counts, 'c_t2')
                    m, mall = V.margins(zc, info['item'], info['code_tokens'], comp)
                    x = int(z1.argmax())
                    natural, zn = V.natural(engine, copy.deepcopy(c1), x, info['n'], counts)
                    if x in V.STOP:  # historical helper omits trajectory count on immediate EOS
                        counts['trajectories'] += 1
                    natural['text'] = engine.tokenizer.decode(natural['ids'], skip_special_tokens=False)
                    import qst_core as QK
                    it = info['item']
                    y = int(QK.y_full(natural['text'], natural['termination'], it['target'], it['listed_codes'], it['question']))
                    classification = QK.FK.classify(natural['text'], natural['termination'], it['target'], it['distractors'], it['question'])
                    arms[name] = {'N': natural, 'Y': y, 'classification': classification,
                                  'first': V.first_step(z1, info['q_shared']), 'C': {'M': m, 'M_all': mall}}
                    tensors['t1|'+name], tensors['C_t2|'+name] = z1.cpu(), zc.cpu()
                    if zn is not None:
                        tensors['natural_t2|'+name] = zn
                    if phase == 'reference':
                        old = refs[i]['directions']['C_clean'] if name == 'C' else refs[i]['directions'][name]['arms']['L00']
                        assert natural['ids'] == old['N']['ids'] and m == old['C']['M']
                        assert arms[name]['first'] == old['first'], ('native logits drift', i, name)
                    del c1, z1, zc, zn
                body = {'id': i, 'scenario': scenarios[i], 'item': info['item'], 'phase': phase,
                        'arms': arms, 'formation_hashes': info['hashes'], 'counts': counts,
                        'seconds': time.monotonic()-before}
                pt = output/phase/(i+'.pt')
                pt.parent.mkdir(exist_ok=True)
                torch.save(tensors, pt)
                jp = pt.with_suffix('.json')
                body['tensor_file'] = str(pt.relative_to(output))
                write(jp, body, immutable=True)
                for p in (pt, jp):
                    receipt['files'][str(p.relative_to(output))] = sha(p)
                for k,v in counts.items():
                    receipt['counts'][k] += v
                assert all(receipt['counts'][k] <= v for k,v in K.limits(stage).items())
                receipt['completed_items'][phase] = receipt['completed_items'].get(phase, 0)+1
                write(output/'receipt.json', receipt)
                assert sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) <= 8*2**30
                results.setdefault(i, {}).update(arms)
                del c, ts, jobs, tensors, cache
            phase_seconds[phase] = time.monotonic()-phase_start
        assert receipt['counts']['trajectories'] == 21*len(ids)
        assert receipt['counts']['t1'] == 21*len(ids) and receipt['counts']['c_t2'] == 21*len(ids)
        assert receipt['counts']['formations'] == 10*len(ids)
        receipt['phase_seconds'] = phase_seconds
        receipt['integrity'] = engine.verify_unchanged()
        receipt['peak_memory_bytes'] = int(torch.cuda.max_memory_allocated(gpu))
        check_manifest(HERE/auth['freeze_path'])
        for p,h in receipt['files'].items():
            assert sha(output/p) == h
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        stop.set(); thread.join()
        signal.alarm(0)
        receipt['wall_seconds'] = time.monotonic()-started
        write(output/'receipt.json', receipt)
    verification = {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'],
                    'receipt_path': str((output/'receipt.json').relative_to(HERE)), 'receipt_sha256': sha(output/'receipt.json')}
    if stage == 'preflight':
        # Conservative extrapolation: max per-input time separately by phase, 1.5 margin plus load.
        maxima = {phase: max(read(p)['seconds'] for p in (output/phase).glob('*.json')) for phase in ('reference','intervention')}
        verification['formal_seconds_estimate'] = receipt['load_seconds'] + 1.5*48*sum(maxima.values())
        verification['formal_bytes_estimate'] = 1.5*24*sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
    else:
        prediction = {d: {s: {'observed_log_gain_squared': float(means[s,d].square().sum()),
                              'prediction_error_squared': float((means[s,d]-r[s,d]).square().sum())}
                          for s in sorted(set(scenarios.values()))} for d in K.DIRECTIONS}
        write(output/'analysis.json', analyse(results, scenarios, {i:ledger[i]['item'] for i in ids}, prediction), immutable=True)
    write(output/'verification.json', verification, immutable=True)
    print(json.dumps(verification))


def analyse(results, scenarios, items, prediction):
    out = {'independent_scenarios': len(set(scenarios.values())), 'seen_inputs': len(results),
           'directions': {}, 'gain_prediction': prediction}
    def summarize(ids, arms):
        ans = {}
        for a in arms:
            rs = [results[i][a] for i in ids]
            by = {s: [results[i][a]['Y'] for i in ids if scenarios[i] == s] for s in sorted({scenarios[i] for i in ids})}
            ans[a] = {'n':len(rs), 'correct':sum(x['Y'] for x in rs),
                      'scenario_equal_accuracy':sum(sum(v)/len(v) for v in by.values())/len(by),
                      'first_stop':sum(x['N']['ids'][0] in (248044,248046) for x in rs),
                      'truncated':sum(x['N']['termination'] == 'budget' for x in rs),
                      'classifications': [x['classification'] for x in rs]}
        return ans
    for d in K.DIRECTIONS:
        pairs = {'recovery': (f'T-P|{d}', d), 'reverse_damage': ('C',f'C-P|{d}'),
                 'configuration_recovery': (f'T-P|{d}',f'T-U|{d}'),
                 'configuration_reverse': (f'C-U|{d}',f'C-P|{d}')}
        arms = ['C',d]+[f'{bg}-{mode}|{d}' for bg in ('C','T') for mode in ('P','U')]
        one = {'arms': summarize(list(results), arms), 'subgroups': {}}
        for name,(a,b) in pairs.items():
            one[name] = K.difference({i:r[a]['Y'] for i,r in results.items()}, {i:r[b]['Y'] for i,r in results.items()}, scenarios, True)
            ids = [i for i in results if items[i]['target'] != items[i]['first_listed']]
            one[name]['M'] = K.difference({i:results[i][a]['C']['M'] for i in ids}, {i:results[i][b]['C']['M'] for i in ids}, {i:scenarios[i] for i in ids})
            mm = one[name]['M']
            mm['stable_positive'] = mm['scenario_equal_mean'] >= .25 and sum(x > 0 for x in mm['scenario_means'].values()) >= 4
            one[name]['G'] = K.difference({i:results[i][a]['first']['G'] for i in results}, {i:results[i][b]['first']['G'] for i in results}, scenarios)
        for field in ('query','order'):
            for value in sorted({items[i][field] for i in results}):
                one['subgroups'][field+'='+value] = summarize([i for i in results if items[i][field] == value], arms)
        for first in (True,False):
            one['subgroups']['target_first='+str(first)] = summarize([i for i in results if (items[i]['target'] == items[i]['first_listed']) == first],arms)
        out['directions'][d] = one
    out['multi_direction_recovery'] = sum(out['directions'][d]['recovery']['multi_scenario'] for d in K.DIRECTIONS[:3]) >= 2
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='cmd', required=True)
    a = sub.add_parser('assets'); a.add_argument('--output', required=True)
    r = sub.add_parser('run')
    r.add_argument('--stage', choices=list(K.CAP_SECONDS), required=True)
    r.add_argument('--gpu', type=int, required=True)
    r.add_argument('--authorization', required=True); r.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.cmd == 'assets':
        assets(args.output)
    else:
        run(args.stage, args.gpu, args.authorization, args.output)
