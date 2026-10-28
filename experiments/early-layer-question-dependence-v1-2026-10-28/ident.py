import json, collections
import os; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')+'/'
def load(p):
    with open(p) as f:
        for line in f:
            if line.strip(): yield json.loads(line)
print("### J. 十点+1：每层有多少通道的8题【完整输出逐字相同】(/10)，以及非EOS但完整相同的例子")
for name,path in [('qwen',R+'layer-survey-toy-v1-2026-10-27/delivery-r01/all.records.jsonl'),('llama',R+'llama31-layer-survey-v1-2026-10-28/delivery-r01/all.records.jsonl')]:
    by=collections.defaultdict(dict); seen=set()
    for r in load(path):
        if r.get('layer') is None: continue
        key=(r['model_id'],r['layer'],r['channel'],r['question_id'])
        if key in seen: continue
        seen.add(key); by[key[:3]][r['question_id']]=r
    per=collections.defaultdict(lambda:[0,0,[]])
    for (m,l,c),qs in by.items():
        outs=[tuple(qs[q]['output']['token_ids']) for q in sorted(qs)]
        same=len(set(outs))==1
        if same:
            per[(m,l)][0]+=1
            if len(outs[0])>1: per[(m,l)][1]+=1; per[(m,l)][2].append((c, qs['Q04']['output']['raw_text'][:40].replace('\n','\\n')))
    models=sorted(set(k[0] for k in per))
    for m in models:
        row=[(l,per[(m,l)][0],per[(m,l)][1]) for l in range(32) if (m,l) in per]
        print(m, 'layer:(allSame, allSame&nonEOS)', [(l,a,b) for l,a,b in row if a])
        for l in range(12):
            if (m,l) in per and per[(m,l)][2]: print('   ', f"L{l}", per[(m,l)][2][:4])
