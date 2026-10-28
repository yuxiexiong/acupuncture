import json, collections, statistics as st
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'
def load(p):
    with open(p) as f:
        for line in f:
            if line.strip(): yield json.loads(line)
print("### I. 剂量系列：每(模型,层)固定通道，各剂量档 8题中不同首token数 / 不同前3token前缀数 （基线应为8/8）；只列 L0–L7 与几个深层")
doses=[-1,-0.5,-0.25,-0.125,-0.0625,0.0625,0.125,0.25,0.5,1]
for name,path in [('qwen',R+'layer-negative-dose-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl'),('llama',R+'llama31-single-point-dose-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')]:
    by=collections.defaultdict(dict); seen=set()
    for r in load(path):
        if r.get('layer') is None: continue
        d=float(r.get('dose',1)); key=(r['model_id'],r['layer'],d,r['question_id'])
        if key in seen: continue
        seen.add(key); by[key[:3]][r['question_id']]=r['output']['token_ids']
    layers=sorted(set(k[1] for k in by))
    show=[l for l in layers if l<8]+[l for l in layers if l in (12,16,20,24,28,31)]
    models=sorted(set(k[0] for k in by))
    for m in models:
        for l in show:
            cells=[]
            for d in doses:
                qs=by.get((m,l,d))
                if not qs: cells.append(' - '); continue
                toks=list(qs.values()); d1=len(set(t[0] for t in toks)); d3=len(set(tuple(t[:3]) for t in toks))
                cells.append(f"{d1}/{d3}")
            print(f"{m:>18} L{l:02d} "+' | '.join(f"{c:>4}" for c in cells))
    print('   doses:',doses)
