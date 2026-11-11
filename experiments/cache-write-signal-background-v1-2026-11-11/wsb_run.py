"""WSB-01 runner. Default authorization is disabled; never queues or advances stages."""
import argparse
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import shutil
import sys
import time
import traceback
from contextlib import contextmanager

import wsb_core as K

HERE, ROOT = K.HERE, K.ROOT
DWB = HERE.parent/'cache-donor-write-bridge-v2-2026-11-07'


def sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(2**20), b''):
            h.update(b)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value, immutable=False):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    if immutable:
        with p.open('x') as f:
            f.write(text)
    else:
        tmp = p.with_suffix(p.suffix+'.tmp')
        tmp.write_text(text)
        tmp.replace(p)


def runtime():
    sys.path.insert(0, str(DWB))
    import dwb_run as V
    assert tuple(V.G14) == K.G and V.MAIN == K.MAIN
    return V


def references():
    base = DWB/'runs/formal-r02/worker-0'
    rc = read(base/'receipt.json')
    assert rc['status'] == 'completed'
    refs, paths = {}, [base/'receipt.json']
    for rel, h in rc['record_hashes'].items():
        p = base/rel
        assert sha(p) == h, p
        paths.append(p)
        if not p.name.startswith('scenario-'):
            r = read(p)
            assert r['text'] not in refs
            refs[r['text']] = r
    assert set(refs) == set(K.panel()[0])
    return refs, paths


def check_files(manifest):
    for rel, h in manifest['files'].items():
        assert sha(ROOT/rel) == h, ('source drift', rel)


def check_model_assets(actual, expected):
    """Identity is invariant; wall_seconds is a measurement, never an identity field."""
    assert actual['status'] == expected['status'] == 'passed'
    assert all(actual[k] == expected[k] for k in ('files', 'manifest_sha256')), 'model asset identity changed'


def assets(output, environment=False):
    """Read-only asset checks, source manifest; environment mode still never loads weights."""
    V = runtime()
    refs, paths = references()
    doc_changes = {}
    for p in (DWB/'freeze-r02.json', K.HERE.parent/'cache-local-v-k-v1-2026-11-03/freeze-r01.json'):
        old = read(p)
        for rel, h in old['files'].items():
            actual = sha(ROOT/rel)
            if rel.startswith('docs/') and actual != h:
                doc_changes[rel] = {'historical': h, 'current': actual}
            else:
                assert actual == h, ('historical executable/data drift', rel)
        paths += [p]+[ROOT/rel for rel in old['files']]
    for entry in read(HERE/'design-audit.json')['sources']:
        assert sha(ROOT/entry['path']) == entry['sha256']
    led = V.LVKR.ledger()
    for s in sorted({v['plan']['base_id'] for v in led.values()}):
        V.QCR.nq_calibration(s+'-ABC-A')
    for module in tuple(sys.modules.values()):
        p = getattr(module, '__file__', None)
        if p and Path(p).suffix == '.py' and Path(p).resolve().is_relative_to(ROOT):
            paths.append(Path(p).resolve())
    paths += list(HERE.glob('*.py'))+[HERE/'PLAN.zh-CN.md', HERE/'SELF_CHECK.zh-CN.md', HERE/'design-audit.json']
    value = dict(status='passed', kind='repository assets only', model_forwards=0,
                 files={str(p.relative_to(ROOT)): sha(p) for p in sorted(set(paths))},
                 bridge_receivers=len(refs), source_bridges=348, baseline_bridges=96,
                 environment_checked=False, revision=K.REVISION, historical_document_changes=doc_changes)
    if environment:
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        import torch
        import transformers
        ki = V.kernel_identity()
        assert not any(ki[k] for k in ('fla', 'kernels', 'causal_conv1d'))
        assert V.exp.model_spec()['revision'] == K.REVISION
        source = read(V.T1.SOURCE/'contract.json')['source']
        assert torch.__version__ == source['torch_version'] and transformers.__version__ == source['transformers_version']
        import transformers.cache_utils as cache_utils
        external = [Path(V.gdn_module().__file__), Path(cache_utils.__file__)]
        value.update(environment_checked=True, kernel_identity=ki, model_assets=V.exp.model_assets(),
                     external_sources={str(p): sha(p) for p in external}, torch_version=torch.__version__,
                     transformers_version=transformers.__version__, cuda_initialized=torch.cuda.is_initialized())
        assert not torch.cuda.is_initialized()
    write(output, value, immutable=True)
    return {'status': 'passed', 'files': len(value['files']), 'environment_checked': environment}


