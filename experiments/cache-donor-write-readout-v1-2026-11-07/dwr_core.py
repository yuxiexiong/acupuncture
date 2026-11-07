"""Frozen DWR estimands and decisions. Six-scene paired bootstrap via unchanged SPF."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'cache-selection-precedence-v1-2026-11-06'))
import spf_core as S
M = S.M
MAIN, SECOND, DIRS = S.MAIN, S.SECOND, S.DIRS
USES = {'D': (1, 0), 'E': (0, 1), 'DE': (1, 1)}
DONOR_ARMS = ('L11d', 'gainD', 'gainE', 'gainDE', 'withdrawD', 'withdrawE', 'withdrawDE')
ARMS = ('L11o',) + DONOR_ARMS


def level(b):
    if b is None or b['lo'] == b['hi'] == M:
        return 'indeterminate'
    return 'holds' if b['lo'] >= M else 'below' if b['hi'] < M else 'indeterminate'


def decision(g, w, recovery, valid_gain, valid_withdraw):
    lg, lw = level(g), level(w)
    if not valid_gain or not valid_withdraw:
        return 'delivery_confounded'
    if lg == lw == 'holds' and recovery['lo'] > 0:
        return 'bidirectional_same_endpoint'
    if lg == 'holds':
        return 'conditional_gain'
    if lw == 'holds':
        return 'self_recovery_without_gain' if recovery['lo'] > 0 else 'transfer_loss_without_self_recovery'
    if g['hi'] < 0 or w['hi'] < 0:
        return 'opposite_direction'
    return 'below_margin' if lg == lw == 'below' else 'indeterminate'


def evaluate(outputs, tables, clusters, self_row, n_boot=10000, n_perm=2000):
    assert set(outputs) == set(ARMS)
    cells, self_conflict, valid, pairs = {}, {}, {}, {}
    for a, arm in outputs.items():
        assert set(arm) == set(tables)
        assert all(set(arm[r]) == {d['id'] for d in tables[r]} for r in arm), 'missing donor output'
        cells[a] = S.cell(arm, tables, clusters, self_row, n_boot, n_perm)
        assert all(v is not None for v in cells[a]['per_receiver'].values()), 'unidentified D_tr'
        vals = [o for rd in arm.values() for o in rd.values()]
        valid[a] = sum(o in (0, 1, 2) for o in vals) / len(vals)
        self_conflict[a], pairs[a] = {}, {}
        for r in arm:
            ds = [d for d in tables[r] if d['type'] in ('AL', 'BD')]
            assert ds
            pairs[a][r] = {d['id']: int(arm[r][d['id']] == self_row[r]) for d in ds}
            self_conflict[a][r] = sum(pairs[a][r].values()) / len(ds)
    out = {}
    for j in USES:
        g, w = 'gain' + j, 'withdraw' + j
        G = S.boot(S.diff(cells[g]['per_receiver'], cells['L11o']['per_receiver']), clusters, n_boot)
        W = S.boot(S.diff(cells['L11d']['per_receiver'], cells[w]['per_receiver']), clusters, n_boot)
        guard_g = valid[g] >= .9 and valid['L11o'] - valid[g] <= .05 + 1e-12
        guard_w = valid[w] >= .9 and valid['L11d'] - valid[w] <= .05 + 1e-12
        changes = {r: {d: pairs[w][r][d] - pairs['L11d'][r][d] for d in pairs[w][r]} for r in pairs[w]}
        rvals = {r + '|' + d: v for r, ds in changes.items() for d, v in ds.items()}
        rclusters = {r + '|' + d: clusters[r] for r, ds in changes.items() for d in ds}
        R = S.boot(rvals, rclusters, n_boot)
        out[j] = {'G': G, 'W': W, 'R': R, 'G_level': level(G), 'W_level': level(W),
                  'gain_delivery': guard_g, 'withdraw_delivery': guard_w,
                  'recovery_pairs': changes, 'recovery_n': sum(map(len, changes.values())),
                  'recovery_raw_change': sum(sum(x.values()) for x in changes.values()),
                  'decision': decision(G, W, R, guard_g, guard_w)}
    contrast = {
        'G_D_minus_E': S.boot(S.diff(cells['gainD']['per_receiver'], cells['gainE']['per_receiver']), clusters, n_boot),
        'W_D_minus_E': S.boot(S.diff(cells['withdrawE']['per_receiver'], cells['withdrawD']['per_receiver']), clusters, n_boot)}
    return {'uses': out, 'valid_all_pairs': valid, 'cells': {a: {k: v for k, v in c.items() if k != 'per_receiver'} for a, c in cells.items()},
            'paired_comparison': contrast}
