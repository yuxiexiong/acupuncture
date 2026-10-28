import json, collections
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'
def load(p):
    with open(p) as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)
def first_eos(r):
    o=r['output']; return o['generated_token_count']==1 and o['end_reason']=='eos_token'
def rep4(ids):
    if len(ids)<4: return 0.0
    seen=set(); rep=0; n=0
    for i in range(len(ids)-3):
        g=tuple(ids[i:i+4]); n+=1
        if g in seen: rep+=1
        seen.add(g)
    return rep/max(1,n)
print("### B. 单点正负十档：早层 L0–L7 每档的 首步EOS / 机械重复 / 中位输出长度 （每格8题）")
for name,path in [('qwen',R+'layer-negative-dose-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl'),('llama',R+'llama31-single-point-dose-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')]:
    tab=collections.defaultdict(lambda: collections.defaultdict(list)); seen=set(); chan={}
    for r in load(path):
        if r.get('layer') is None: continue
        d=float(r.get('dose',1)); key=(r['model_id'],r['layer'],r['channel'],r['question_id'],d)
        if key in seen: continue
        seen.add(key)
        if r['layer']<8:
            tab[(r['model_id'],r['layer'])][d].append(r); chan[(r['model_id'],r['layer'])]=r['channel']
    doses=[-1,-0.5,-0.25,-0.125,-0.0625,0.0625,0.125,0.25,0.5,1]
    for k in sorted(tab):
        cells=[]
        for d in doses:
            rs=tab[k].get(d,[])
            if not rs: cells.append('  -  '); continue
            e=sum(first_eos(r) for r in rs); rp=sum(rep4(r['output']['token_ids'])>=0.5 for r in rs)
            L=sorted(r['output']['generated_token_count'] for r in rs)[len(rs)//2]
            cells.append(f"{e}/{rp}/{L:3d}")
        print(f"{k[0]:>18} L{k[1]} N{chan[k]:<6}", ' | '.join(cells))
    print("   doses:", doses)
