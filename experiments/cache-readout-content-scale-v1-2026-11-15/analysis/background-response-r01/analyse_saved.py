"""CPU-only descriptive reuse of frozen RCS records; no model imports/forwards."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import statistics
import time

os.environ['CUDA_VISIBLE_DEVICES'] = ''
START = time.monotonic()
MAX_SECONDS = 1800
MAX_OUTPUT = 128 * 2**20
G = (13, 14, 16, 17, 18, 20, 21, 22, 24, 25, 26, 28, 29, 30)
SOURCE_SHA = 'feef68e10fac5b205a0906641c6f4f736143458944f7e35c023e51b768d3bbe2'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 2**20), b''):
            h.update(chunk)
    return h.hexdigest()


def mean(values):
    values = list(values)
    return statistics.mean(values) if values else None


def receiver_mean(rows, field):
    groups = {}
    for row in rows:
        value = row[field]
        if value is not None:
            groups.setdefault(row['receiver'], []).append(value)
    return mean(mean(v) for v in groups.values())


def continuous(a):
    rows = []
    for p in a['continuous']['pairs']:
        row = {k: p[k] for k in ('receiver', 'donor', 'scenario')}
        for bg in ('C', 'H'):
            b = p['backgrounds'][bg]
            l = b['L']
            terms = {'C0': l['10']-l['00'], 'C1': l['11']-l['01'],
                     'S0': l['01']-l['00'], 'S1': l['11']-l['10'],
                     'all_uses': l['11']-l['00'], 'residual00': l['00']+b['m'],
                     'e': b['e']}
            assert abs(terms['all_uses']+terms['residual00']-b['e']) < 1e-9
            assert abs(terms['C0']+terms['S1']-terms['all_uses']) < 1e-9
            assert abs(terms['C1']+terms['S0']-terms['all_uses']) < 1e-9
            row.update({bg+'_'+k: v for k, v in terms.items()})
        row.update({'delta_'+k: row['H_'+k]-row['C_'+k] for k in terms})
        rows.append(row)
    fields = [k for k in rows[0] if k not in ('receiver', 'donor', 'scenario')]
    return {'kind': 'posthoc_descriptive_same_data_no_new_intervals', 'pairs': rows,
            'means': {k: receiver_mean(rows, k) for k in fields},
            'scenarios': {s: {k: receiver_mean([r for r in rows if r['scenario'] == s], k)
                             for k in fields} for s in sorted({r['scenario'] for r in rows})}}


def ratio(a, b):
    return a/b if b != 0 else None


def tensor_metrics(t, state):
    import torch
    norm = lambda x: float(x.double().norm())
    # Matches the frozen source: FP32 l2norm, eps inside rsqrt, then query scaling.
    q = t['q'].float()
    q = q * torch.rsqrt(q.square().sum(-1, keepdim=True)+1e-6)
    q = (q / math.sqrt(q.shape[-1])).reshape(32, 128).double()
    k = t['k'].float()
    k = (k * torch.rsqrt(k.square().sum(-1, keepdim=True)+1e-6)).reshape(32, 128).double()
    j = state['J'].reshape(32, 128, 128).double()
    alpha = t['log_decay'].reshape(32).double().exp()
    beta = t['beta'].reshape(32).double()
    jq = (j*q.unsqueeze(-1)).sum(-2)
    jk = (j*k.unsqueeze(-1)).sum(-2)
    direct = alpha[:, None]*jq
    erase = (alpha*beta*(k*q).sum(-1))[:, None]*jk
    net = direct-erase
    raw = (t['raw1'].double()-t['raw0'].double()).reshape_as(net)
    oracle_error = float((net-raw).abs().max()) / max(1., float(net.abs().max()))
    assert oracle_error <= 1e-5, oracle_error
    x0, x1 = t['x0'].reshape_as(net), t['x1'].reshape_as(net)
    d = x1.double()-x0.double()
    weight = t['weight'].double()
    gate = torch.nn.functional.silu(t['z'].float()).double().reshape_as(net)
    metrics = {'J': norm(j), 'Jq': norm(jq), 'D': norm(direct), 'E': norm(erase),
               'raw_d': norm(raw), 'cast_d': norm(d),
               'alpha_weighted_gain': ratio(norm(direct), norm(jq)),
               'net_over_D': ratio(norm(net), norm(direct)),
               'D_E_cos': ratio(float((direct*erase).sum()), norm(direct)*norm(erase)),
               'E_over_D': ratio(norm(erase), norm(direct)),
               'D_dot_E': float((direct*erase).sum()),
               'oracle_error': oracle_error,
               'alpha_mean': float(alpha.mean()), 'beta_mean': float(beta.mean())}
    vectors = {'raw_d': raw, 'cast_d': d, 'gate_operator': weight*gate,
               'inv_r0': t['inv_r0'].double().reshape(32, 1),
               'inv_r1': t['inv_r1'].double().reshape(32, 1)}
    assert abs(norm(net)**2-(norm(direct)**2+norm(erase)**2-2*float((direct*erase).sum()))) < 1e-8*max(1.,norm(net)**2)
    for r in ('0', '1'):
        inv = t['inv_r'+r].double().reshape(32, 1)
        scaled = d*inv
        weighted = scaled*weight
        gated = weighted*gate
        metrics.update({'scaled'+r: norm(scaled), 'weighted'+r: norm(weighted),
                        'gated'+r: norm(gated),
                        'scale_gain'+r: ratio(norm(scaled), norm(d)),
                        'gate_gain'+r: ratio(norm(gated), norm(weighted))})
        vectors['gated'+r] = gated
    # Same local native11 drivers, not the global 11-minus-01 arm difference.
    inv1 = t['inv_r1'].float().reshape(32, 1)
    def endpoint(x):
        out = t['weight'] * (x.float()*inv1).to(x.dtype)
        return (out*torch.nn.functional.silu(t['z'].float()).reshape_as(out)).to(x.dtype)
    n1, n0 = endpoint(x1), endpoint(x0)
    saved_native = t['native_norm'].reshape_as(n1)
    # GPU/CPU SiLU rounding is not bitwise portable. All 39,911,424 saved
    # values were audited: only 3 differ, each by one output BF16 ULP.
    ulps = torch.maximum(torch.nextafter(saved_native.abs(), torch.full_like(saved_native, float('inf')))-saved_native.abs(), torch.nextafter(n1.abs(), torch.full_like(n1, float('inf')))-n1.abs()).double()
    discrepancy = (n1.double()-saved_native.double()).abs()
    assert torch.all(discrepancy <= ulps), 'CPU reconstruction differs by more than one output ULP'
    metrics['cpu_native_different_values'] = int((discrepancy != 0).sum())
    metrics['cpu_native_max_abs_error'] = float(discrepancy.max())
    finite_num = n1.double()-n0.double()
    metrics['cpu_finite_num1'] = norm(finite_num)
    metrics['num_rounding_error1'] = norm(finite_num-vectors['gated1'])
    vectors['cpu_finite_num1'] = finite_num
    return metrics, vectors


def scan(root, manifest, a):
    import torch
    torch.set_num_threads(1)
    assert not torch.cuda.is_initialized()
    files = manifest['runs']['formal-20261115-r01']['files']
    selected = sorted(p for p in files if p.endswith('-C11-t2.pt'))
    assert len(selected) == 348
    read_files, rows = {}, []
    def load(rel):
        p = root/rel
        expected = files[rel]
        assert p.stat().st_size == expected['bytes']
        actual = sha(p)
        assert actual == expected['sha256'], rel
        read_files[rel] = expected
        return torch.load(p, map_location='cpu', weights_only=True)
    for index, rel in enumerate(selected):
        assert time.monotonic()-START < MAX_SECONDS
        stem = rel[:-len('-C11-t2.pt')]
        receiver, donor = Path(stem).parent.name, Path(stem).name
        # Only immutable source records; no output files overwritten.
        record_rel = 'runs/formal-20261115-r01/records/'+receiver+'/'+donor+'.json'
        record_path = root/record_rel
        assert sha(record_path) == files[record_rel]['sha256']
        record = json.loads(record_path.read_text())
        bg_data, j_diffs = {}, {}
        for bg in ('C', 'H'):
            tensors, states = load(stem+'-'+bg+'11-t2.pt'), load(stem+'-'+bg+'-t1.pt')
            assert set(tensors) == set(states) == set(G)
            bg_data[bg] = {l: tensor_metrics(tensors[l], states[l]) for l in G}
            if bg == 'C':
                j_c = {l: states[l]['J'] for l in G}
            else:
                j_diffs = {l: float((states[l]['J']-j_c[l]).norm()) for l in G}
                del j_c
            del tensors, states
        for layer in G:
            row = {'receiver': receiver, 'donor': donor, 'scenario': receiver.split('-')[3],
                   'donor_type': record['meta']['donor']['type'], 'layer': layer}
            for bg in ('C', 'H'):
                row.update({bg+'_'+k: v for k, v in bg_data[bg][layer][0].items()})
            row['J_HC_diff'] = j_diffs[layer]
            row['J_HC_relative_diff'] = ratio(j_diffs[layer], row['C_J'])
            for k in ('raw_d', 'cast_d', 'gated0', 'gated1', 'cpu_finite_num1'):
                c, h = bg_data['C'][layer][1][k], bg_data['H'][layer][1][k]
                row['HC_ratio_'+k] = ratio(float(h.norm()), float(c.norm()))
                row['HC_cos_'+k] = ratio(float((c*h).sum()), float(c.norm()*h.norm()))
            # Fixed-vector operator comparisons, not new model interventions.
            vc, vh = bg_data['C'][layer][1], bg_data['H'][layer][1]
            for ref, vref in (('C', vc), ('H', vh)):
                dref = vref['cast_d']
                for rn in ('0', '1'):
                    rc, rh, rr = vc['inv_r'+rn], vh['inv_r'+rn], vref['inv_r'+rn]
                    gc, gh, gr = vc['gate_operator'], vh['gate_operator'], vref['gate_operator']
                    row['fixed_d'+ref+'_r'+ref+rn+'_gate_H_over_C'] = ratio(float((dref*rr*gh).norm()), float((dref*rr*gc).norm()))
                    row['fixed_d'+ref+'_gate'+ref+'_scale'+rn+'_H_over_C'] = ratio(float((dref*rh*gr).norm()), float((dref*rc*gr).norm()))
            rows.append(row)
        if (index+1) % 48 == 0:
            print('read pairs', index+1, 'elapsed', round(time.monotonic()-START, 1), flush=True)
    fields = [k for k in rows[0] if k not in ('receiver','donor','scenario','donor_type','layer')]
    summaries = {}
    for l in G:
        rr = [r for r in rows if r['layer'] == l]
        summaries[str(l)] = {'conflict_means': {k: receiver_mean([r for r in rr if r['donor_type'] in ('AL', 'BD')], k) for k in fields},
                             'conflict_scenarios': {s: {k: receiver_mean([r for r in rr if r['scenario'] == s and r['donor_type'] in ('AL', 'BD')], k) for k in fields} for s in sorted({r['scenario'] for r in rr})},
                             'means': {k: receiver_mean(rr, k) for k in fields},
                             'scenarios': {s: {k: receiver_mean([r for r in rr if r['scenario'] == s], k)
                                              for k in fields} for s in sorted({r['scenario'] for r in rr})},
                             'undefined': {k: sum(r[k] is None for r in rr) for k in fields}}
    assert not torch.cuda.is_initialized()
    return {'rows': rows, 'per_layer': summaries, 'verified_input_files': read_files,
            'verified_input_bytes': sum(x['bytes'] for x in read_files.values()),
            'cuda_initialized': False, 'model_forwards': 0, 'torch_threads': torch.get_num_threads()}


def self_test():
    # Unequal donor counts must not change receiver weights.
    rows = [{'receiver':'a','x':1}, {'receiver':'a','x':3}, {'receiver':'b','x':8}]
    assert receiver_mean(rows,'x') == 5
    assert ratio(1,0) is None
    b = {'L': {'00':-4.,'10':-1.,'01':-3.5,'11':0.}, 'm':5., 'e':5.}
    p = {'receiver':'a','donor':'d','scenario':'s','backgrounds':{'C':b,'H':b}}
    out = continuous({'continuous':{'pairs':[p]}})
    assert out['means']['C_C0'] == 3 and out['means']['C_C1'] == 3.5
    assert out['means']['C_residual00'] == 1 and out['means']['delta_e'] == 0
    print('self-test passed: weighting, residual, endpoint contrasts, zero denominators')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--tensors', action='store_true')
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    assert args.root and args.output and not args.output.exists()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('CPU budget exceeded')))
    signal.alarm(MAX_SECONDS)
    source = args.root/'runs/formal-20261115-r01/analysis.json'
    assert sha(source) == SOURCE_SHA
    a = json.loads(source.read_text())
    result = {'analysis_source_sha256': SOURCE_SHA, 'script_sha256': sha(Path(__file__)),
              'continuous': continuous(a), 'model_forwards': 0}
    if args.tensors:
        manifest_path = args.manifest or args.root/'readiness/artifacts-final-r01.json'
        manifest = json.loads(manifest_path.read_text())
        result['manifest_sha256'] = sha(manifest_path)
        result['tensors'] = scan(args.root, manifest, a)
    result['elapsed_seconds'] = time.monotonic()-START
    content = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    assert len(content.encode()) < MAX_OUTPUT
    with args.output.open('x') as f:
        f.write(content)
    print('completed', args.output, 'seconds', result['elapsed_seconds'], flush=True)


if __name__ == '__main__':
    main()
