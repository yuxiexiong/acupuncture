"""Post-hoc, descriptive (not pre-registered): what do the non-oracle buffer arms answer?  Reads FBR-01 stage-A formal records only."""
import glob, json, re, sys
sys.path.insert(0, '.')
CODE = re.compile(r'(?<![A-Za-z0-9])[A-Z][0-9]+(?![A-Za-z0-9])')
recs = {}
for f in sorted(glob.glob('runs/A-formal-r02/worker-*/records/*.json')):
    r = json.load(open(f)); recs[r['text']] = r
def out(nr):
    t = nr['text'].replace('<|im_end|>', '').replace('<|endoftext|>', '')
    c = list(dict.fromkeys(CODE.findall(t)))
    return c[0] if len(c) == 1 else ('STOP' if not c and nr['termination'] == 'stop' else 'OTHER')
def pos(it, code):
    return it['listed_codes'].index(code) if code in it['listed_codes'] else None
dirs = list(next(iter(recs.values()))['directions'])
for d in dirs:
    print('==', d)
    for arm in ('F_mean', 'F_one_o', 'F_one_s', 'VmK'):
        cat = {'target': 0, 'first_listed(not target)': 0, 'other_listed': 0, 'STOP': 0, 'OTHER': 0}
        bypos = {0: [0, 0], 1: [0, 0], 2: [0, 0]}       # receiver target position -> [correct, n]
        donor_entity = donor_position = n_dist = 0
        for i, r in recs.items():
            it = r['item']; o = out(r['directions'][d]['arms'][arm]['N'])
            tp = pos(it, it['target']); bypos[tp][1] += 1
            if o == it['target']:
                cat['target'] += 1; bypos[tp][0] += 1
            elif o == it['first_listed']:
                cat['first_listed(not target)'] += 1
            elif o in it['listed_codes']:
                cat['other_listed'] += 1
            else:
                cat[o] += 1
            if arm in ('F_one_s', 'F_one_o'):
                dn = recs[r['reference']['one_s' if arm == 'F_one_s' else 'one_o']]['item']
                dpos = pos(dn, dn['target'])
                code_at_dpos = it['listed_codes'][dpos]
                same_entity_code = dn['target'] if dn['target'] in it['listed_codes'] else None
                if arm == 'F_one_s' and same_entity_code is not None and same_entity_code != code_at_dpos:
                    n_dist += 1
                    donor_entity += int(o == same_entity_code); donor_position += int(o == code_at_dpos)
                elif arm == 'F_one_o':
                    n_dist += 1; donor_position += int(o == code_at_dpos)
        extra = ''
        if arm == 'F_one_s':
            extra = f' | where donor-entity and donor-position differ (n={n_dist}): answers donor ENTITY code {donor_entity}, code at donor POSITION {donor_position}'
        if arm == 'F_one_o':
            extra = f' | answers the code at the donor\'s target position: {donor_position}/{n_dist}'
        print(f'  {arm:8s}', cat, '| correct by receiver target position 1/2/3:', '/'.join(f'{a}of{b}' for a, b in bypos.values()), extra)
    dn = {recs[r['reference']['one_o']]['item']['listed_codes'].index(recs[r['reference']['one_o']]['item']['target']) for r in recs.values()}
    print('  F_one_o donors target positions (0-based):', dn)