class WriteHook:
    """Reuse frozen LHook's shadow convolution and cleanup; replace only its kernel wrapper."""
    def __init__(self, V, model, *, donor=None, package=None, zero=False):
        assert sum((donor is not None, package is not None, zero)) == 1
        self.V, self.package = V, package
        self.base = V.LVKR.LHook(model, K.G, 'cell', a=int(donor is not None), cconv=donor)
        self.calls, self.records, self.deltas = [], {}, {}
        self.collect = donor is not None

    def __enter__(self):
        self.base.__enter__()
        def kern(query, key, value, g=None, beta=None, initial_state=None,
                 output_final_state=False, use_qk_l2norm_in_kernel=False, **kw):
            b = self.base
            if b.layer not in K.G:
                return b.orig_k(query, key, value, g=g, beta=beta, initial_state=initial_state,
                                output_final_state=output_final_state,
                                use_qk_l2norm_in_kernel=use_qk_l2norm_in_kernel, **kw)
            assert not kw, ('unexpected kernel kwargs', kw)
            assert b.layer not in self.calls
            self.calls.append(b.layer)
            delta = self.package[b.layer] if self.package is not None else None
            out, state, delta, rec = K.update(self.V.LVKR.custom_update, b.QM.l2norm,
                query, key, value, g, beta, initial_state, output_final_state,
                use_qk_l2norm_in_kernel, shadow=b.sv[b.layer] if self.collect else None, delta=delta)
            rec['state_sha256'] = self.V.F.th(state)
            rec['delta_sha256'] = self.V.F.th(delta)
            rec['delta_norm'] = float(delta.norm())
            self.records[b.layer] = rec
            if self.collect:
                self.deltas[b.layer] = delta.detach().cpu()
            return out, state
        self.base.QM.torch_recurrent_gated_delta_rule = kern
        return self

    def __exit__(self, *exc):
        return self.base.__exit__(*exc)

    def check(self):
        assert tuple(self.calls) == tuple(self.base.conv_calls) == K.G
        assert not self.base.handles
        assert self.base.QM.torch_recurrent_gated_delta_rule is self.base.orig_k
        assert self.base.QM.causal_conv1d_update is self.base.orig_c


class Meter:
    """Time every forward and disjoint residual overhead, including file I/O."""
    def __init__(self, V, gpu):
        self.V, self.original = V, V.L.forward
        self.gpu = gpu
        self.phase, self.forward_seconds, self.maxima = None, 0., {}

    def add(self, name, seconds):
        self.maxima[name] = max(self.maxima.get(name, 0.), seconds)

    def __enter__(self):
        def forward(model, tokens, start, cache, *a, **kw):
            t = time.monotonic()
            out = self.original(model, tokens, start, cache, *a, **kw)
            import torch
            torch.cuda.synchronize(self.gpu)
            dt = time.monotonic()-t
            name = self.phase
            if name == 'formation':
                name = 'prefix_token' if cache is None else 'formation_token'
            self.add(name, dt/len(tokens) if name == 'prefix_token' else dt)
            self.forward_seconds += dt
            return out
        self.V.L.forward = forward
        return self

    def __exit__(self, *exc):
        self.V.L.forward = self.original

    @contextmanager
    def overhead(self, name):
        t, f = time.monotonic(), self.forward_seconds
        try:
            yield
        finally:
            self.add(name, max(0., time.monotonic()-t-(self.forward_seconds-f)))


def bridge(new, old):
    assert new['x'] == old['x'] and new['N']['ids'] == old['N']['ids']
    assert new['N']['termination'] == old['N']['termination'], 'old full-answer bridge failed'


