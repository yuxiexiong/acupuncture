import json
import sys
d = json.load(open(sys.argv[1]))


def f(b):
    return 'None' if b is None else f"{b['mean']:+.3f} [{b['lo']:+.3f},{b['hi']:+.3f}] p={b['perm_p']:.3f} n={b['n']}/{b['clusters']}cl"


for dirn, x in d['directions'].items():
    dc = x['decision']
    print('=====', dirn, dc['outcome'])
    print('Y', dc['Y'])
    print('conflict', {k: f(v) for k, v in dc['conflict'].items()})
    print('interaction', f(dc['interaction']), '| perm_null_hi', round(dc['perm_null_hi'], 3))
    for arm, c in x['cells'].items():
        pn = c['perm_null']
        print(f"  {arm:14s} D_tr {f(c['D_tr'])} | eff {c['effect']:13s} tag {c['tag']:12s} y_self {c['y_self']:.3f} open {c['open']:.3f} first|self!=0 {c['first_when_self_not_first']:.3f}"
              f" | D_rk {f(c['D_rk'])} | D_ks {f(c['D_ks'])} | D_rs {f(c['D_rs'])} | D_os {f(c['D_os'])}" + (f" | null hi {pn['hi']:.3f}" if pn else ''))
    print('  categories:')
    for arm, c in x['categories'].items():
        print(f"    {arm:14s} {c}")
    print('  correct by self row:', x['correct_by_self_row'])
    print('  cell d w/o seen pairs', f(x['D_tr_cell_d_without_seen_pairs']), '| self rate on same-key donors (cell d)', round(x['self_rate_on_same_key_donors_cell_d'], 3))
