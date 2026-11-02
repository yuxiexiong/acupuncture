"""NQ-01 frozen rules (plan v2 §4–§5).  Pure functions over per-cell classifications.

Cell output (from the frozen FC classifier): delivered = target present and no other distinct code; unique = the single distinct
code when exactly one is present, else None.
Scenario (9 cells) category: follow_query if >= 8 cells delivered; follow_first if >= 8 cells uniquely output the first-listed
code; follow_identity if >= 8 cells uniquely output one and the same code; else mixed.  (The three are mutually exclusive by
construction of the 3 cyclic orders x 3 queries: target and first-listed coincide in 3 cells, a fixed code is first-listed in 3.)
Direction label: a category held by >= 5/6 scenarios, else mixed.
Applicability: C scenario ok if >= 8/9 cells delivered; panel ok if >= 5/6 scenarios.  Damage transfer per direction: a scenario
counts if >= 6/9 cells have C delivered and T_nat not delivered; direction transferred if >= 4/6 scenarios.
Status of an arm for a category: not_applicable_baseline / not_applicable_damage / support / unsupported.
Overall: support in >= 3 of the fixed 4 directions.
"""
RULE = {'cell_count': 8, 'scen_count': 5, 'c_cell': 8, 'c_scen': 5, 'dmg_cell': 6, 'dmg_scen': 4, 'dir_count': 3}
CATS = ('follow_query', 'follow_first', 'follow_identity')


def scenario_category(cells):
    """cells: list of 9 dicts {'delivered': bool, 'unique': code|None, 'first_listed': code}."""
    assert len(cells) == 9
    if sum(c['delivered'] for c in cells) >= RULE['cell_count']:
        return 'follow_query'
    if sum(c['unique'] is not None and c['unique'] == c['first_listed'] for c in cells) >= RULE['cell_count']:
        return 'follow_first'
    codes = [c['unique'] for c in cells if c['unique'] is not None]
    if codes and max(codes.count(x) for x in set(codes)) >= RULE['cell_count']:
        return 'follow_identity'
    return 'mixed'


def direction_label(scen_cats):
    for cat in CATS:
        if sum(v == cat for v in scen_cats.values()) >= RULE['scen_count']:
            return cat
    return 'mixed'


def c_applicable(c_cells_by_scen):
    ok = {s: sum(c['delivered'] for c in cells) >= RULE['c_cell'] for s, cells in c_cells_by_scen.items()}
    return {'scenarios': ok, 'panel_ok': sum(ok.values()) >= RULE['c_scen']}


def damage_transfer(c_cells_by_scen, t_cells_by_scen):
    ok = {s: sum(c['delivered'] and not t['delivered'] for c, t in zip(c_cells_by_scen[s], t_cells_by_scen[s])) >= RULE['dmg_cell']
          for s in c_cells_by_scen}
    return {'scenarios': ok, 'transferred': sum(ok.values()) >= RULE['dmg_scen']}


def status(panel_ok, transferred, label, cat):
    if not panel_ok:
        return 'not_applicable_baseline'
    if not transferred:
        return 'not_applicable_damage'
    return 'support' if label == cat else 'unsupported'


def overall(statuses):
    n = sum(s == 'support' for s in statuses.values())
    return {'met': n >= RULE['dir_count'], 'n_support': n, 'of': len(statuses),
            'n_not_applicable': sum(s.startswith('not_applicable') for s in statuses.values())}


def paired_improvement(c_cells, t_cells, a_cells):
    return sum(c['delivered'] and not t['delivered'] and a['delivered'] for c, t, a in zip(c_cells, t_cells, a_cells))


def pairing(a_cells, b_cells):
    out = {'a_only': 0, 'b_only': 0, 'both': 0, 'neither': 0}
    for a, b in zip(a_cells, b_cells):
        x, y = a['delivered'], b['delivered']
        out['both' if x and y else 'a_only' if x else 'b_only' if y else 'neither'] += 1
    return out


def q_values(z_by_query):
    """z_by_query: queried letter -> {letter: diag score of that item's code second token} for one scenario/order/arm.
    Q_ij = ((z_i - z_j)[ask i] - (z_i - z_j)[ask j]) / 2 for pairs AB, AC, BC (descriptive only)."""
    out = {}
    for i, j in (('A', 'B'), ('A', 'C'), ('B', 'C')):
        out[i + j] = ((z_by_query[i][i] - z_by_query[i][j]) - (z_by_query[j][i] - z_by_query[j][j])) / 2
    return out