def natural_answer(V, engine, cache, z, info):
    import spf_analysis as A
    counts = info['counts']
    x, before = int(z.argmax()), counts['trajectories']
    nr, _ = V.natural(engine, cache, x, info['n'], counts)
    if x in V.STOP:
        counts['trajectories'] += 1
    assert counts['trajectories'] == before+1
    nr['text'] = engine.tokenizer.decode(nr['ids'], skip_special_tokens=False)
    it = info['item']
    return {'x': x, 'N': nr, 'row': A.row_out(nr, it),
            'classification': A.NK.FK.classify(nr['text'], nr['termination'], it['target'], it['distractors'], it['question'])}


def snapshot(V, cache, logits, types):
    """Canonicalize signed zero only; hash every cache tensor and t1 logits."""
    def digest(t):
        assert t.isfinite().all()
        raw = V.F.th(t)
        normalized = t.clone()
        normalized[normalized == 0] = 0
        return {'raw': raw, 'zero_canonical': V.F.th(normalized), 'shape': list(t.shape), 'dtype': str(t.dtype)}
    def meta(obj):
        # Frozen cache management counters/flags live as scalar attributes; tensor fields below.
        return {k: v for k, v in vars(obj).items() if v is None or isinstance(v, (str, bool, int, float))}
    return {'logits': digest(logits), 'management': {'cache': meta(cache), 'layers': [meta(l) for l in cache.layers]},
            'cache': {f'{i}|{field}': digest(V.L._get(cache.layers[i], field))
            for i, _kind, field in V.L.component_tensors(cache, types)}}


def identical(a, b):
    assert set(a['cache']) == set(b['cache'])
    assert a['management'] == b['management'], 'cache management state changed'
    pairs = [(a['logits'], b['logits'])]+[(a['cache'][k], b['cache'][k]) for k in a['cache']]
    assert all(x['zero_canonical'] == y['zero_canonical'] for x, y in pairs), 'exact t1 replay failed'
    assert all((x['shape'], x['dtype']) == (y['shape'], y['dtype']) for x, y in pairs)
    return sum(x['raw'] != y['raw'] for x, y in pairs)


