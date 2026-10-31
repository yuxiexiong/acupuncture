"""CFM-S3 v3 judgments (CONTRACT.zh-CN.md §5-§6 = design r3 §8). Pure Python; reads verified formal records.

Four separate steps per (anchor, window, readout, base, cell): (1) directional effect beyond the same-direction
null, (2) magnitude N or S, (3) band (>=0.8 near complete, 0.2-0.8 partial, <=0.2 little), (4) support / refute /
insufficient, where refutation requires the null resolution r <= 0.5.

python s3_analysis.py run RUN_DIR --out ANALYSIS_DIR
python s3_analysis.py selftest
"""
import argparse
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
GROUPS = ('V', 'R', 'K', 'Qc', 'KV')
COMBOS = ('R+K', 'V+R+K', 'V+K')
BANDS = {'complete': 0.8, 'little': 0.2}
R_MAX = 0.5          # refutation needs resolution r <= 0.5
Q = 0.95             # same-direction null quantile
INTERACTION_NEGLIGIBLE = 0.2
READOUTS = ('D', 'S_fact')


def quantile(xs, q=Q):
    xs = sorted(xs)
    if not xs:
        return float('nan')
    pos = q * (len(xs) - 1)
    lo, hi = math.floor(pos), math.ceil(pos)
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def band(x):
    if x is None or math.isnan(x):
        return None
    return 'complete' if x >= BANDS['complete'] else ('little' if x <= BANDS['little'] else 'partial')


# ---------------------------------------------------------------- readouts per base

def base_readouts(facts):
    """facts: {target_index: (first_step, candidates)} -> D (mean stop advantage) and S_fact."""
    ll = {t: [c['loglikelihood'] for c in facts[t][1]] for t in (0, 1)}
    return {'D': (facts[0][0]['stop_advantage'] + facts[1][0]['stop_advantage']) / 2,
            'S_fact': (ll[0][0] - ll[0][1]) - (ll[1][0] - ll[1][1]),
            'EOS': sum(bool(facts[t][2]) for t in (0, 1))}


def collect(records):
    """-> table[(anchor, base)] = {'ref': {arm: readouts}, 'cell': {name: readouts}}"""
    by = {}
    for rec in records:
        u, it = rec['unit'], rec['item']
        d = by.setdefault((u['anchor'], it['base_id']), {'ref': {}, 'cell': {}})
        for arm, r in rec['references'].items():
            d['ref'].setdefault(arm, {})[it['target_index']] = (r['first_step'], r['candidates'], r['first_step_eos'])
        for c in rec['cells']:
            d['cell'].setdefault(c['cell']['name'], {})[it['target_index']] = (c['first_step'], c['candidates'], c['first_step_eos'])
    table = {}
    for key, d in by.items():
        assert all(set(v) == {0, 1} for v in list(d['ref'].values()) + list(d['cell'].values())), key
        table[key] = {'ref': {a: base_readouts(v) for a, v in d['ref'].items()}, 'cell': {n: base_readouts(v) for n, v in d['cell'].items()}}
    return table


# ---------------------------------------------------------------- step functions

def normalized(kind, y, y_t, y_ref):
    """remove/scope/post: recovery toward the reference; keep: retention of the original effect."""
    delta = y_ref - y_t
    if delta == 0:
        return float('nan')
    return (y - y_t) / delta if kind != 'keep' else (y_ref - y) / delta


def judge_cell(value, null_values, denominator_ok):
    """Steps 1-3 for one base; null_values are normalized same-direction null values pooled over bases and draws."""
    if not denominator_ok:
        return {'value': None, 'directional': None, 'band': None, 'r': None, 'note': 'denominator_unresolved'}
    q = quantile(null_values) if null_values else float('nan')
    r = max(q, 0.0) if not math.isnan(q) else float('nan')
    return {'value': value, 'directional': (value > q) if not math.isnan(q) else None, 'band': band(value), 'r': r}


