"""Contract §5 judgement from verified run records. CPU only.

python analyze_localize.py selftest
python analyze_localize.py run RUN_DIR OUT_JSON
"""
import importlib.util
import json
from pathlib import Path
import random
import statistics
import sys

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('readout_analyze', HERE.parent / 'early-stop-knowledge-readout-v1-2026-10-29/analyze.py')
readout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(readout)
signflip_p = readout.signflip_p

BAND_LOW = 0.897  # development reference band from early-stop-knowledge-readout (frozen)
ARMS = ('A0', 'A2', 'A3', 'A4', 'A5')
ANCHORS = ('N_L00_C4146_D+1', 'N_L02_C5251_D-1', 'N_L02_C5063_D+1')


def S_by_base(lls, items):
    """lls: {item_id: [ll(A), ll(B)]} -> {base: S}; target_index 0 means A is correct."""
    bases = {}
    for iid, it in items.items():
        bases.setdefault(it['base_id'], {})[it['target_index']] = iid
    out = {}
    for b, t in bases.items():
        if t.get(0) in lls and t.get(1) in lls:
            a, c = lls[t[0]], lls[t[1]]
            out[b] = (a[0] - a[1]) - (c[0] - c[1])
    return out


def ratio(s, clean):
    common = sorted(set(s) & set(clean))
    return statistics.median(s[b] / clean[b] for b in common)


def tier(s_arm, s_a0, clean):
    r = ratio(s_arm, clean)
    if r >= BAND_LOW:
        return 'restored', r, None
    diffs = [s_arm[b] - s_a0[b] for b in sorted(set(s_arm) & set(s_a0))]
    p = signflip_p(diffs)
    return ('partial' if p < 0.01 else 'not_restored'), r, p


def carrier(tiers):
    """tiers: {arm: tier}. Contract §5.2 table."""
    if tiers['A0'] == 'restored':
        return 'not_applicable'
    kv = tiers['A2'] in ('restored', 'partial')
    lin = tiers['A5'] in ('restored', 'partial')
    if kv and not lin:
        return 'kv'
    if lin and not kv:
        rec, conv = tiers['A3'] in ('restored', 'partial'), tiers['A4'] in ('restored', 'partial')
        return 'linear:recurrent' if rec and not conv else 'linear:conv' if conv and not rec else 'linear:both' if rec and conv else 'linear:joint'
    return 'either_needed' if kv and lin else 'any_suffices'


def decay(s_b1, s_b2):
    diffs = [s_b1[b] - s_b2[b] for b in sorted(set(s_b1) & set(s_b2))]
    if signflip_p(diffs) < 0.01:
        return 'decay_holds', diffs
    if signflip_p([-d for d in diffs]) < 0.01:
        return 'reversed', diffs
    return 'indistinguishable', diffs


def judge(table, items):
    """table: {(condition, arm): {item_id: [llA, llB]}} plus ('clean','A1')."""
    clean = S_by_base(table[('clean', 'A1')], items)
    result = {'clean_S': clean, 'conditions': {}}
    conditions = sorted({c for c, a in table if c != 'clean'})
    for c in conditions:
        s = {a: S_by_base(table[(c, a)], items) for a in ARMS if (c, a) in table}
        tiers, detail = {}, {}
        r0 = ratio(s['A0'], clean)
        tiers['A0'] = 'restored' if r0 >= BAND_LOW else 'failed'
        detail['A0'] = {'R': r0}
        for a in ARMS[1:]:
            t, r, p = tier(s[a], s['A0'], clean)
            tiers[a], detail[a] = t, {'R': r, 'p_vs_A0': p}
        row = {'tiers': tiers, 'detail': detail, 'carrier': carrier(tiers)}
        if (c, 'B1') in table and (c, 'B2') in table:
            b1, b2 = S_by_base(table[(c, 'B1')], items), S_by_base(table[(c, 'B2')], items)
            verdict, diffs = decay(b1, b2)
            row['decay'] = {'verdict': verdict, 'R_B1': ratio(b1, clean), 'R_B2': ratio(b2, clean), 'mean_diff': statistics.fmean(diffs)}
        result['conditions'][c] = row
    anchors = [result['conditions'][c]['carrier'] for c in ANCHORS if c in result['conditions']]
    result['main_prediction'] = {'anchors': dict(zip([c for c in ANCHORS if c in result['conditions']], anchors)),
                                 'holds': sum(a == 'linear:recurrent' for a in anchors) >= 2}
    return result


