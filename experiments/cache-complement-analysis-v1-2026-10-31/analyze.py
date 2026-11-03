"""CPU-only reanalysis of archived exports; never imports the model engine."""
import csv, hashlib, json, subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
SRC=ROOT/'source'
def read(p): return json.loads((SRC/p).read_text())
def unpack(p): return subprocess.check_output(['zstd','-dc',str(SRC/p)])
def save(p,x): (ROOT/p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
export='exports/b_validate-r01-answers.jsonl.zst'
raw=unpack(export); manifest=read('exports/exports-manifest.json')['b_validate-r01']
assert hashlib.sha256((SRC/export).read_bytes()).hexdigest()==manifest['export_sha256']
assert hashlib.sha256(raw).hexdigest()==manifest['uncompressed_sha256']
allrows=[json.loads(l) for l in raw.splitlines()]
assert len(allrows)==manifest['records']==2040
items={x['id']:x for x in read('data/validation-r01.json')}
joined=json.loads(unpack('reading/validation-r01/joined.json.zst'))
labels={x['key']:x for x in joined['rows']}
key=json.loads(unpack('reading/validation-r01/key.json.zst'))
assert hashlib.sha256((SRC/'reading/validation-r01/lock.json').read_bytes()).hexdigest()==joined['lock_sha256']
freeze=read('freeze-r01.json'); frozen=[]
for f,h in freeze['files'].items():
 rel=f.split('early-state-localization-stage2-v2-2026-10-30/')[-1]
 if (SRC/rel).is_file():
  assert hashlib.sha256((SRC/rel).read_bytes()).hexdigest()==h,rel
  frozen.append(rel)
armmap={'all:TTT':'TT','all:CCC':'CC','grp4:kv+recurrent+conv:clean':'CT','grp4:kv+recurrent+conv:pollute':'TC'}
selected=[]
for r in allrows:
 if r['arm'] not in armmap: continue
 if r['condition_id']!=('clean' if r['arm']=='all:CCC' else 'N_L00_C4146_D-1'):continue
 receipt=read('runs/b_validate-r01/'+r['worker']+'/receipt.json')
 assert receipt['status']=='completed'
 assert receipt['freeze_sha256']==hashlib.sha256((SRC/'freeze-r01.json').read_bytes()).hexdigest()
 assert receipt['record_hashes']['records/'+r['key']+'.json']==r['record_sha256']
 r=dict(r);r['cell']=armmap[r['arm']];r['item']=items[r['item_id']]
 lab=labels[r['key']];r['label']=lab['label']
 assert hashlib.sha256(r['answer_text'].encode()).hexdigest()==key[lab['anon_id']]['text_sha256']
 assert lab['item_id']==r['item_id'] and lab['arm']==r['arm']
 assert r['generated_tokens']==len(r['token_ids'])==len(r['stop_advantage_steps'])
 assert r['first_step_eos']==(r['token_ids'][0] in [248044,248046])
 if r['cell'] in ('CT','TC'):
  assert r['group']==4 and r['subset']=='kv+recurrent+conv'
  assert r['background']==('T' if r['cell']=='CT' else 'C')
 for c,text in zip(r['candidates'],r['item']['choices']):
  assert c['text']==text
  assert abs(sum(c['token_logprobs'])-c['loglikelihood'])<1e-6
 r['D']=r['stop_advantage_steps'][0]
 r['contrast']=r['candidates'][0]['loglikelihood']-r['candidates'][1]['loglikelihood']
 r['success_old']=r['label']['fact']=='follows_fact' and not r['label']['contradiction']
 selected.append(r)
assert len(selected)==96
index={(r['base_id'],r['item']['fact_version'],r['cell']):r for r in selected}
assert len(index)==96
bases=sorted({r['base_id'] for r in selected});cells=['TT','CT','TC','CC'];table=[]
for b in bases:
 t={'base':b,'family':index[b,0,'CC']['item']['family']}
 for c in cells:
  pair=[index[b,v,c] for v in [0,1]]
  t['D_'+c]=float(np.mean([r['D'] for r in pair])); oriented=sorted(pair,key=lambda r:r['item']['target_index']);t['S_'+c]=oriented[0]['contrast']-oriented[1]['contrast']
  t['P_'+c]=int(all(r['success_old'] for r in pair))
 for m,sign in [('D',-1),('S',1)]:
  t[m+'_a']=sign*(t[m+'_CT']-t[m+'_TT']);t[m+'_b']=sign*(t[m+'_CC']-t[m+'_TC']);t[m+'_I']=t[m+'_b']-t[m+'_a']
  old=read('analysis/b_validate-r01.json')['tests']
  role='early:stop' if m=='D' else 'early:fact'
  for v,dir in [('a','clean'),('b','pollute')]:
   expected=old[role+'|grp4:kv+recurrent+conv:'+dir]['by_base'][b]
   assert abs(t[m+'_'+v]-expected)<1e-6,(b,m,v,t[m+'_'+v],expected)
 table.append(t)
rng=np.random.default_rng(20261031)
groups=[[i for i,t in enumerate(table) if t['family']==f] for f in sorted({t['family'] for t in table})]
ix=np.concatenate([rng.choice(g,size=(10000,len(g)),replace=True) for g in groups],axis=1)
summary={}
for m in ['D','S']:
 summary[m]={}
 for name in ['a','b','I']:
  vals=np.array([t[m+'_'+name] for t in table]); boots=vals[ix].mean(axis=1)
  summary[m][name]={'mean':float(vals.mean()),'median':float(np.median(vals)),'ci95':np.quantile(boots,[.025,.975]).tolist(),'positive':int(sum(vals>0)),'negative':int(sum(vals<0)),'leave_one_out':[float(np.delete(vals,i).mean()) for i in range(12)],'by_family':{f:float(np.mean([t[m+'_'+name] for t in table if t['family']==f])) for f in sorted({t['family'] for t in table})}}
 summary[m]['cells']={c:float(np.mean([t[m+'_'+c] for t in table])) for c in cells}
behavior={}
for c in cells:
 rows=[r for r in selected if r['cell']==c]
 behavior[c]={'first_eos':sum(r['first_step_eos'] for r in rows),'D_range':[min(r['D'] for r in rows),max(r['D'] for r in rows)],'D_zero':sum(r['D']==0 for r in rows),'facts':{f:sum(r['label']['fact']==f for r in rows) for f in sorted({r['label']['fact'] for r in rows})},'success_no_contradiction':sum(r['success_old'] for r in rows),'paired_success':sum(t['P_'+c] for t in table),'contradiction':sum(r['label']['contradiction'] for r in rows),'repetition':sum(r['label']['repetition'] for r in rows),'truncated':sum(r['end_reason']!='eos_token' for r in rows)}
with (ROOT/'by-base.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
save('selected-records.json',selected);save('summary.json',dict(metrics=summary,behavior=behavior))
save('verification.json',dict(export_hashes_verified=True,reading_text_hashes_verified=96,frozen_files_checked=frozen,records=96,candidate_sequences=192,receipt_record_hash_links_verified=96,original_analysis_differences_max_below=1e-6,original_tensor_audits_rechecked=False,gpu_calls=0))
with (ROOT/'answers-review.md').open('w') as f:
 for b in bases:
  for v in [0,1]:
   f.write(f'## {b} / fact {v}\n\n'+index[b,v,'CC']['item']['prompt']+'\n\n')
   for c in cells:
    r=index[b,v,c];f.write(f"### {c} · D={r['D']} · {r['label']}\n\n{r['answer_text'] or '[首步EOS，无正文]'}\n\n")
print(json.dumps(dict(metrics=summary,behavior=behavior),ensure_ascii=False,indent=2))