def execute(engine, V, stage, output, receipt, meter):
    setup = time.monotonic()
    import torch
    items, tables = K.panel(stage)
    refs, _ = references()
    led = V.LVKR.ledger()
    contexts = V.exp.contexts_for(engine.tokenizer, [led[i]['item'] for i in items])
    types = V.L.layer_types(engine.model)
    assert tuple(V.B.g_layers(types, V.SPLIT)) == K.G
    assert tuple(engine.stop_ids) == tuple(V.STOP) == (248044, 248046)
    assert V.exp.model_spec()['revision'] == K.REVISION
    for l in K.G:
        m = V.L.model_layers(engine.model)[l].linear_attn
        assert (m.num_v_heads, m.head_k_dim, m.head_v_dim) == (32, 128, 128)
        assert V.V_LO == 2*m.key_dim and V.V_LO+m.value_dim == m.conv1d.weight.shape[0]
    V.KRDR.QHOOK_ORIG[0] = V.gdn_module().torch_recurrent_gated_delta_rule
    V.F.hook_baseline(engine.model)
    counts = receipt['counts']
    answers, delivery = {}, {c: [] for c in K.CELLS}
    meter.add('setup', time.monotonic()-setup)

    def save(rel, body, tensor=False):
        path = output/rel
        path.parent.mkdir(parents=True, exist_ok=True)
        assert not path.exists()
        if tensor:
            torch.save(body, path)
        else:
            write(path, body, immutable=True)
        receipt['files'][rel] = sha(path)
        receipt['bytes'] += path.stat().st_size
        assert receipt['bytes']+receipt['prior_bytes'] <= K.STORAGE
        if stage == 'preflight':
            assert receipt['bytes'] <= K.PREFLIGHT_STORAGE, 'preflight artifact cap exceeded'
        write(output/'receipt.json', receipt)

    def first(cache, info, mode, hook=None):
        meter.phase = mode
        c, z = V.fwd(engine, copy.deepcopy(cache), info['last'], info['n']-1, counts, 't1', hook)
        counts['shadow'] += hook.base.n_shadow if hook else 0
        receipt['arm_counts'][mode] += 1
        return c, z, snapshot(V, c, z, types)

    def finish(c, z, info):
        meter.phase = 'decode'
        return natural_answer(V, engine, c, z, {**info, 'counts': counts})

    for scenario in sorted({x['scenario'] for x in items.values()}):
        ids = [i for i in items if items[i]['scenario'] == scenario]
        C, H, info, hashes = {}, {}, {}, {}
        cal, _ = V.QCR.nq_calibration(scenario+'-ABC-A')
        for i in ids:
            with meter.overhead('formation_overhead'):
                meter.phase = 'formation'
                C[i], ts, info[i] = V.form_new(engine, led[i], contexts, cal, {K.MAIN: V.conditions()[K.MAIN]}, counts)
                assert all(h == refs[i]['formation_hashes'][k] for k, h in info[i]['hashes'].items())
                H[i] = V.SP.compose(ts[K.MAIN], V.TG['OO'], {'oc': C[i]})
                V.SP.check_arm(H[i], ts[K.MAIN], V.TG['OO'], {'oc': C[i]}, types, i)
                hashes[i] = [V.comp_sha(c, types, V.ALLK, 0) for c in (C[i], H[i])]
                del ts
        for r in ids:
            backgrounds = {'C': C[r], 'H': H[r]}
            bases = {}
            with meter.overhead('receiver_overhead'):
                for bg, cache in backgrounds.items():
                    c, z, snap = first(cache, info[r], 'baseline')
                    bases[bg] = {'answer': finish(c, z, info[r]), 'snapshot': snap}
                    old = refs[r]['once']['C0'] if bg == 'C' else refs[r]['directions'][K.MAIN]['OO']
                    bridge(bases[bg]['answer'], old)
                    h = WriteHook(V, engine.model, zero=True)
                    cz, zz, sz = first(cache, info[r], 'zero', h)
                    bases[bg]['zero_signed_zero_tensors'] = identical(snap, sz)
                    del c, z, cz, zz, h
                save(f'records/{r}/bases.json', {'bases': bases, 'formation_hashes': info[r]['hashes']})
            answers[r] = {c: {} for c in K.CELLS}
            for donor in tables[r]:
                d = donor['id']
                with meter.overhead('pair_overhead'):
                    record, source_data = {}, {}
                    donor_conv = {l: V.L._get(C[d].layers[l], 'conv_states') for l in K.G}
                    for source, cache in backgrounds.items():
                        h = WriteHook(V, engine.model, donor=donor_conv)
                        c, z, snap = first(cache, info[r], 'source', h)
                        ans = finish(c, z, info[r])
                        if source == 'H':
                            bridge(ans, refs[r]['directions'][K.MAIN]['DO|'+d])
                        rel = f'packages/{r}/{d}-{source}.pt'
                        save(rel, {'delta': h.deltas, 'local': h.records}, tensor=True)
                        # Both receiving backgrounds reload the same frozen file, never recompute delta.
                        source_data[source] = (rel, snap, ans)
                        record['R_'+source] = {'answer': ans, 'snapshot': snap, 'package': rel}
                        del c, z, h
                    for source, (rel, snap, ans) in source_data.items():
                        package_sha = receipt['files'][rel]
                        for bg, cache in backgrounds.items():
                            assert sha(output/rel) == package_sha
                            package = torch.load(output/rel, map_location='cpu', weights_only=True)
                            h = WriteHook(V, engine.model, package=package['delta'])
                            c, z, replay_snap = first(cache, info[r], 'replay', h)
                            cell = bg+source
                            new = finish(c, z, info[r])
                            check = identical(snap, replay_snap) if bg == source else None
                            if bg == source:
                                bridge(new, ans)
                            assert all(h.records[l]['delta_sha256'] == package['local'][l]['delta_sha256'] for l in K.G)
                            answers[r][cell][d] = new['row']
                            delivery[cell].append(dict(receiver=r, donor=d, donor_type=donor['type'],
                                self_row=items[r]['listed_codes'].index(items[r]['target']), donor_row=donor['row'], **new))
                            record[cell] = {'answer': new, 'snapshot': replay_snap,
                                            'signed_zero_tensors': check, 'package_sha256': package_sha,
                                            'layers': h.records}
                            assert sha(output/rel) == package_sha, 'source file changed'
                            del c, z, h, package
                    deltas = [torch.load(output/source_data[s][0], map_location='cpu', weights_only=True)['delta'] for s in ('C', 'H')]
                    record['delta_geometry_descriptive_only'] = {}
                    for l in K.G:
                        x, y = deltas[0][l], deltas[1][l]
                        nx, ny = float(x.norm()), float(y.norm())
                        record['delta_geometry_descriptive_only'][l] = {'norm_C': nx, 'norm_H': ny,
                            'cosine': float((x*y).sum())/(nx*ny) if nx*ny else None}
                    del deltas, x, y
                    save(f'records/{r}/{d}.json', record)
                    assert receipt['prior_bytes']+sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) <= K.STORAGE
                    if stage == 'preflight':
                        assert sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) <= K.PREFLIGHT_STORAGE
                    check_counts(receipt, stage, complete=False)
        assert all(hashes[i] == [V.comp_sha(c, types, V.ALLK, 0) for c in (C[i], H[i])] for i in ids)
        del C, H, backgrounds, cache, donor_conv
    check_counts(receipt, stage, complete=True)
    save('answers.json', {'rows': answers, 'delivery': delivery})
    return answers


