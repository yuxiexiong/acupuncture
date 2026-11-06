"""Post-hoc, descriptive: single-donor arms, donor target position x receiver output position."""
import glob, json, re
CODE = re.compile(r'(?<![A-Za-z0-9])[A-Z][0-9]+(?![A-Za-z0-9])')
recs = {}
for f in sorted(glob.glob('runs/A-formal-r02/worker-*/records/*.json')):
    r = json.load(open(f)); recs[r['text']] = r
def outpos(it, nr):
    t = nr['text'].replace('<|im_end|>', '').replace('<|endoftext|>', '')
    c = list(dict.fromkeys(CODE.findall(t)))
    if len(c) == 1 and c[0] in it['listed_codes']: return it['listed_codes'].index(c[0])
    return 'x'
dirs = list(next(iter(recs.values()))['directions'])
for d in dirs:
    print('==', d)
    for arm, key in (('F_one_o', 'one_o'), ('F_one_s', 'one_s')):
        tab = {}
        for i, r in recs.items():
            it = r['item']; dn = recs[r['reference'][key]]['item']
            dp = dn['listed_codes'].index(dn['target']); rp = it['listed_codes'].index(it['target'])
            op = outpos(it, r['directions'][d]['arms'][arm]['N'])
            tab.setdefault((dp, rp), {}).setdefault(op, 0); tab[(dp, rp)][op] += 1
        print(' ', arm, '(donor target pos, receiver target pos) -> output pos counts')
        for k in sorted(tab): print('    ', k, dict(sorted(tab[k].items(), key=lambda kv: str(kv[0]))))
        # marginal: among receivers whose target pos != donor pos, output == donor pos vs == receiver pos vs == 0
        n = a = b = z = 0
        for (dp, rp), v in tab.items():
            if dp == rp: continue
            m = sum(v.values()); n += m; a += v.get(dp, 0); b += v.get(rp, 0); z += v.get(0, 0)
        print(f'     donor pos != receiver pos: n={n}, output=donor pos {a}, output=receiver target {b}, output=first {z}')
        n = a = 0
        for (dp, rp), v in tab.items():
            if dp == 0: continue
            n += sum(v.values()); a += v.get(dp, 0)
        print(f'     donor pos != first: n={n}, output=donor pos {a}')