def verdict_single(n, s):
    """Contract §6: G necessary-and-sufficient under the stated replacements."""
    if n['value'] is None or s['value'] is None:
        return 'insufficient'
    if n['directional'] and s['directional'] and n['band'] == 'complete' and s['band'] == 'complete':
        return 'support'
    if (n['band'] == 'little' and n['r'] <= R_MAX) or (s['band'] == 'little' and s['r'] <= R_MAX):
        return 'refute'
    return 'insufficient'


def verdict_joint(nA, nB, nAB, sA, sB, sAB):
    """Joint change of A and B required: removing either alone only partial while both complete, or keeping
    either alone little while both complete. Refuted: one side alone complete and the other little."""
    vals = [nA, nB, nAB, sA, sB, sAB]
    if any(v['value'] is None for v in vals):
        return 'insufficient'
    rem = nA['band'] in ('partial', 'little') and nB['band'] in ('partial', 'little') and nAB['band'] == 'complete' and nAB['directional']
    kep = sA['band'] == 'little' and sB['band'] == 'little' and sAB['band'] == 'complete' and sAB['directional']
    if rem or kep:
        return 'support'
    for one, other in ((nA, nB), (nB, nA)):
        if one['band'] == 'complete' and one['directional'] and other['band'] == 'little' and other['r'] <= R_MAX:
            return 'refute'
    return 'insufficient'


def verdict_presence(x):
    if x['value'] is None:
        return 'insufficient'
    if x['directional'] and x['band'] in ('partial', 'complete'):
        return 'support'
    if x['band'] == 'little' and x['r'] <= R_MAX:
        return 'refute'
    return 'insufficient'


def verdict_survives(n_both):
    """Post family (contract §6.3): support if retention 1 - n_both >= 0.2; refute only if the clean follow-up recovers
    >= 0.8, beyond the same-size random follow-up null, with resolution r <= 0.5."""
    if n_both['value'] is None:
        return 'insufficient'
    if 1 - n_both['value'] >= BANDS['little']:
        return 'support'
    if n_both['band'] == 'complete' and n_both['directional'] and n_both['r'] <= R_MAX:
        return 'refute'
    return 'insufficient'


def verdict_complete(x):
    if x['value'] is None:
        return 'insufficient'
    if x['directional'] and x['band'] == 'complete':
        return 'support'
    if x['band'] == 'little' and x['r'] <= R_MAX:
        return 'refute'
    return 'insufficient'


# ---------------------------------------------------------------- the analysis

def window_refs(window):
    return {'E': '01', 'L': '10'}[window]