def load_run(run):
    run = Path(run)
    table, items, eos, attention, records = {}, {}, {}, {}, 0
    for receipt in sorted(run.glob('worker-*/receipt.json')):
        rec_hashes = json.loads(receipt.read_text())['record_hashes']
        for rel in rec_hashes:
            r = json.loads((receipt.parent / rel).read_text())
            records += 1
            key = (r['spec']['condition_id'], r['spec']['arm'])
            items[r['item']['id']] = r['item']
            table.setdefault(key, {})[r['item']['id']] = [c['loglikelihood'] for c in r['candidates']]
            g = r['generation']
            eos.setdefault(key, []).append(len(g['token_ids']) == 1 and g['end_reason'] == 'eos_token')
            if g.get('first_token_attention'):
                attention.setdefault(key, []).append(g['first_token_attention'])
    return table, items, eos, attention, records


def run(run_dir, out):
    table, items, eos, attention, n = load_run(run_dir)
    result = judge(table, items)
    result['records'] = n
    result['first_step_eos'] = {f'{c}|{a}': sum(v) for (c, a), v in eos.items()}
    result['first_token_attention_mean'] = {f'{c}|{a}': {k: statistics.fmean(x[k] for x in v) for k in v[0]}
                                            for (c, a), v in attention.items()}
    with open(out, 'x') as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    return result


def selftest():
    rng = random.Random(1)
    items = {}
    for b in range(12):
        for t in (0, 1):
            items[f'B{b}-f{t}'] = {'id': f'B{b}-f{t}', 'base_id': f'B{b}', 'target_index': t}
    mag = {b: rng.uniform(5, 15) for b in range(12)}

    def lls(scale):
        return {iid: [mag[int(it['base_id'][1:])] * scale * (1 if it['target_index'] == 0 else -1) / 2 + rng.gauss(0, .2), 0.0]
                for iid, it in items.items()}
    table = {('clean', 'A1'): lls(1.0)}
    scenarios = {
        'kv': dict(A0=0, A2=1, A3=0, A4=0, A5=0),
        'rec': dict(A0=0, A2=0, A3=1, A4=0, A5=1),
        'conv': dict(A0=0, A2=0, A3=0, A4=1, A5=1),
        'either': dict(A0=0, A2=1, A3=0, A4=0, A5=1),
        'any': dict(A0=0, A2=0, A3=0, A4=0, A5=0),
        'partial_kv': dict(A0=0, A2=.5, A3=0, A4=0, A5=0),
        'lin_both': dict(A0=0, A2=0, A3=1, A4=1, A5=1),
        'lin_joint': dict(A0=0, A2=0, A3=0, A4=0, A5=1),
        'na': dict(A0=1, A2=1, A3=1, A4=1, A5=1),
    }
    for name, arms in scenarios.items():
        for a, v in arms.items():
            table[(name, a)] = lls(v)
    for name, (b1, b2) in {'dec': (.8, .1), 'rev': (.1, .8), 'flat': (.4, .4)}.items():
        for a in ARMS:
            table[(name, a)] = lls(0)
        table[(name, 'B1')], table[(name, 'B2')] = lls(b1), lls(b2)
    res = judge(table, items)
    got = {c: v['carrier'] for c, v in res['conditions'].items()}
    want = {'kv': 'kv', 'rec': 'linear:recurrent', 'conv': 'linear:conv', 'either': 'either_needed',
            'any': 'any_suffices', 'partial_kv': 'kv', 'na': 'not_applicable',
            'lin_both': 'linear:both', 'lin_joint': 'linear:joint'}
    for k, v in want.items():
        assert got[k] == v, (k, got[k])
    assert res['conditions']['partial_kv']['tiers']['A2'] == 'partial'
    decays = {c: res['conditions'][c]['decay']['verdict'] for c in ('dec', 'rev', 'flat')}
    assert decays == {'dec': 'decay_holds', 'rev': 'reversed', 'flat': 'indistinguishable'}, decays
    print('selftest passed', got, decays)


if __name__ == '__main__':
    selftest() if sys.argv[1] == 'selftest' else run(*sys.argv[2:4])