def check_counts(receipt, stage, complete):
    lim = K.limits(stage)
    c = receipt['counts']
    for key, value in c.items():
        assert value <= lim.get(key, 0), (key, value, lim.get(key, 0))
    for k, value in receipt['arm_counts'].items():
        assert value <= lim[k]
        if complete:
            assert value == lim[k]
    if complete:
        for k in ('formations', 'prefix_prefills', 't1', 'trajectories', 'shadow'):
            assert c[k] == lim[k], (k, c[k], lim[k])


def authorize(path, stage):
    a = read(path)
    if a.get('gpu_authorized') is not True:
        raise PermissionError('WSB-01: GPU disabled; implementation/CPU acceptance only')
    assert a['experiment'] == HERE.name and stage in a['allowed_stages'] and a['user_instruction']
    assert a['maximum_workers'] == 1 and time.time() < a['expires_unix']
    manifest = HERE/a['freeze_path']
    assert sha(manifest) == a['freeze_sha256']
    m = read(manifest)
    check_files(m)
    assert m['environment_checked'] and m['revision'] == K.REVISION
    for p, h in m['external_sources'].items():
        assert sha(p) == h
    cpu = HERE/a['cpu_receipt_path']
    assert sha(cpu) == a['cpu_receipt_sha256']
    cr = read(cpu)
    assert cr['status'] == 'passed' and cr['model_forwards'] == 0 and cr['upstream_kernel_tested']
    assert all(sha(HERE/p) == h for p, h in cr['source_hashes'].items())
    assert cr['torch_version'] == m['torch_version'] and cr['external_sources']
    assert all(m['external_sources'].get(p) == h for p, h in cr['external_sources'].items())
    prior = a.get('prior_preflights', {})
    assert len(prior) <= (1 if stage == 'preflight' else 2)
    spent = total_bytes = 0
    for rel, h in prior.items():
        p = HERE/rel
        assert sha(p) == h
        r = read(p)
        assert r['stage'] == 'preflight' and r['wall_seconds'] >= 0
        exit_record = read(p.parent/'exit.json')
        spent += max(r['wall_seconds'], exit_record['supervisor_wall_seconds'])
        total_bytes += sum(f.stat().st_size for f in p.parent.rglob('*') if f.is_file())
    assert spent+K.CAP[stage] <= K.TOTAL_CAP
    if stage == 'formal':
        vp = HERE/a['preflight_verification_path']
        assert sha(vp) == a['preflight_verification_sha256']
        v = read(vp)
        assert v['status'] == 'passed' and v['freeze_sha256'] == a['freeze_sha256']
        assert v['receipt_path'] in prior and v['receipt_sha256'] == prior[v['receipt_path']]
        pre_root = (HERE/v['receipt_path']).parent
        assert read(pre_root/'receipt.json')['status'] == 'completed' and read(pre_root/'exit.json')['returncode'] == 0
        assert v['formal_seconds_estimate'] <= K.CAP['formal']
        assert total_bytes+v['formal_bytes_estimate'] <= K.STORAGE
    return a, total_bytes


