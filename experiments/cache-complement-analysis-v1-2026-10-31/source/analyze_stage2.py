"""Contract draft-r02 §5-§9: G all-layer difference, selection rules, II-A map, II-B tests. CPU only.

python analyze_stage2.py selftest
python analyze_stage2.py audit AUDIT_RUN LABELS_JSON|- OUT_JSON
python analyze_stage2.py g G_RUN OUT_JSON                       (development or history panel)
python analyze_stage2.py lock-g G_DEV_ANALYSIS G_DEV_VERIFICATION OUT_LOCK
python analyze_stage2.py a G_DEV_RUN A_RUN G_LOCK OUT_JSON
python analyze_stage2.py lock-a A_ANALYSIS G_LOCK OUT_LOCK
python analyze_stage2.py b B_RUN A_LOCK OUT_JSON
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import statistics
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location('readout_analyze', HERE.parent / 'early-stop-knowledge-readout-v1-2026-10-29/analyze.py')
readout = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(readout)
signflip_p = readout.signflip_p  # exact: all 2^n sign patterns, one-sided, p = share with mean >= observed

COMPONENTS = ('kv', 'recurrent', 'conv')
G_CODES = ('TTT', 'CCC', 'CTT', 'TCT', 'TTC', 'TCC', 'CTC', 'CCT')
SUBSETS = ('kv', 'recurrent', 'conv', 'kv+recurrent', 'kv+conv', 'recurrent+conv', 'kv+recurrent+conv')
JOINT = 'kv+recurrent+conv'
WINDOWS = {'early': (0, 1, 2, 3), 'mid': (12, 13, 14, 15), 'late': (24, 25, 26, 27)}
READOUTS = ('stop', 'fact')
ALPHA = 0.05
BOOTSTRAP = 10_000
ANALYSIS_SEED = 20261030
SMALL_DENOMINATOR = 2.0  # nats; clean S below this is pre-flagged, never dropped from the main analysis
CCC = ('clean', 'all:CCC')


# ---------------------------------------------------------------- readouts

def parse_condition(cid):
    _, layer, channel, dose = cid.split('_')
    return int(layer[1:]), int(channel[1:]), float(dose[1:])


def bases_of(items):
    bases = {}
    for iid, it in items.items():
        bases.setdefault(it['base_id'], {})[it['target_index']] = iid
    assert all(set(v) == {0, 1} for v in bases.values()), 'each base needs both facts'
    return dict(sorted(bases.items()))


def S_by_base(cells, items):
    """S(b) = [ll(A)-ll(B)] under the fact with A correct - [ll(A)-ll(B)] under the fact with B correct."""
    out = {}
    for b, t in bases_of(items).items():
        a, c = cells[t[0]]['lls'], cells[t[1]]['lls']
        out[b] = (a[0] - a[1]) - (c[0] - c[1])
    return out


def D_by_base(cells, items):
    """First-step stop advantage D, the two facts of each base weighted equally."""
    return {b: (cells[t[0]]['D'] + cells[t[1]]['D']) / 2 for b, t in bases_of(items).items()}


READER = {'stop': D_by_base, 'fact': S_by_base}


def cell(table, condition, arm):
    key = CCC if arm == 'all:CCC' else (condition, arm)
    assert key in table, f'missing cell {key}'
    return table[key]


def effect(table, items, readout, condition, arm, direction='clean'):
    """Positive = expected direction (§9). stop clean D(T)-D(arm), pollute D(arm)-D(C);
    fact clean S(arm)-S(T), pollute S(C)-S(arm)."""
    x = READER[readout](cell(table, condition, arm), items)
    ref = READER[readout](cell(table, condition, 'all:TTT' if direction == 'clean' else 'all:CCC'), items)
    sign = (1 if direction == 'pollute' else -1) * (1 if readout == 'stop' else -1)
    return {b: sign * (x[b] - ref[b]) for b in x}


def damage(table, items, readout, condition):
    """Absolute anomaly of the fully polluted cache: stop D(TTT)-D(CCC), fact S(CCC)-S(TTT)."""
    return effect(table, items, readout, condition, 'all:CCC', 'clean')


def ratio_R(table, items, condition, arm):
    s, clean = S_by_base(cell(table, condition, arm), items), S_by_base(cell(table, None, 'all:CCC'), items)
    small = sorted(b for b in clean if clean[b] < SMALL_DENOMINATOR)
    terms = {b: s[b] / clean[b] for b in s}
    kept = [terms[b] for b in terms if b not in small]
    return {'R': statistics.median(terms.values()), 'small_denominator_bases': small,
            'R_excluding_small': statistics.median(kept) if kept else None, 'remaining_bases': len(kept)}


def stop_summary(cells):
    return {'n': len(cells), 'first_step_eos': sum(c['first_step_eos'] for c in cells.values()),
            'truncated': sum(c['truncated'] for c in cells.values()),
            'mean_generated_tokens': statistics.fmean(c['generated_tokens'] for c in cells.values()),
            'nonempty_answers': sum(c['delivered_nonempty'] for c in cells.values())}


# ---------------------------------------------------------------- statistics

_INDEX = {}


def bootstrap_ci(values, n=BOOTSTRAP, seed=ANALYSIS_SEED):
    """Percentile 95% interval of the base-level mean. One fixed index matrix per panel size (seed 20261030),
    so every comparison is resampled over the same base draws."""
    k = len(values)
    if k not in _INDEX:
        _INDEX[k] = np.random.default_rng(seed).integers(0, k, size=(n, k))
    means = np.sort(np.asarray(values, dtype=float)[_INDEX[k]].mean(axis=1))
    return [float(means[int(0.025 * n)]), float(means[int(0.975 * n) - 1])]


def describe(by_base):
    v = [by_base[b] for b in sorted(by_base)]
    return {'by_base': dict(sorted(by_base.items())), 'mean': statistics.fmean(v), 'median': statistics.median(v),
            'n_positive': sum(x > 0 for x in v), 'n': len(v), 'ci95_bootstrap': bootstrap_ci(v)}


def holm(pvalues, alpha=ALPHA):
    """Holm step-down; returns {id: (adjusted p, rejected)}."""
    order = sorted(pvalues, key=lambda k: (pvalues[k], k))
    m, running, out = len(order), 0.0, {}
    for i, k in enumerate(order):
        running = max(running, min(1.0, (m - i) * pvalues[k]))
        out[k] = (running, running <= alpha)
    return out


def interactions(E):
    """E: {frozenset(classes): {base: effect}} for all seven non-empty subsets, on one background (§9).
    Second order E(X+Y)-E(X)-E(Y); third order by inclusion-exclusion over the eight combinations."""
    out = {}
    for x, y in combinations(COMPONENTS, 2):
        xy = E[frozenset((x, y))]
        out[f'{x}+{y}'] = {b: xy[b] - E[frozenset((x,))][b] - E[frozenset((y,))][b] for b in xy}
    full = E[frozenset(COMPONENTS)]
    out[JOINT] = {b: full[b] - sum(E[frozenset(p)][b] for p in combinations(COMPONENTS, 2))
                  + sum(E[frozenset((c,))][b] for c in COMPONENTS) for b in full}
    return {k: describe(v) for k, v in out.items()}


def cleaned_of_code(code):
    return frozenset(c for c, letter in zip(COMPONENTS, code) if letter == 'C')


def max_signflip_p(vectors):
    """Selection-aware null for a pick of the maximum: exact one-sided sign flip of max_k mean(signs * v_k),
    the same 2^n sign pattern applied to every candidate so their correlation is kept."""
    v = np.asarray(vectors, dtype=float)  # (candidates, bases)
    n = v.shape[1]
    signs = 1 - 2 * ((np.arange(2 ** n)[:, None] >> np.arange(n)) & 1)  # (2^n, n); row 0 = identity
    stats = (signs @ v.T / n).max(axis=1)
    return float((stats >= stats[0] - 1e-12).mean())


def anomaly_flags(desc, p_selection, readout, eos=None):
    """Selection labels (§6-§7): picked regardless of these flags; flagged when no anomaly/improvement is shown.
    The calibrated null is the max-statistic sign flip over all candidates of the pick, never a bare sign of the mean."""
    flags = []
    if desc['mean'] <= 0:
        flags.append('non_positive_mean')
    if p_selection >= ALPHA:
        flags.append('not_beyond_selection_null')
    if readout == 'stop' and eos is not None and eos == 0:
        flags.append('no_first_step_eos')
    return flags


# ---------------------------------------------------------------- G (§4-§6)

def g_analysis(table, items, structures=None):
    conds = sorted({c for c, a in table if c != 'clean'}, key=parse_condition)
    per = {}
    for c in conds:
        row = {'layer': parse_condition(c)[0], 'stop': {'TTT': stop_summary(cell(table, c, 'all:TTT'))}, 'arms': {}}
        for r in READOUTS:
            row[f'damage_{r}'] = describe(damage(table, items, r, c))
        for code in G_CODES[1:]:
            arm = f'all:{code}'
            row['arms'][code] = {r: describe(effect(table, items, r, c, arm)) for r in READOUTS}
            row['arms'][code]['R'] = ratio_R(table, items, c, arm)
            row['arms'][code]['stop_summary'] = stop_summary(cell(table, c, arm))
        row['R_TTT'] = ratio_R(table, items, c, 'all:TTT')
        E = {r: {cleaned_of_code(code): effect(table, items, r, c, f'all:{code}') for code in G_CODES[1:]} for r in READOUTS}
        row['interactions'] = {r: interactions(E[r]) for r in READOUTS}
        if structures and c in structures:
            row['structure'] = structures[c]
        per[c] = row
    windows = {}
    for w, layers in WINDOWS.items():
        in_w = [c for c in conds if parse_condition(c)[0] in layers]
        windows[w] = {'conditions': in_w}
        for sign, chosen in (('all', in_w), ('positive', [c for c in in_w if parse_condition(c)[2] > 0]),
                             ('negative', [c for c in in_w if parse_condition(c)[2] < 0])):
            if not chosen:
                continue
            res = {}
            for r in READOUTS:
                for arm in ('damage',) + G_CODES[2:]:
                    vals = [damage(table, items, r, c) if arm == 'damage' else effect(table, items, r, c, f'all:{arm}') for c in chosen]
                    res[f'{r}:{arm}'] = describe({b: statistics.fmean(v[b] for v in vals) for b in vals[0]})
            windows[w][sign] = res
    return {'conditions': per, 'windows': windows,
            'clean': {'stop': stop_summary(cell(table, None, 'all:CCC')), 'S': S_by_base(cell(table, None, 'all:CCC'), items)}}


def g_selection(table, items):
    """§6: per window, the condition with the largest stop-advantage increase and the one with the largest fact
    sensitivity loss; exact ties -> smaller layer, smaller channel, negative sign first."""
    conds = sorted({c for c, a in table if c != 'clean'}, key=parse_condition)
    roles, details = {}, {}
    for w, layers in WINDOWS.items():
        in_w = [c for c in conds if parse_condition(c)[0] in layers]
        assert in_w, f'no conditions in window {w}'
        for r in READOUTS:
            scores = {c: statistics.fmean(damage(table, items, r, c).values()) for c in in_w}
            best = sorted(in_w, key=lambda c: (-scores[c], *parse_condition(c)))[0]
            desc = describe(damage(table, items, r, best))
            eos = stop_summary(cell(table, best, 'all:TTT'))['first_step_eos']
            vecs = [[v for _, v in sorted(damage(table, items, r, c).items())] for c in in_w]
            p_sel = max_signflip_p(vecs)
            roles[f'{w}:{r}'] = best
            details[f'{w}:{r}'] = {'condition': best, 'scores': scores, 'damage': desc, 'TTT_first_step_eos': eos,
                                   'p_selection_adjusted': p_sel, 'flags': anomaly_flags(desc, p_sel, r, eos),
                                   'note': 'extreme of the window; not a window average'}
    return roles, details


# ---------------------------------------------------------------- II-A (§7)

def a_analysis(table, items, selection):
    by_cond = {}
    for role, cid in selection.items():
        by_cond.setdefault(cid, []).append(role)
    out = {'map': {}, 'candidates': {}, 'candidate_details': {}}
    for cid, roles in sorted(by_cond.items()):
        cmap = {}
        for g in range(8):
            grp = {s: {r: describe(effect(table, items, r, cid, f'grp{g}:{s}:clean')) for r in READOUTS} for s in SUBSETS}
            E = {r: {frozenset(s.split('+')): effect(table, items, r, cid, f'grp{g}:{s}:clean') for s in SUBSETS} for r in READOUTS}
            grp['interactions'] = {r: interactions(E[r]) for r in READOUTS}
            cmap[g] = grp
        out['map'][cid] = {'roles': roles, 'groups': cmap, 'damage': {r: describe(damage(table, items, r, cid)) for r in READOUTS}}
        for role in roles:
            r = role.split(':')[1]
            scores = {g: statistics.fmean(effect(table, items, r, cid, f'grp{g}:{JOINT}:clean').values()) for g in range(8)}
            g_best = sorted(range(8), key=lambda g: (-scores[g], g))[0]
            desc = cmap[g_best][JOINT][r]
            p_sel = max_signflip_p([[v for _, v in sorted(effect(table, items, r, cid, f'grp{g}:{JOINT}:clean').items())] for g in range(8)])
            out['candidates'][role] = {'condition_id': cid, 'group': g_best}
            out['candidate_details'][role] = {'scores': scores, 'improvement': desc, 'p_selection_adjusted': p_sel,
                                              'flags': anomaly_flags(desc, p_sel, r)}
    return out


# ---------------------------------------------------------------- II-B (§8-§9)

def b_analysis(table, items, candidates):
    tests, pvalues, explore = {}, {}, {}
    for role, cand in sorted(candidates.items()):
        cid, g, r = cand['condition_id'], cand['group'], role.split(':')[1]
        for d in ('clean', 'pollute'):
            tid = f'{role}|grp{g}:{JOINT}:{d}'
            values = effect(table, items, r, cid, f'grp{g}:{JOINT}:{d}', d)
            pvalues[tid] = signflip_p([values[b] for b in sorted(values)])
            tests[tid] = {'role': role, 'condition_id': cid, 'group': g, 'readout': r, 'direction': d,
                          'p_one_sided': pvalues[tid], **describe(values)}
        ex = {'anomaly_on_new_panel': {x: describe(damage(table, items, x, cid)) for x in READOUTS}}
        for d in ('clean', 'pollute'):
            ex[d] = {s: {x: describe(effect(table, items, x, cid, f'grp{g}:{s}:{d}', d)) for x in READOUTS} for s in SUBSETS}
            E = {x: {frozenset(s.split('+')): effect(table, items, x, cid, f'grp{g}:{s}:{d}', d) for s in SUBSETS} for x in READOUTS}
            ex[d]['interactions'] = {x: interactions(E[x]) for x in READOUTS}
        explore[role] = ex
    assert 0 < len(pvalues) <= 12, len(pvalues)
    for tid, (adj, rej) in holm(pvalues).items():
        tests[tid].update(p_holm=adj, rejected_holm=rej, verdict='detected_in_panel' if rej else 'insufficient_evidence')
    conds = sorted({c['condition_id'] for c in candidates.values()})
    return {'tests': tests, 'family_alpha': ALPHA, 'm': len(pvalues), 'exploratory': explore,
            'globals': g_analysis({k: v for k, v in table.items() if k[0] in conds or k == CCC}, items)['conditions']}


def audit_verdict(table, items, labels=None):
    """§3 clean audit of the new panel: 24/24 correct core without core contradiction, clean S > 0 per base."""
    clean = S_by_base(cell(table, None, 'all:CCC'), items)
    s_ok = all(v > 0 for v in clean.values())
    out = {'clean_S': clean, 'all_bases_positive': s_ok,
           'small_denominator_bases': sorted(b for b, v in clean.items() if v < SMALL_DENOMINATOR)}
    if labels is None:
        out['status'] = 'awaiting_reading' if s_ok else 'failed'
        return out
    assert set(labels) == set(items), 'labels must cover every input'
    core = [iid for iid, lab in labels.items() if lab['core'] != 'correct' or lab['core_contradiction']]
    out['inputs_failing_core'] = sorted(core)
    out['status'] = 'passed' if s_ok and not core else 'failed'
    return out


# ---------------------------------------------------------------- IO

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_run(run, table=None, items=None, keep=None):
    """Verified records -> table {(condition, arm): {item_id: cell}}; keep filters (condition, arm) keys."""
    run, table, items = Path(run), {} if table is None else table, {} if items is None else items
    records, structures, identity = 0, {}, {}
    receipts = sorted(run.glob('worker-*/receipt.json'))
    assert receipts, f'no worker receipts under {run}'
    for receipt in receipts:
        for rel, digest in json.loads(receipt.read_text())['record_hashes'].items():
            path = receipt.parent / rel
            assert sha(path) == digest, rel
            r = json.loads(path.read_text())
            key = (r['spec']['condition_id'], r['spec']['arm'])
            if keep is not None and not keep(key):
                continue
            records += 1
            items[r['item']['id']] = r['item']
            identity[r['item']['id']] = (r['reference_sha256'], r['prompt_token_sha256'], r['freeze_sha256'])
            g = r['generation']
            table.setdefault(key, {})[r['item']['id']] = {
                'lls': [c['loglikelihood'] for c in r['candidates']], 'D': g['readouts'][0]['stop_advantage'],
                'first_step_eos': g['first_step_eos'], 'truncated': g['truncated'],
                'generated_tokens': g['generated_tokens'], 'delivered_nonempty': g['delivered_nonempty']}
        for cache in sorted(receipt.parent.glob('caches/*.json')):
            cid = cache.stem.split('__')[1]
            s = json.loads(cache.read_text())['structure']
            structures.setdefault(cid, []).append({c: {'downstream_layers': len(s['downstream_layers'][c]),
                'differing_layers': len(s['differing_layers'][c]),
                'diff_norm_sum': sum(x['diff_norm'] for x in s['rows'] if x['component'] == c)} for c in COMPONENTS})
    return table, items, records, structures, identity


def write(out, value):
    with open(out, 'x') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return value


def scripts():
    return {p.name: sha(p) for p in (HERE / 'analyze_stage2.py', HERE / 'stage2.py')}


def utc():
    return datetime.now(timezone.utc).isoformat()


def cmd_audit(run, labels, out):
    table, items, n, _, _ = load_run(run)
    lab = None if labels == '-' else json.loads(Path(labels).read_text())
    return write(out, {'records': n, 'run': str(run), **audit_verdict(table, items, lab)})


def cmd_g(run, out):
    table, items, n, structures, _ = load_run(run)
    roles, details = g_selection(table, items)
    return write(out, {'records': n, 'run': str(run), 'scripts': scripts(), **g_analysis(table, items, structures),
                       'selection': roles, 'selection_details': details})


def cmd_lock_g(analysis, verification, out):
    a = json.loads(Path(analysis).read_text())
    assert not list((HERE / 'runs').glob('a_*')) and not list((HERE / 'runs').glob('b_*')), 'stage-II outputs exist'
    assert json.loads(Path(verification).read_text())['status'] == 'passed'
    return write(out, {'status': 'locked', 'selection': a['selection'], 'selection_details': a['selection_details'],
                       'g_analysis_sha256': sha(analysis), 'g_development_verification_sha256': sha(verification),
                       'scripts': scripts(), 'stage_two_outputs_previously_unseen': True, 'locked_at': utc()})


def cmd_a(g_run, a_run, g_lock, out):
    lock = json.loads(Path(g_lock).read_text())
    assert lock['status'] == 'locked' and lock['scripts'] == scripts(), 'scripts changed since the G lock'
    conds = set(lock['selection'].values())
    # §11: TTT/CCC references are reused from G development, never regenerated; identities must agree.
    table, items, n_g, _, id_g = load_run(g_run, keep=lambda k: k == CCC or (k[0] in conds and k[1] == 'all:TTT'))
    table, items, n_a, _, id_a = load_run(a_run, table, items)
    assert set(id_a) <= set(id_g) and all(id_a[i] == id_g[i] for i in id_a), 'reused G records differ in identity'
    return write(out, {'records': {'g_reused': n_g, 'a': n_a}, 'g_lock_sha256': sha(g_lock), 'scripts': scripts(),
                       **a_analysis(table, items, lock['selection'])})


def cmd_lock_a(analysis, g_lock, out):
    a = json.loads(Path(analysis).read_text())
    assert not list((HERE / 'runs').glob('b_*')), 'II-B outputs exist; candidates can no longer be locked'
    assert a['g_lock_sha256'] == sha(g_lock)
    return write(out, {'status': 'locked', 'candidates': a['candidates'], 'candidate_details': a['candidate_details'],
                       'a_analysis_sha256': sha(analysis), 'g_lock_sha256': sha(g_lock), 'scripts': scripts(),
                       'validation_outputs_previously_unseen': True, 'locked_at': utc()})


def cmd_b(run, a_lock, out):
    lock = json.loads(Path(a_lock).read_text())
    assert lock['status'] == 'locked' and lock['scripts'] == scripts(), 'scripts changed since the A lock'
    table, items, n, _, _ = load_run(run)
    return write(out, {'records': n, 'a_lock_sha256': sha(a_lock), **b_analysis(table, items, lock['candidates'])})


# ---------------------------------------------------------------- synthetic rehearsal (contract §12; CLAUDE.md §6.2)

def synthetic_items(prefix='B'):
    return {f'{prefix}{b:02d}-f{t}': {'id': f'{prefix}{b:02d}-f{t}', 'base_id': f'{prefix}{b:02d}', 'target_index': t}
            for b in range(12) for t in (0, 1)}


def synthetic_cells(items, rng, present_stop, present_fact, mag):
    """present_*: share of the condition's anomaly present in this cell (0 = clean, 1 = fully polluted)."""
    return {iid: {'lls': [mag[it['base_id']] * (1 - present_fact) * (1 if it['target_index'] == 0 else -1) / 2 + rng.normal(0, .2), 0.0],
                  'D': -4 + 8 * present_stop + rng.normal(0, .5), 'first_step_eos': present_stop > .5, 'truncated': False,
                  'generated_tokens': 1 if present_stop > .5 else 20, 'delivered_nonempty': present_stop <= .5}
            for iid, it in items.items()}


