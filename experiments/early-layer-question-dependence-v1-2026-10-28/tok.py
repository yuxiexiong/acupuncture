import json, collections
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'
def load(p):
    with open(p) as f:
        for line in f:
            if line.strip(): yield json.loads(line)
for name,path in [('qwen',R+'layer-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl'),('llama',R+'llama31-layer-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')]:
    ft=collections.defaultdict(collections.Counter); ex={}
    seen=set()
    for r in load(path):
        if r.get('layer') is None or r['layer']>7: continue
        key=(r['model_id'],r['layer'],r['channel'],r['question_id']); 
        if key in seen: continue
        seen.add(key)
        t=r['output']['token_ids'][0]; band='L0-2' if r['layer']<=2 else 'L3-7'
        ft[(r['model_id'],band)][t]+=1
        ex.setdefault(t, r['output']['raw_text'][:18].replace('\n','\\n'))
    for k in sorted(ft):
        tot=sum(ft[k].values())
        print(k, tot, [(t,c,ex[t]) for t,c in ft[k].most_common(8)])
