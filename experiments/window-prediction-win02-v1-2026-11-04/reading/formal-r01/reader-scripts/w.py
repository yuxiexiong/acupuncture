import json,sys
pk,out,tsv=sys.argv[1:4]
d=json.load(open(pk)); ids=[r['id'] for it in d['items'] for r in it['responses']]
rows=[]
for line in open(tsv,encoding='utf-8'):
    line=line.rstrip('\n')
    if not line: continue
    i,f,c,r,n=line.split('|')
    rows.append({"id":i,"fact":f,"contradiction":c=='1',"repetition":r=='1',"note":n})
assert [x['id'] for x in rows]==ids or sorted(x['id'] for x in rows)==sorted(ids), "id mismatch"
assert len(rows)==len(ids)==len(set(x['id'] for x in rows))
assert all(x['fact'] in {'follows_fact','other_fact','other_wrong','not_delivered','unclear'} for x in rows)
with open(out,'w',encoding='utf-8') as o:
    for x in rows: o.write(json.dumps(x,ensure_ascii=False)+'\n')
from collections import Counter
print(len(rows),Counter(x['fact'] for x in rows),'contra',sum(x['contradiction'] for x in rows),'rep',sum(x['repetition'] for x in rows))
