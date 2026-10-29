"""Fact-sensitivity readout from forced candidate scores (CONTRACT.zh-CN.md). CPU only.

python analyze.py selftest
python analyze.py run PANEL EXPORT_ZST DATA_JSON OUT_JSON
"""
import itertools
import json
import random
import statistics
import subprocess
import sys


def load(export, data):
    items = {r['id']: r for r in json.load(open(data))}
    ll = {}
    for line in subprocess.run(['zstd', '-dc', export], capture_output=True, check=True).stdout.decode().splitlines():
        r = json.loads(line)
        if r['spec'].get('mode') != 'full' or not r['candidates']:
            continue
        item = items[r['item_id']]
        assert [c['text'] for c in r['candidates']] == item['choices']
        ll[(r['condition']['id'], r['item_id'])] = {'lls': [c['loglikelihood'] for c in r['candidates']],
            'eos_first': len(r['token_ids']) == 1 and r['end_reason'] == 'eos_token', 'condition': r['condition']}
    return items, ll


def sensitivity(items, ll, cid):
    """S(c,b) per base; None if a fact is missing."""
    bases = {}
    for iid, it in items.items():
        bases.setdefault(it['base_id'], {})[it['target_index']] = iid
    out = {}
    for b, by_target in sorted(bases.items()):
        a_correct, b_correct = by_target.get(0), by_target.get(1)
        ra, rb = ll.get((cid, a_correct)), ll.get((cid, b_correct))
        if ra is None or rb is None:
            out[b] = None
            continue
        out[b] = {'S': (ra['lls'][0] - ra['lls'][1]) - (rb['lls'][0] - rb['lls'][1]),
                  'both_eos_first': ra['eos_first'] and rb['eos_first']}
    return out


def signflip_p(values):
    obs = statistics.fmean(values)
    hits = total = 0
    for signs in itertools.product((1, -1), repeat=len(values)):
        total += 1
        hits += statistics.fmean(s * v for s, v in zip(signs, values)) >= obs - 1e-12
    return hits / total


def ratio(s, clean):
    return statistics.median(s[b]['S'] / clean[b]['S'] for b in s)


def tier(r, p, band_low):
    if r >= band_low:
        return 'retained'
    return 'reduced_present' if p < 0.01 else 'not_detected'


def evaluate(items, ll, conds, reference_ids):
    clean = sensitivity(items, ll, 'clean')
    assert all(v and v['S'] != 0 for v in clean.values())
    refs = sorted(ratio({b: v for b, v in sensitivity(items, ll, c).items()}, clean) for c in reference_ids)
    q = lambda x: refs[min(len(refs) - 1, max(0, round(x * (len(refs) - 1))))]
    band = (q(0.025), q(0.975))
    rows = {}
    for cid in conds:
        s = sensitivity(items, ll, cid)
        if any(v is None for v in s.values()):
            rows[cid] = {'tier': 'not_computable'}
            continue
        vals = [v['S'] for v in s.values()]
        r, p = ratio(s, clean), signflip_p(vals)
        sub = {b: v for b, v in s.items() if v['both_eos_first']}
        rows[cid] = {'R': r, 'p': p, 'mean_S': statistics.fmean(vals), 'tier': tier(r, p, band[0]),
                     'eos_subset_bases': len(sub),
                     'eos_subset': None if len(sub) < 2 else {'R': ratio(sub, clean), 'p': signflip_p([v['S'] for v in sub.values()]),
                                                               'tier': tier(ratio(sub, clean), signflip_p([v['S'] for v in sub.values()]), band[0])}}
    return {'reference_band': band, 'reference_conditions': len(refs),
            'clean_S': {b: v['S'] for b, v in clean.items()}, 'conditions': rows}


def selftest():
    rng = random.Random(0)
    items = {}
    for b in range(12):
        for t in (0, 1):
            items[f'B{b}-f{t}'] = {'id': f'B{b}-f{t}', 'base_id': f'B{b}', 'target_index': t}
    ll = {}
    def put(cid, f):
        for iid, it in items.items():
            ll[(cid, iid)] = {'lls': f(it), 'eos_first': True, 'condition': {}}
    base = {b: rng.uniform(4, 12) for b in range(12)}
    clean = lambda it: [base[int(it['base_id'][1:])] * (1 if it['target_index'] == 0 else -1) / 2 + rng.gauss(0, .3), 0.0]
    put('clean', clean)
    refs = [f'ref{i}' for i in range(48)]
    for c in refs:
        put(c, lambda it: [clean(it)[0] * rng.uniform(.85, 1.15), 0.0])
    put('same', lambda it: ll[('clean', it['id'])]['lls'])
    put('zero', lambda it: [rng.gauss(0, .3), 0.0])
    put('weak', lambda it: [clean(it)[0] * .3 + rng.gauss(0, .1), 0.0])
    out = evaluate(items, ll, ['same', 'zero', 'weak'], refs)
    got = {c: v['tier'] for c, v in out['conditions'].items()}
    assert got == {'same': 'retained', 'zero': 'not_detected', 'weak': 'reduced_present'}, got
    print('selftest passed', got, 'band', [round(x, 3) for x in out['reference_band']])
    return got


def run(panel, export, data, out):
    items, ll = load(export, data)
    conds = sorted({c for c, _ in ll})
    meta = {c: next(v['condition'] for (cc, _), v in ll.items() if cc == c) for c in conds}
    refs = [c for c in conds if meta[c]['kind'] == 'native' and abs(meta[c]['dose']) == 0.25]
    targets = [c for c in conds if meta[c]['kind'] != 'clean']
    result = evaluate(items, ll, targets, refs)
    for c, row in result['conditions'].items():
        m = meta[c]
        row.update(kind=m['kind'], layer=m['layer'], dose=m['dose'],
                   window='early' if m['layer'] < 4 else 'middle' if m['layer'] < 16 else 'late')
    result['panel'] = panel
    with open(out, 'x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


if __name__ == '__main__':
    selftest() if sys.argv[1] == 'selftest' else run(*sys.argv[2:6])