def analyze_table(table):
    anchors = sorted({a for a, _ in table})
    out = {'per_anchor': {}}
    for anchor in anchors:
        bases = sorted(b for a, b in table if a == anchor)
        res = {}
        for readout in READOUTS:
            for window in ('E', 'L'):
                ref_arm = window_refs(window)
                kinds = {}
                for g in GROUPS + COMBOS:
                    kinds[f'remove:{g}'] = 'remove'
                    kinds[f'keep:{g}'] = 'keep'
                kinds['scope:origin'] = 'scope'
                kinds['scope:later'] = 'scope'
                cellres = {}
                for cname, kind in kinds.items():
                    full = f'{window}:{cname}'
                    nulls_rand, nulls_perm, abs_null = [], [], []
                    vals = {}
                    for b in bases:
                        t = table[(anchor, b)]
                        y_t, y_ref = t['ref']['11'][readout], t['ref'][ref_arm][readout]
                        vals[b] = (normalized(kind, t['cell'][full][readout], y_t, y_ref), y_ref - y_t)
                        for name, y in t['cell'].items():
                            if name.startswith(full + ':null-random'):
                                nulls_rand.append(normalized(kind, y[readout], y_t, y_ref))
                                abs_null.append(abs(y[readout] - (y_t if kind != 'keep' else y_ref)))
                            elif name == full + ':null-perm':
                                nulls_perm.append(normalized(kind, y[readout], y_t, y_ref))
                    floor = quantile(abs_null) if abs_null else 0.0
                    per_base = {}
                    for b, (v, delta) in vals.items():
                        ok = abs(delta) > floor
                        jr = judge_cell(v, nulls_rand, ok)
                        jp = judge_cell(v, nulls_perm, ok) if nulls_perm else None
                        if jp is not None and jr['directional'] is not None and jp['directional'] is not None and jr['directional'] != jp['directional']:
                            jr = dict(jr, note='nulls_disagree_descriptive_only', directional=None)
                        per_base[b] = {'random_null': jr, 'perm_null': jp, 'delta': delta}
                    cellres[cname] = {'per_base': per_base, 'null_random_q95': quantile(nulls_rand) if nulls_rand else None,
                                      'null_perm_q95': quantile(nulls_perm) if nulls_perm else None, 'abs_null_floor': floor}
                # complete cell is a gate; report its readout too
                verdicts = {}
                for b in bases:
                    J = lambda c: cellres[c]['per_base'][b]['random_null']
                    v = {f'single:{g}': verdict_single(J(f'remove:{g}'), J(f'keep:{g}')) for g in GROUPS}
                    v['joint:V_vs_RK'] = verdict_joint(J('remove:V'), J('remove:R+K'), J('remove:V+R+K'), J('keep:V'), J('keep:R+K'), J('keep:V+R+K'))
                    v['joint:V_x_K'] = verdict_joint(J('remove:V'), J('remove:K'), J('remove:V+K'), J('keep:V'), J('keep:K'), J('keep:V+K'))
                    v['scope:origin_complete'] = verdict_complete(J('scope:origin'))
                    v['scope:later_complete'] = verdict_complete(J('scope:later'))
                    inter = {}
                    for a_, b_, ab in (('V', 'R+K', 'V+R+K'), ('V', 'K', 'V+K')):
                        for side in ('remove', 'keep'):
                            xs = [J(f'{side}:{x}')['value'] for x in (ab, a_, b_)]
                            inter[f'{side}:{ab}'] = None if any(x is None for x in xs) else xs[0] - xs[1] - xs[2]
                    verdicts[b] = {'verdicts': v, 'interactions': inter}
                res[f'{readout}|{window}'] = {'cells': cellres, 'bases': verdicts}
            # post-withdrawal family
            for run in ('11', '10'):
                cells = {}
                nulls = []
                vals = {}
                for b in bases:
                    t = table[(anchor, b)]
                    y_t, y_ref = t['ref'][run][readout], t['ref']['00'][readout]
                    rec = {n: normalized('remove', t['cell'][f'post{run}:{n}'][readout], y_t, y_ref) for n in ('Wr', 'Rd', 'both')}
                    vals[b] = (rec, y_ref - y_t, y_t)
                    for d in (0, 1):
                        y = t['cell'][f'post{run}:both:null-random-{d}'][readout]
                        nulls.append(normalized('remove', y, y_t, y_ref))  # recovery under a same-size random follow-up change
                abs_floor = quantile([abs(table[(anchor, b)]['cell'][f'post{run}:both:null-random-{d}'][readout] - vals[b][2])
                                      for b in bases for d in (0, 1)])
                for b, (rec, delta, _) in vals.items():
                    ok = abs(delta) > abs_floor
                    j = judge_cell(rec['both'], nulls, ok)
                    inter = rec['both'] - rec['Wr'] - rec['Rd'] if ok else None
                    cells[b] = {'recovery': rec if ok else None, 'recovery_both': j, 'retention_both': None if j['value'] is None else 1 - j['value'],
                                'verdict_effect_survives_clean_followup': verdict_survives(j),
                                'interaction': inter, 'interaction_negligible': None if inter is None else abs(inter) <= INTERACTION_NEGLIGIBLE,
                                'delta': delta}
                res[f'{readout}|post{run}'] = {'bases': cells, 'null_q95': quantile(nulls), 'abs_null_floor': abs_floor}
        out['per_anchor'][anchor] = res
    out['counts'] = counts(out)
    return out


def counts(out):
    c = {}
    for anchor, res in out['per_anchor'].items():
        for key, r in res.items():
            if 'post' in key:
                c[f'{anchor}|{key}|survives'] = tally(v['verdict_effect_survives_clean_followup'] for v in r['bases'].values())
                continue
            for b, v in r['bases'].items():
                for name, verdict in v['verdicts'].items():
                    c.setdefault(f'{anchor}|{key}|{name}', {}).setdefault(verdict, 0)
                    c[f'{anchor}|{key}|{name}'][verdict] += 1
    return c