def worker(stage, gpu, auth_path, output):
    a, prior_bytes = authorize(auth_path, stage)
    assert os.environ.get('WSB_SUPERVISOR_PID') == str(os.getppid()), 'use run: independent hard timeout required'
    V = runtime()
    import torch
    sys.path.insert(0, str(V.T1.SOURCE))
    from control_engine import ControlEngine
    output = Path(output).resolve()
    assert output.is_relative_to(HERE/'runs')
    output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    rc = dict(status='running', stage=stage, pid=os.getpid(), gpu=gpu, counts={k: 0 for k in V.COUNT_KEYS},
              arm_counts={k: 0 for k in ('baseline', 'source', 'replay', 'zero')}, files={}, bytes=0,
              prior_bytes=prior_bytes, freeze_sha256=a['freeze_sha256'], authorization_sha256=sha(auth_path))
    write(output/'authorization.json', read(auth_path), immutable=True)
    write(output/'receipt.json', rc)
    try:
        source = read(V.T1.SOURCE/'contract.json')['source']
        engine = ControlEngine(source['model_path'], V.exp.model_spec(), f'cuda:{gpu}')
        V.exp.metadata_check(engine)
        check_model_assets(V.exp.model_assets(), read(HERE/a['freeze_path'])['model_assets'])
        write(output/'metadata.json', engine.metadata, immutable=True)
        meter = Meter(V, gpu)
        meter.add('load', time.monotonic()-start)
        with meter:
            execute(engine, V, stage, output, rc, meter)
        integrity_start = time.monotonic()
        rc['integrity'] = engine.verify_unchanged()
        assert rc['integrity']['hooks_removed']
        assert rc['integrity']['target_weight_sha256_after'] == engine.metadata['target_weight_sha256_before']
        check_files(read(HERE/a['freeze_path']))
        meter.add('integrity', time.monotonic()-integrity_start)
        finalize_start = time.monotonic()
        assert all(sha(output/p) == h for p, h in rc['files'].items())
        meter.add('finalize_per_pair', (time.monotonic()-finalize_start)/K.limits(stage)['pairs'])
        rc['timing_maxima'] = meter.maxima
        rc['peak_memory_bytes'] = torch.cuda.max_memory_allocated(gpu)
        rc['status'] = 'completed'
    except BaseException:
        rc.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        rc['wall_seconds'] = time.monotonic()-start
        write(output/'receipt.json', rc)
    if stage == 'preflight':
        tokens = sum(v['plan']['b']+1 for v in V.LVKR.ledger().values())
        estimate = K.project_seconds(rc['timing_maxima'], tokens)
        measured = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
        byte_estimate = math.ceil(1.25*measured*K.limits('formal')['pairs']/K.limits('preflight')['pairs'])
        write(output/'verification.json', dict(status='passed', stage=stage, freeze_sha256=a['freeze_sha256'],
              formal_seconds_estimate=estimate, formal_bytes_estimate=byte_estimate,
              budget_gate='passed' if estimate <= K.CAP['formal'] and byte_estimate+prior_bytes+measured <= K.STORAGE else 'blocked',
              receipt_path=str((output/'receipt.json').relative_to(HERE)), receipt_sha256=sha(output/'receipt.json')), immutable=True)


