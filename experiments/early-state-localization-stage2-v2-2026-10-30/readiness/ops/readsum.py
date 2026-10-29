import json, collections
here='/workspace/acupuncture/experiments/early-state-localization-stage2-v2-2026-10-30/'
def load(name):
    out=collections.defaultdict(list)
    for r in json.load(open(here+f'reading/{name}/joined.json'))['rows']:
        cid=r['condition']['id'] if isinstance(r['condition'],dict) else r['condition']
        out[(cid, r['arm'])].append(r['label']['fact'])
    return out
def rate(v): c=collections.Counter(v); n=len(v); return f"follow {c['follows_fact']/n:4.0%} nodeliv {c['not_delivered']/n:4.0%} otherfact {c['other_fact']/n:4.0%} n={n}"
W={'early':(0,1,2,3),'mid':(12,13,14,15),'late':(24,25,26,27)}
lay=lambda c:int(c.split('_')[1][1:])
for name in ('g_history-r01','development-r01'):
    d=load(name); print('==',name)
    print('  clean CCC', rate(d[('clean','all:CCC')]))
    for w,ls in W.items():
        for arm in ('all:TTT','all:CTT','all:TCC'):
            v=[x for (c,a),xs in d.items() if c!='clean' and a==arm and lay(c) in ls for x in xs]
            print(f'  {w:5s} {arm}', rate(v))
lock=json.load(open(here+'readiness/a-lock-r01.json'))['candidates']
d=load('validation-r01'); print('== validation (II-B new items)'); print('  clean CCC', rate(d[('clean','all:CCC')]))
for role,c in sorted(lock.items()):
    cid,g=c['condition_id'],c['group']
    print(' ',role,cid,'grp',g)
    for arm in ('all:TTT',f'grp{g}:kv+recurrent+conv:clean',f'grp{g}:kv+recurrent+conv:pollute'):
        print('     ',arm.ljust(34),rate(d[(cid,arm)]))
