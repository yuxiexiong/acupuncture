"""CT-01 pure rules (CONTRACT.zh-CN.md r01).  Zero model calls.

Main: shared s0, q0 (C_native stop / non-stop winners) for all cells:  D = Q + A - B,
  Q = z(s0) - z(q0), A = max_stop - z(s0), B = max_nonstop - z(q0).  For every 2^3 recovery interaction,
  I_D = I_Q + I_A - I_B exactly (linear in the cell values).
Auxiliary (edge u -> v, n_u / n_v = non-stop winners):  D_v - D_u = d[max_stop - z(n_u)] - g,  g = z_v(n_v) - z_v(n_u) >= 0
  ("advantage of the new winner over the old one in v"; not 'the new token rose').  Both n_u and n_v tracked against s0.
"""
import re
import unicodedata

STOP = (248044, 248046)
CODES = {'X': '100', 'F': '010', 'H': '001', 'XF': '110', 'XH': '101', 'FH': '011', 'XFH': '111'}
ANSWER_RE = re.compile(r'目标条目\S*?编号为([A-Za-z0-9]+)')
CODE_RE = re.compile(r'编号为([A-Za-z0-9]+)')
CATEGORIES = ('special', 'clean_first_token', 'answer_overlap', 'distractor_overlap', 'whitespace_punct', 'lexical', 'uncertain')
RULE = {'scen_count': 5, 'dir_count': 3}


def answer_and_distractors(record_text):
    ans = ANSWER_RE.search(record_text).group(1)
    others = [c for c in CODE_RE.findall(record_text) if c != ans]
    return ans, others


def token_sets(tok, ans, others):
    def enc(s):
        return set(tok.encode(s, add_special_tokens=False)) | set(tok.encode(' ' + s, add_special_tokens=False))
    a = enc(ans)
    d = set().union(*[enc(o) for o in others]) - a if others else set()
    return a, d


def categorize(tid, text, special_ids, q0, ans_ids, dis_ids):
    """Frozen priority: special > clean first token > answer overlap > distractor overlap > whitespace/punct > lexical > uncertain."""
    if tid in special_ids:
        return 'special'
    if tid == q0:
        return 'clean_first_token'
    if tid in ans_ids:
        return 'answer_overlap'
    if tid in dis_ids:
        return 'distractor_overlap'
    if text is None or '�' in text:
        return 'uncertain'
    if text.strip() == '' or all(unicodedata.category(c)[0] in 'PSZC' for c in text):
        return 'whitespace_punct'
    if any(c.isalnum() for c in text):
        return 'lexical'
    return 'uncertain'


def cell_terms(z44, z46, za, D, s0):
    z = {STOP[0]: z44, STOP[1]: z46}
    smax = max(z.values())
    return {'D': D, 'Q': z[s0] - za, 'A': smax - z[s0], 'B': (smax - D) - za}


def interactions(vals):
    """vals: code -> value for '000'..'111' (bits X F H, 1 = restored).  R(A) = v(000) - v(A)."""
    R = {name: vals['000'] - vals[code] for name, code in CODES.items()}
    i_XF = R['XF'] - R['X'] - R['F']
    i_XH = R['XH'] - R['X'] - R['H']
    i_FH = R['FH'] - R['F'] - R['H']
    i_XFH = R['XFH'] - R['XF'] - R['XH'] - R['FH'] + R['X'] + R['F'] + R['H']
    return {'r_X': R['X'], 'r_F': R['F'], 'r_H': R['H'], 'i_XF': i_XF, 'i_XH': i_XH, 'i_FH': i_FH, 'i_XFH': i_XFH}


def decompose_interactions(terms_by_cell):
    """terms_by_cell: code -> {'D','Q','A','B'}.  Returns per-quantity interaction dicts and the closure error."""
    out = {q: interactions({c: t[q] for c, t in terms_by_cell.items()}) for q in ('D', 'Q', 'A', 'B')}
    err = max(abs(out['D'][k] - (out['Q'][k] + out['A'][k] - out['B'][k])) for k in out['D'])
    return out, err


def edge_aux(z_u, z_v, s0, n_u, n_v):
    """z_*: full logit vectors (indexable).  Advantage g of new over old winner in v, and both tracked against s0."""
    g = float(z_v[n_v] - z_v[n_u])
    old = float((z_v[s0] - z_v[n_u]) - (z_u[s0] - z_u[n_u]))
    new = float((z_v[s0] - z_v[n_v]) - (z_u[s0] - z_u[n_v]))
    return {'switched': n_u != n_v, 'new_over_old_advantage': g, 'd_s0_minus_old': old, 'd_s0_minus_new': new}


def scenario_pairs(values):
    out = {}
    for iid, v in values.items():
        s, f = iid.rsplit('-', 1)
        out.setdefault(s, {})[f] = v
    return {s: (d['f0'], d['f1']) for s, d in sorted(out.items())}


def prediction_direction(cats_by_input):
    """P_T: native T non-stop winner is whitespace_punct or special in both facts of >= 5/6 scenarios."""
    ok = {'whitespace_punct', 'special'}
    pairs = scenario_pairs({i: c in ok for i, c in cats_by_input.items()})
    n = sum(a and b for a, b in pairs.values())
    return n >= RULE['scen_count'], n