def launch(stage, gpu, auth_path, output):
    _, prior_bytes = authorize(auth_path, stage)  # denial precedes nvidia-smi and imports of torch/model code
    import fcntl
    with open('/tmp/acupuncture-wsb-01.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)  # one WSB worker, even across different GPUs
        return launch_locked(stage, gpu, auth_path, output, prior_bytes)


def launch_locked(stage, gpu, auth_path, output, prior_bytes):
    assert isinstance(gpu, int) and gpu >= 0
    procs = subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-compute-apps=pid', '--format=csv,noheader,nounits'], text=True, timeout=10).strip()
    assert not procs, 'GPU occupied; no queue or shared run'
    free = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True, timeout=10).strip())
    assert free >= 24576, 'insufficient free GPU memory'
    output = Path(output).resolve()
    assert output.is_relative_to(HERE/'runs') and not output.exists()
    output.parent.mkdir(parents=True, exist_ok=True)
    estimate = None if stage == 'preflight' else read(HERE/read(auth_path)['preflight_verification_path'])['formal_bytes_estimate']
    assert shutil.disk_usage(output.parent).free >= K.required_free_bytes(stage, estimate), 'insufficient stage artifact space'
    command = [sys.executable, str(Path(__file__).resolve()), '_worker', '--stage', stage,
               '--gpu', str(gpu), '--authorization', str(Path(auth_path).resolve()), '--output', str(output)]
    start = time.monotonic()
    with output.with_suffix('.log').open('x') as log:
        try:
            p = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=K.CAP[stage], check=False,
                               env={**os.environ, 'WSB_SUPERVISOR_PID': str(os.getpid())})
            code = p.returncode
        except subprocess.TimeoutExpired:
            code = -9  # subprocess.run killed and waited for this child only
        wall = time.monotonic()-start
        output.mkdir(exist_ok=True)
        write(output/'exit.json', {'returncode': code, 'supervisor_wall_seconds': wall}, immutable=True)
        if code != 0:
            path = output/'receipt.json'
            rc = read(path) if path.exists() else {'stage': stage, 'files': {}}
            rc.update(status='failed', wall_seconds=wall, supervisor_returncode=code)
            write(path, rc)
            raise RuntimeError('WSB worker failed or timed out; preserved partial evidence')
    rc = read(output/'receipt.json')
    assert rc['status'] == 'completed'
    check_counts(rc, stage, complete=True)
    assert rc['wall_seconds'] <= K.CAP[stage]
    return {'status': 'completed', 'output': str(output)}


def analyse_run(path, output):
    path = Path(path)
    rc = read(path/'receipt.json')
    assert rc['status'] == 'completed' and rc['stage'] == 'formal'
    assert read(path/'exit.json')['returncode'] == 0
    check_counts(rc, 'formal', complete=True)
    assert all(sha(path/p) == h for p, h in rc['files'].items())
    data = read(path/'answers.json')
    result = K.analyse(data['rows'], *K.panel())
    result['delivery'] = {}
    for cell, rows in data['delivery'].items():
        conflict = [r for r in rows if r['donor_type'] in ('AL', 'BD')]
        result['delivery'][cell] = dict(n=len(rows), valid=sum(r['row'] in (0,1,2) for r in rows),
            own=sum(r['row'] == r['self_row'] for r in rows), donor_row=sum(r['row'] == r['donor_row'] for r in rows),
            other_row=sum(r['row'] in (0,1,2) and r['row'] not in (r['self_row'],r['donor_row']) for r in rows),
            first_stop=sum(not r['N']['reached_t2'] for r in rows),
            later_stop=sum(r['N']['reached_t2'] and r['N']['termination'] == 'stop' for r in rows),
            no_answer=sum(r['classification']['tags']['n_distinct_codes'] == 0 for r in rows),
            multi_code=sum(r['classification']['main'] == 'multi_code' for r in rows),
            other=sum(r['row'] == 'other' for r in rows), truncated=sum(r['N']['termination'] == 'budget' for r in rows),
            conflict_n=len(conflict), conflict_own_correct=sum(r['row'] == r['self_row'] for r in conflict))
    write(output, result, immutable=True)
    return {'status': 'analysed', 'output': str(output)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    q = sub.add_parser('assets'); q.add_argument('--output', required=True); q.add_argument('--environment', action='store_true')
    q = sub.add_parser('analyse'); q.add_argument('path'); q.add_argument('--output', required=True)
    for name in ('run', '_worker'):
        q = sub.add_parser(name)
        q.add_argument('--stage', choices=tuple(K.CAP), required=True)
        q.add_argument('--gpu', type=int, required=True)
        q.add_argument('--authorization', required=True); q.add_argument('--output', required=True)
    a = p.parse_args()
    if a.command == 'assets':
        result = assets(a.output, a.environment)
    elif a.command == 'analyse':
        result = analyse_run(a.path, a.output)
    else:
        result = (launch if a.command == 'run' else worker)(a.stage, a.gpu, a.authorization, a.output)
    print(json.dumps(result, ensure_ascii=False))
