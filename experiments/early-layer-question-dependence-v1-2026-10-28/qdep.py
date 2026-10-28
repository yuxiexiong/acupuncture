import json, collections, statistics as st
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'
def load(p):
    with open(p) as f:
        for line in f:
            if line.strip(): yield json.loads(line)
def first_eos(r): o=r['output']; return o['generated_token_count']==1 and o['end_reason']=='eos_token'
print("### H. 问题依赖度：每个(模型,层,通道,+1)的8题中「不同首token数」与「不同前3token前缀数」；每层报中位数、=1的通道数(/10)、以及排除首步EOS后仍只有1种首token的通道数")
for name,path in [('qwen',R+'layer-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl'),('llama',R+'llama31-layer-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')]:
    by=collections.defaultdict(dict); seen=set(); base=collections.defaultdict(dict)
    for r in load(path):
        if r.get('layer') is None:
            base[r['model_id']][r['question_id']]=r['output']['token_ids']; continue
        key=(r['model_id'],r['layer'],r['channel'],r['question_id'])
        if key in seen: continue
        seen.add(key); by[key[:3]][r['question_id']]=r
    for m in base: print(m,'baseline distinct first tokens over 8 Q:',len(set(t[0] for t in base[m].values())), 'distinct 3-prefix:',len(set(tuple(t[:3]) for t in base[m].values())))
    per_layer=collections.defaultdict(list)
    for (m,l,c),qs in by.items():
        toks=[qs[q]['output']['token_ids'] for q in sorted(qs)]
        d1=len(set(t[0] for t in toks)); d3=len(set(tuple(t[:3]) for t in toks))
        noneos=[t for t,q in zip(toks,sorted(qs)) if not first_eos(qs[q])]
        d1ne=len(set(t[0] for t in noneos)) if noneos else None
        per_layer[(m,l)].append((d1,d3,d1ne,len(noneos)))
    for k in sorted(per_layer):
        v=per_layer[k]
        d1=[x[0] for x in v]; d3=[x[1] for x in v]
        one=sum(1 for x in v if x[0]==1); one3=sum(1 for x in v if x[1]==1)
        one_ne=sum(1 for x in v if x[2]==1 and x[3]>=4)
        print(f"{k[0]:>18} L{k[1]:02d} medDistinctFirst={st.median(d1):4.1f} medDistinct3pref={st.median(d3):4.1f} chans_allSameFirst={one}/10 chans_allSame3pref={one3}/10 chans_sameFirst_nonEOS(>=4 nonEOS answers)={one_ne}")