def tally(xs):
    out = {}
    for x in xs:
        out[x] = out.get(x, 0) + 1
    return out


def load(run):
    sys.path.insert(0, str(HERE.parent / 'early-input-control-v1-2026-10-29'))
    import experiment as ex
    run = Path(run)
    v = ex.read(run / 'verification.json')
    assert v['status'] == 'passed' and v['stage'] == 'formal'
    recs = []
    for w in sorted(run.glob('worker-*')):
        rcp = ex.read(w / 'receipt.json')
        for p in sorted((w / 'records').glob('*.json')):
            assert ex.sha(p) == rcp['record_hashes'][str(p.relative_to(w))]
            recs.append(ex.read(p))
    assert len(recs) == 24
    return recs, ex


def diagnostics(records):
    """Mismatch ratio per cell family and window (diagnostic only, contract §5.4)."""
    out = {}
    for rec in records:
        ref = rec['reference_displacement_sq']
        for c in rec['cells']:
            cell = c['cell']
            if cell['family'] != 'formation' or 'null' in cell:
                continue
            ins = sum(c['insert_displacement_sq'].values())
            den = sum(ref.get(f'{cell["window"]}|{layer}|{g}', 0.0) for layer in c['cell_layers'] for g in cell['set'])
            out.setdefault(f'{rec["unit"]["anchor"]}|{cell["name"]}', []).append(math.sqrt(ins / den) if den > 0 else None)
    return {k: {'median': sorted(x for x in v if x is not None)[len(v) // 2], 'max': max(x for x in v if x is not None)} for k, v in out.items()}


def run(run_dir, out_dir):
    recs, ex = load(run_dir)
    table = collect(recs)
    result = analyze_table(table)
    result['diagnostics_mismatch'] = diagnostics(recs)
    result['table'] = {f'{a}|{b}': v for (a, b), v in table.items()}
    ex.write(Path(out_dir) / 's3-judgments-r01.json', result, immutable=True)
    return {'counts': result['counts']}


# ---------------------------------------------------------------- selftest: every verdict reachable

def synthetic_table(world, seed=0):
    """Six bases, one anchor, references T (11) = 0, refs (01/10/00) = 10 on both readouts; cell values by world."""
    import random
    rng = random.Random(seed)
    bases = [f'B{i}' for i in range(6)]
    table = {}
    for b in bases:
        ref = {'00': {'D': 10.0, 'S_fact': 10.0, 'EOS': 0}, '01': {'D': 10.0, 'S_fact': 10.0, 'EOS': 0},
               '10': {'D': 10.0, 'S_fact': 10.0, 'EOS': 0}, '11': {'D': 0.0, 'S_fact': 0.0, 'EOS': 2}}
        cell = {}

        def put(name, frac_toward_ref):
            y = 10.0 * frac_toward_ref + rng.uniform(-0.1, 0.1)
            cell[name] = {'D': y, 'S_fact': y, 'EOS': 0}
        noise = {'quiet': 0.02, 'loud': 0.7}[world.get('null', 'quiet')]
        for w in ('E', 'L'):
            put(f'{w}:complete', 1.0)
            for g in GROUPS + COMBOS:
                rv = world.get(f'remove:{g}', 0.0)
                kv = world.get(f'keep:{g}', 0.0)        # retention -> cell value = ref - retention*delta
                put(f'{w}:remove:{g}', rv)
                put(f'{w}:keep:{g}', 1.0 - kv)
                for d in range(2):
                    put(f'{w}:remove:{g}:null-random-{d}', rng.uniform(-noise, noise))
                    put(f'{w}:keep:{g}:null-random-{d}', 1.0 - rng.uniform(-noise, noise))
                if g in GROUPS:
                    put(f'{w}:remove:{g}:null-perm', rng.uniform(-noise, noise))
            for s in ('origin', 'later'):
                put(f'{w}:scope:{s}', world.get(f'scope:{s}', 0.0))
                for d in range(2):
                    put(f'{w}:scope:{s}:null-random-{d}', rng.uniform(-noise, noise))
        for r in ('11', '10'):
            for n in ('Wr', 'Rd', 'both'):
                put(f'post{r}:{n}', world.get(f'post:{n}', 0.0))
            for d in range(2):
                put(f'post{r}:both:null-random-{d}', rng.uniform(-noise, noise))
        table[('A', b)] = {'ref': ref, 'cell': cell}
    return table


def selftest():
    rep = {}
    # V necessary and sufficient -> support; R does nothing with quiet nulls -> refute.
    t = analyze_table(synthetic_table({'remove:V': 1.0, 'keep:V': 1.0}))
    v = t['per_anchor']['A']['D|E']['bases']['B0']['verdicts']
    assert v['single:V'] == 'support' and v['single:R'] == 'refute', v
    rep['single'] = 'support and refute reachable'
    # Loud nulls: nothing can be refuted -> insufficient.
    t = analyze_table(synthetic_table({'remove:V': 1.0, 'keep:V': 1.0, 'null': 'loud'}))
    v = t['per_anchor']['A']['D|E']['bases']['B0']['verdicts']
    assert v['single:R'] == 'insufficient', v
    rep['resolution'] = 'r > 0.5 turns a would-be refutation into insufficient'
    # Joint V with {R,K}: each alone partial, both complete -> support; one side complete, other little -> refute.
    t = analyze_table(synthetic_table({'remove:V': 0.4, 'remove:R+K': 0.4, 'remove:V+R+K': 1.0,
                                       'keep:V': 0.1, 'keep:R+K': 0.1, 'keep:V+R+K': 1.0}))
    v = t['per_anchor']['A']['D|L']['bases']['B1']
    assert v['verdicts']['joint:V_vs_RK'] == 'support', v
    assert abs(v['interactions']['remove:V+R+K'] - 0.2) < 0.05
    t = analyze_table(synthetic_table({'remove:V': 1.0, 'remove:R+K': 0.0, 'remove:V+R+K': 1.0, 'keep:V': 1.0, 'keep:V+R+K': 1.0}))
    assert t['per_anchor']['A']['D|L']['bases']['B1']['verdicts']['joint:V_vs_RK'] == 'refute'
    rep['joint'] = 'support and refute reachable'
    # Post family: retention after clean follow-up and the interaction flag.
    t = analyze_table(synthetic_table({'post:Wr': 0.1, 'post:Rd': 0.1, 'post:both': 0.3}))
    p = t['per_anchor']['A']['D|post11']['bases']['B2']
    assert p['verdict_effect_survives_clean_followup'] == 'support' and p['interaction_negligible'] is True, p
    t = analyze_table(synthetic_table({'post:Wr': 0.1, 'post:Rd': 0.1, 'post:both': 1.0}))
    p = t['per_anchor']['A']['D|post11']['bases']['B2']
    assert p['verdict_effect_survives_clean_followup'] == 'refute' and p['interaction_negligible'] is False, p
    rep['post'] = 'survive support/refute and interaction flag reachable'
    # Scope.
    t = analyze_table(synthetic_table({'scope:origin': 1.0, 'scope:later': 0.0}))
    v = t['per_anchor']['A']['S_fact|E']['bases']['B3']['verdicts']
    assert v['scope:origin_complete'] == 'support' and v['scope:later_complete'] == 'refute', v
    rep['scope'] = 'support and refute reachable'
    # Denominator rule: references equal -> no ratio.
    tb = synthetic_table({'remove:V': 1.0})
    for key in tb:
        tb[key]['ref']['01'] = dict(tb[key]['ref']['11'])
    t = analyze_table(tb)
    assert t['per_anchor']['A']['D|E']['cells']['remove:V']['per_base']['B0']['random_null']['note'] == 'denominator_unresolved'
    rep['denominator'] = 'unresolved denominators give no ratio'
    rep['status'] = 'passed'
    return rep


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    q = sub.add_parser('run')
    q.add_argument('run')
    q.add_argument('--out', required=True)
    sub.add_parser('selftest')
    a = p.parse_args()
    print(json.dumps(run(a.run, a.out) if a.cmd == 'run' else selftest(), ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
