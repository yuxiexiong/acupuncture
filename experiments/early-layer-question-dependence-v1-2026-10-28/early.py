import json, collections, sys, statistics as st
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'
QSTOP={248044,248046}; LSTOP={128001,128008,128009}
def load(p):
    with open(p) as f:
        for line in f:
            line=line.strip()
            if line: yield json.loads(line)
def first_eos(r):
    o=r['output']; return o['generated_token_count']==1 and o['end_reason']=='eos_token'
def mid(r): 
    m=r.get('model_id') or ''
    return m
# ---- A: per model x layer x channel first-step EOS at +1 (ten-point survey)
print("### A. 十点+1：每层每通道的首步EOS数（/8），早层 L0–L7")
for name,path,lay in [('qwen',R+'layer-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl',8),('llama',R+'llama31-layer-survey-v1-2026-10-28/delivery-r01/all.records.jsonl',8)]:
    cnt=collections.defaultdict(lambda: collections.defaultdict(int)); seen=set()
    firsttok=collections.defaultdict(collections.Counter)
    scales={}
    ctx={}
    for r in load(path):
        if r.get('layer') is None: 
            if r.get('context'): ctx[mid(r)]=r['context']
            continue
        key=(mid(r),r['layer'],r['channel'],r['question_id'],float(r.get('dose',1)))
        if key in seen: continue
        seen.add(key)
        if r['layer']<lay:
            cnt[(mid(r),r['layer'])][r['channel']]+=first_eos(r)
            t=r['output']['token_ids'][0]
            firsttok[(mid(r),r['layer'])][t]+=1
        if mid(r) not in scales and r.get('calibration',{}).get('residual_scales'):
            scales[mid(r)]=r['calibration']['residual_scales']
    for k in sorted(cnt):
        row=cnt[k]; vals=[row[c] for c in sorted(row)]
        print(k, 'channels EOS/8:', vals, ' layer total', sum(vals))
    print("--- first-token distribution (token id:count), top 5 per layer")
    for k in sorted(firsttok):
        print(k, firsttok[k].most_common(5))
    print("--- calibration residual scales (m) per layer, first 8 and last 2")
    for m,s in scales.items():
        ks=sorted(s,key=int); print(m, [(k,round(s[k],2)) for k in ks[:8]], '...', [(k,round(s[k],2)) for k in ks[-2:]])
    for m,c in ctx.items():
        print('--- context of', m); print(repr(c[:600]))
    globals()[name+'_firsttok']=firsttok