def synthetic_table(items, conds, world, locals_=(), seed=1):
    """world(cond, group, classes, background) -> (present_stop, present_fact); group None for G codes."""
    rng = np.random.default_rng(seed)
    mag = {it['base_id']: float(rng.uniform(1.5, 12)) for it in items.values()}
    table = {CCC: synthetic_cells(items, rng, 0, 0, mag)}
    for c in conds:
        for code in G_CODES[1:] + ('TTT',):
            if code != 'CCC':
                table[(c, f'all:{code}')] = synthetic_cells(items, rng, *world(c, None, cleaned_of_code(code), 'T'), mag)
    for c, g, d in locals_:
        for s in SUBSETS:
            table[(c, f'grp{g}:{s}:{d}')] = synthetic_cells(items, rng, *world(c, g, frozenset(s.split('+')), 'T' if d == 'clean' else 'C'), mag)
    return table


def g_world(strength):
    """Stop is lifted by cleaning either linear class; fact half by KV and half by recurrent (stage-1 shape)."""
    def world(c, g, classes, bg):
        m = strength(c)
        stop = 0.0 if ('recurrent' in classes or 'conv' in classes) else 1.0
        fact = 1 - 0.5 * ('kv' in classes) - 0.5 * ('recurrent' in classes)
        return m[0] * stop, m[1] * fact
    return world


def depth_world(stop_group, fact_group, effective=True):
    def world(c, g, classes, bg):
        if g is None:
            return (0.0, 0.0) if classes == frozenset(COMPONENTS) else (1.0, 1.0)
        hit_s = effective and g == stop_group and ('recurrent' in classes or 'conv' in classes)
        hit_f = effective and g == fact_group and 'kv' in classes and 'recurrent' in classes
        if bg == 'T':  # local clean from polluted background
            return (0.0 if hit_s else 1.0), (0.1 if hit_f else 1.0)
        return (1.0 if hit_s else 0.0), (0.9 if hit_f else 0.0)
    return world


def selftest():
    assert abs(signflip_p([1.0] * 12) - 1 / 4096) < 1e-15 and signflip_p([-1.0] * 12) == 1.0
    h = holm({'a': .01, 'b': .04, 'c': .03, 'd': .005})
    assert [h[k][1] for k in 'abcd'] == [True, False, False, True] and abs(h['c'][0] - .06) < 1e-12
    assert bootstrap_ci([1.0, 2.0, 3.0]) == bootstrap_ci([1.0, 2.0, 3.0])
    # max-statistic null reduces to the single sign flip for one candidate; positive maxima of all-positive rows hit 1/4096
    rv = list(np.random.default_rng(0).normal(0, 1, 12))
    assert abs(max_signflip_p([rv]) - signflip_p(rv)) < 1e-12 and max_signflip_p([[1.0] * 12, [0.5] * 12]) == 1 / 4096
    # interactions: additive -> 0, pure synergy -> positive second and third order
    base = {'b': 0.0}
    add = {frozenset(s.split('+')): {'b': float(len(s.split('+')))} for s in SUBSETS}
    assert all(abs(v['mean']) < 1e-12 for v in interactions(add).values())
    syn = {k: (dict(base) if len(k) < 3 else {'b': 1.0}) for k in add}
    assert interactions(syn)[JOINT]['mean'] == 1.0
    # G: 64 conditions, designated winners per window; tie rule layer < channel < negative sign
    sys.path.insert(0, str(HERE))
    import stage2
    conds = [c['id'] for c in stage2.g_conditions()]
    stop_win = {'early': 'N_L02_C5251_D-1', 'mid': 'N_L13_C248_D+1', 'late': 'N_L26_C7907_D-1'}
    fact_win = {'early': 'N_L00_C4146_D+1', 'mid': 'N_L15_C7988_D-1', 'late': 'N_L24_C3721_D+1'}
    strength = lambda c: (1.0 if c in stop_win.values() else .4, 1.0 if c in fact_win.values() else .4)
    items = synthetic_items()
    gt = synthetic_table(items, conds, g_world(strength))
    roles, details = g_selection(gt, items)
    assert roles == {**{f'{w}:stop': c for w, c in stop_win.items()}, **{f'{w}:fact': c for w, c in fact_win.items()}}, roles
    assert all(not d['flags'] for d in details.values())
    ga = g_analysis(gt, items)
    early = ga['conditions']['N_L02_C5251_D-1']
    assert early['arms']['TCT']['stop']['mean'] > 3 and abs(early['arms']['CTT']['stop']['mean']) < 1
    assert early['interactions']['stop']['recurrent+conv']['mean'] < -3  # either class suffices: negative 2nd order
    # null G world: selection still follows the rule, every role flagged
    gn = synthetic_table(items, conds, g_world(lambda c: (0.0, 0.0)), seed=2)
    nroles, ndetails = g_selection(gn, items)
    assert len(nroles) == 6 and all(d['flags'] for d in ndetails.values()), ndetails
    # tie rule: identical tables for two conditions -> smaller layer, then negative sign
    tie = {CCC: gt[CCC]}
    for c in ('N_L01_C2765_D+1', 'N_L01_C2765_D-1', 'N_L03_C7666_D-1'):
        for code in G_CODES:
            if code != 'CCC':
                tie[(c, f'all:{code}')] = gt[('N_L02_C5251_D-1', f'all:{code}')]
    troles, _ = g_selection({**tie, **{k: v for k, v in gt.items() if k[0] not in ('N_L01_C2765_D+1', 'N_L01_C2765_D-1', 'N_L03_C7666_D-1', 'N_L02_C5251_D-1')}}, items)
    assert troles['early:stop'] == 'N_L01_C2765_D-1', troles
    # II-A: designated groups win; null depth world flags every candidate
    sel = roles
    sconds = sorted(set(sel.values()))
    at = synthetic_table(items, sconds, depth_world(2, 5), [(c, g, 'clean') for c in sconds for g in range(8)], seed=3)
    a = a_analysis(at, items, sel)
    assert all(a['candidates'][r]['group'] == (2 if r.endswith('stop') else 5) for r in sel), a['candidates']
    an = a_analysis(synthetic_table(items, sconds, depth_world(2, 5, False), [(c, g, 'clean') for c in sconds for g in range(8)], seed=4), items, sel)
    assert all(d['flags'] for d in an['candidate_details'].values())
    assert all(an['candidates'][r]['group'] == 0 or an['candidate_details'][r]['scores'][an['candidates'][r]['group']] >=
               max(an['candidate_details'][r]['scores'].values()) for r in sel)
    # II-B: the confirmatory family can be satisfied ...
    vitems = synthetic_items('V')
    cands = a['candidates']
    locs = sorted({(c['condition_id'], c['group'], d) for c in cands.values() for d in ('clean', 'pollute')})
    bt = synthetic_table(vitems, sconds, depth_world(2, 5), locs, seed=5)
    b = b_analysis(bt, vitems, cands)
    assert b['m'] == 12 and all(t['rejected_holm'] for t in b['tests'].values()), [t['p_holm'] for t in b['tests'].values()]
    # ... and not satisfied when the groups do nothing
    bn = b_analysis(synthetic_table(vitems, sconds, depth_world(2, 5, False), locs, seed=6), vitems, cands)
    assert not any(t['rejected_holm'] for t in bn['tests'].values())
    # clean audit both outcomes
    good = {iid: {'core': 'correct', 'core_contradiction': False} for iid in vitems}
    assert audit_verdict(bt, vitems, good)['status'] == 'passed'
    assert audit_verdict(bt, vitems)['status'] == 'awaiting_reading'
    assert audit_verdict(bt, vitems, dict(good, **{'V03-f1': {'core': 'other_fact', 'core_contradiction': False}}))['status'] == 'failed'
    flipped = dict(bt)
    flipped[CCC] = {iid: dict(c, lls=[-c['lls'][0], 0.0]) for iid, c in bt[CCC].items()}
    assert audit_verdict(flipped, vitems, good)['status'] == 'failed'
    r = ratio_R(bt, vitems, sconds[0], 'all:TTT')
    assert r['remaining_bases'] + len(r['small_denominator_bases']) == 12
    print('selftest passed', json.dumps({'g_roles': roles, 'a_candidates': cands, 'b_rejected': 12, 'b_null_rejected': 0}))


if __name__ == '__main__':
    cmd, args = sys.argv[1], sys.argv[2:]
    {'selftest': selftest, 'audit': cmd_audit, 'g': cmd_g, 'lock-g': cmd_lock_g, 'a': cmd_a, 'lock-a': cmd_lock_a,
     'b': cmd_b}[cmd](*args)
