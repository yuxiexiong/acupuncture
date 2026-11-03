"""Extend the original offline report. Read archived data only; never load a model."""
import base64, collections, gzip, hashlib, html, io, json, os, re, subprocess
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/acupuncture-advisor-v2-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
ROOT=Path(__file__).resolve().parents[2]; HERE=Path(__file__).resolve().parent
CANON=Path('/Users/ruizhixu/Documents/ChatGPT/acupuncture')
REF='585e2c0a'; OLD='docs/Acupuncture_实验结果_导师展示_2026-10-28.html'
OUT=ROOT/OLD; E=html.escape
C=ROOT/'experiments/early-input-control-v1-2026-10-29'
S=ROOT/'experiments/early-stop-knowledge-readout-v1-2026-10-29'
L=ROOT/'experiments/early-state-localization-v1-2026-10-29'
J=CANON/'experiments/joint-behavior-capability-v1-2026-10-28'
NAVY,TEAL,RED,GOLD='#253f59','#147d86','#b6503d','#b98a37'
font_manager.fontManager.addfont('/System/Library/Fonts/Supplemental/Songti.ttc')
plt.rcParams.update({'font.family':'Songti SC','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':NAVY,'text.color':NAVY,'xtick.color':NAVY,'ytick.color':NAVY,'axes.edgecolor':'#b6c1cb','svg.fonttype':'path','figure.facecolor':'white','axes.facecolor':'white','axes.unicode_minus':False})
sources={}; checks={}; datasets={}; figures=[]; documents=[]
def read(p):
 p=Path(p); b=p.read_bytes();sources[str(p)]=hashlib.sha256(b).hexdigest()
 if p.suffix=='.zst':return subprocess.check_output(['zstd','-dc',str(p)]).decode()
 if p.suffix=='.gz':return gzip.decompress(b).decode()
 return b.decode()
def js(p):return json.loads(read(p))
def jlines(p):return [json.loads(s) for s in read(p).splitlines() if s.strip()]
def dump(v):return json.dumps(v,ensure_ascii=False,separators=(',',':'),allow_nan=False)
def pack(v):return base64.b64encode(gzip.compress(dump(v).encode(),mtime=0)).decode()
def table(headers, rows, caption=''):
 return '<div class="table-scroll"><table>'+('<caption>'+E(caption)+'</caption>' if caption else '')+'<thead><tr>'+''.join('<th>'+E(str(v))+'</th>' for v in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+E(str(v))+'</td>' for v in row)+'</tr>' for row in rows)+'</tbody></table></div>'
def inline(s):
 s=re.sub(r'!?\[([^\]]+)\]\([^)]+\)',r'\1',s);s=E(s)
 s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
 return re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
def markdown(s):
 lines=s.splitlines();out=[];i=0
 while i<len(lines):
  l=lines[i]
  if l.startswith('```'):
   block=[];i+=1
   while i<len(lines) and not lines[i].startswith('```'):block.append(lines[i]);i+=1
   out.append('<pre class="source-text">'+E('\n'.join(block))+'</pre>')
  elif l.startswith('|'):
   block=[]
   while i<len(lines) and lines[i].startswith('|'):block.append(lines[i]);i+=1
   cells=lambda x:[v.strip() for v in x.strip().strip('|').split('|')]
   out.append(table(cells(block[0]),[cells(v) for v in block[2:]]));continue
  elif re.match(r'^#{1,6} ',l):
   n=min(4,len(l)-len(l.lstrip('#'))+1);out.append(f'<h{n}>'+inline(l.lstrip('# '))+f'</h{n}>')
  elif l.strip():out.append('<p>'+inline(l)+'</p>')
  i+=1
 return ''.join(out)
def doc(p,title):
 text=read(p);documents.append({'title':title,'path':str(p),'text':text,'sha256':sources[str(p)]})
 return '<details class="source-doc"><summary>'+E(title)+' · 完整正文</summary><div>'+markdown(text)+'</div></details>'
def figout(fig,title,source):
 fig.tight_layout();buf=io.StringIO();fig.savefig(buf,format='svg',bbox_inches='tight',metadata={'Date':None});plt.close(fig)
 s=buf.getvalue();s=s[s.index('<svg'):];s=re.sub(r'[ \t]+$', '', s, flags=re.M);n=len(figures)+1
 for ident in sorted(set(re.findall(r'id="([^"]+)"',s)),key=len,reverse=True):
  s=s.replace(f'id="{ident}"',f'id="newfig{n}_{ident}"').replace('#'+ident+'"','#newfig'+str(n)+'_'+ident+'"').replace('#'+ident+')','#newfig'+str(n)+'_'+ident+')')
 figures.append({'number':n,'title':title,'source':source})
 return '<div class="plot wide" role="img" aria-label="'+E(title)+'">'+s+'</div>'
def note(text):return '<div class="reading"><p>'+text+'</p></div>'
def section(id,num,title,sub,body):return f'<section id="{id}"><div class="section-head"><div class="num">{num}</div><div><h2>{title}</h2><p class="subhead">{sub}</p></div></div>{body}</section>'
def flow(nodes):return '<div class="flow">'+ '<div class="arrow">→</div>'.join('<div class="node"><strong>'+a+'</strong><small>'+b+'</small></div>' for a,b in nodes)+'</div>'

# 1. Exact-source answer archives. Preserve text, token ids, candidate scores and locked labels.
items={i['id']:i for f in ['development','confirmation','anchors'] for i in js(C/f'data/{f}.json')}
stages=['development','mechanism-development','patch-development','confirmation','mechanism-confirmation','patch-confirmation']
stage_names=['早层深度比较·开发','时段与撤针·开发','局部替换·开发','早层深度比较·新题确认','时段与撤针·新题确认','局部替换·新题确认']
raw={}; joined={}
for stage,name,n in zip(stages,stage_names,[4632,1210,552,3480,1440,576]):
 rows=jlines(C/f'exports/{stage}-r01-answers.jsonl.zst');assert len(rows)==n
 labels=js(C/f'reading/{stage}-r01/joined.json.zst')['rows'];joined[stage]=labels;bykey={r['key']:r['label'] for r in labels}
 receipts={f'worker-{w}':js(C/f'runs/{stage}-r01/worker-{w}/receipt.json') for w in [0,1]}
 for r in rows:
  assert receipts[r['worker']]['status']=='completed'
  assert receipts[r['worker']]['record_hashes'][r['record']]==r['record_sha256']
  r['prompt']=items[r['item_id']]['prompt'];r['review']=bykey.get(r['key']);r['condition_id']=r['condition']['id']
 raw[stage]=rows;datasets[name]=rows
checks['early_input_export_record_hashes']=sum(map(len,raw.values()))
checks['early_input_NA']=sum(r['status']!='completed' for rows in raw.values() for r in rows)
assert checks['early_input_export_record_hashes']==11890 and checks['early_input_NA']==676
jr=js(J/'analysis-r01/paired-reading-records-r01.json')['records'];assert len(jr)==3720
joint=[]
for r in jr:
 p=J/r['source_path'];b=p.read_bytes();assert hashlib.sha256(b).hexdigest()==r['source_sha256']
 original=json.loads(b);assert original['output']==r['output']
 o=r['output'];joint.append({'key':r['item']['id']+'__'+r['condition']['id'],'item_id':r['item']['id'],'condition_id':r['condition']['id'],'condition':r['condition'],'prompt':r['item']['prompt'],'answer_text':o['answer_text'],'raw_text':o['raw_text'],'token_ids':o['token_ids'],'end_reason':o['end_reason'],'status':'completed','review':r['review'],'candidates':r.get('candidate_readout'),'source':r['source_path'],'record_sha256':r['source_sha256']})
datasets['双针联合测量·全部31条件']=joint;checks['joint_raw_hash_and_text_matches']=len(joint)
pairs=js(J/'analysis-r01/candidate-fact-pairs-r01.json')['pairs'];assert len(pairs)==1488
# Also make the older scan/dose corpus fully searchable; exact duplicate baselines/+1 share one source.
oldrows={}
for rel in ['layer-survey-toy-v1-2026-10-27','layer-negative-dose-survey-toy-v1-2026-10-27','llama31-layer-survey-v1-2026-10-28','llama31-single-point-dose-survey-v1-2026-10-28']:
 for r in jlines(ROOT/f'experiments/{rel}/delivery-r01/all.records.jsonl'):
  dose=r.get('dose',(r.get('intervention') or {}).get('dose',0));key=(r['model_id'],r.get('layer'),r.get('channel'),dose,r['question_id'])
  if key in oldrows:assert oldrows[key]['token_ids']==r['output']['token_ids'];continue
  o=r['output'];oldrows[key]={'key':str(key),'item_id':r['question_id'],'condition_id':f"{r['model_id']} L{r.get('layer')} N{r.get('channel')} d{dose}",'condition':{'model':r['model_id'],'layer':r.get('layer'),'channel':r.get('channel'),'dose':dose},'prompt':r['prompt'],'answer_text':o['answer_text'],'raw_text':o['raw_text'],'token_ids':o['token_ids'],'end_reason':o['end_reason'],'status':'completed'}
assert len(oldrows)==18272;datasets['四模型单针·去重完整原文']=list(oldrows.values())

summ={p:js(C/f'reading/{p}-r01/summary.json') for p in ['development','confirmation']}
readout={p:js(S/f'readout-{p}-r01.json') for p in ['development','confirmation']}
pred=js(C/'reading/mechanism-confirmation-r01/predictions-C1-C6.json')
assert all(v['holds'] is True for v in pred.values())
byjoint={(r['item_id'],r['condition_id']):r for r in joint}
def answerbox(r,title):
 txt=r['answer_text'];txt='（无正文；见停止原因）' if txt=='' else ('（不适用：'+str(r.get('reason'))+'）' if txt is None else txt)
 return '<div class="answer"><h3>'+E(title)+'</h3><pre>'+E(txt)+'</pre><p class="note">'+E(str(r.get('item_id'))+' · '+str(r.get('condition_id'))+' · '+str(r.get('end_reason')))+' · '+str(len(r.get('token_ids') or []))+' token</p></div>'
def jointcase(item,cond,explain):
 a=byjoint[(item,'clean')];b=byjoint[(item,cond)]
 return '<p class="case-guide">'+E(a['prompt'])+'</p><div class="grid2">'+answerbox(a,'原版完整回答')+answerbox(b,cond+' 完整回答')+'</div>'+note(explain)

# 2. Joint candidate plots: exact eight-base pair counts, never a semantic total score.
conds=['clean']+[f'{r}_d{d}' for r in ['AB','R01','R02','R03','R04','R05'] for d in ['0.0625','0.125','0.25','0.5','1']]
cols=[(f,d) for f in ['reading','arithmetic','relation'] for d in ['required','direct']]
mat=np.array([[sum(x['both_fact_targets_selected'] for x in pairs if x['condition']==c and (x['family'],x['demand'])==(f,d)) for f,d in cols] for c in conds])
assert list(mat[0])==[8,8,7,8,7,8] and list(mat[5])==[8,8,3,8,0,5]
fig,ax=plt.subplots(figsize=(10.8,9));im=ax.imshow(mat,cmap='GnBu',vmin=0,vmax=8,aspect='auto')
ax.set_xticks(range(6),['阅读\n自行处理','阅读\n给定结论','计算\n自行处理','计算\n给定结论','关系\n自行处理','关系\n给定结论']);ax.set_yticks(range(31),['原版']+[c.replace('_d',' × ') for c in conds[1:]],fontsize=9)
for y in range(31):
 for x in range(6):ax.text(x,y,str(mat[y,x]),ha='center',va='center',fontsize=9,color='white' if mat[y,x]>5 else NAVY)
ax.set_title('全部31条件：两种事实都选中目标措辞的情景数',loc='left',fontweight='bold');fig.colorbar(im,ax=ax,label='每格8个基础情景')
jointheat=figout(fig,'联合测量完整31条件候选读数','candidate-fact-pairs-r01.json')
fig,axs=plt.subplots(1,3,figsize=(11.6,3.3),sharey=True)
for i,(ax,fam) in enumerate(zip(axs,['阅读','计算','关系'])):
 for k,color,lab in [(0,RED,'自行处理'),(1,TEAL,'给定结论')]:ax.plot(range(6),mat[:6,i*2+k],marker='o',color=color,label=lab)
 ax.set_title(fam,loc='left');ax.set_xticks(range(6),['原版','1/16','1/8','1/4','1/2','1']);ax.set_ylim(-.4,8.8);ax.set_yticks([0,2,4,6,8]);ax.grid(axis='y',alpha=.2);ax.set_xlabel('原双针剂量（离散档位）')
axs[0].set_ylabel('两事实都选中目标 / 8');axs[2].legend(frameon=False,fontsize=9)
jointcurve=figout(fig,'联合测量任务与需求的分离','candidate-fact-pairs-r01.json')

# 3. Depth comparisons from the frozen summaries, preserving denominator and signs.
def window(panel,kind,w,sign,dose):return next(g for g in summ[panel]['groups'] if g['key']==['window',kind,w,sign,dose])
fig,axs=plt.subplots(1,2,figsize=(11.6,3.7))
for ax,p,title in zip(axs,['development','confirmation'],['开发题','新题确认']):
 for sign,col,offset in [('+',RED,-.18),('-',TEAL,.18)]:
  g=[window(p,'native',w,sign,1.0) for w in ['early','middle','late']];v=[x['affected_condition_bases'] for x in g]
  assert all(x['condition_bases']==96 for x in g)
  ax.bar(np.arange(3)+offset,v,width=.34,color=col,label=sign+'1')
  for i,x in enumerate(v):ax.text(i+offset,x+2,str(x),ha='center',fontsize=10)
 ax.set_xticks(range(3),['早 L0-3','中 L12-15','后 L24-27']);ax.set_ylim(0,110);ax.set_ylabel('受影响的条件×情景 / 96');ax.set_title(title,loc='left');ax.legend(frameon=False)
depthplot=figout(fig,'早中后层异常的开发与确认对照','reading/*/summary.json')
fig,axs=plt.subplots(1,2,figsize=(11.6,3.6))
for ax,p,title in zip(axs,['development','confirmation'],['开发题','新题确认']):
 labels=[];counts=[]
 for w in ['early','middle','late']:
  for sign in ['+','-']:
   g=window(p,'native',w,sign,1.0);f=g['fact_labels_clean_correct'];n=g['clean_correct_inputs'];labels.append({'early':'早','middle':'中','late':'后'}[w]+sign+'1')
   counts.append([g['eos_first_token'],f.get('not_delivered',0)-g['eos_first_token'],f.get('other_fact',0)+f.get('other_wrong',0),n-f.get('not_delivered',0)-f.get('other_fact',0)-f.get('other_wrong',0)])
 a=np.array(counts);bottom=np.zeros(6)
 for i,(label,color) in enumerate(zip(['首步停止','其他未交付','事实/内容错误','其余标签'],[RED,GOLD,TEAL,'#b8c7d0'])):
  ax.bar(range(6),a[:,i],bottom=bottom,color=color,label=label);bottom+=a[:,i]
 ax.set_xticks(range(6),labels);ax.set_ylabel('输入数（每栏192）');ax.set_title(title,loc='left')
axs[1].legend(frameon=False,fontsize=9,bbox_to_anchor=(1.02,1),loc='upper left')
symptoms=figout(fig,'停止与内容错误分开呈现','reading/*/summary.json')
# Timing and patch labels: observed locked labels, not a new semantic classifier.
def abnormal(r):return r['label']['fact'] in ['other_fact','other_wrong','not_delivered'] or bool(r['label']['contradiction'])
mc=joined['mechanism-confirmation'];md=joined['mechanism-development']
modeids=['full','prefill','decode','prompt_last','prompt_except_last']
anchors=['N_L00_C4146_D+1','N_L02_C5251_D-1']
fig,axs=plt.subplots(1,2,figsize=(11.6,3.6),sharey=True)
for ax,cid in zip(axs,anchors):
 for rows,color,off,label in [(md,TEAL,-.18,'开发'),(mc,RED,.18,'确认')]:
  vals=[]
  for mode in modeids:
   a=[r for r in rows if r['condition']['id']==cid and r['key'].endswith('__'+mode)];assert len(a)==24
   vals.append(sum(abnormal(r) for r in a))
  ax.bar(np.arange(5)+off,vals,.34,color=color,label=label)
  for i,v in enumerate(vals):ax.text(i+off,v+.4,str(v),ha='center',fontsize=9)
 ax.set_xticks(range(5),['全程','仅提示','仅生成','提示\n末位置','提示\n除末位']);ax.set_ylim(0,27);ax.set_title(cid.replace('N_',''),loc='left');ax.set_ylabel('异常回答 / 24');ax.legend(frameon=False)
timingplot=figout(fig,'改变注入时段与位置','mechanism reading joined labels')
withdraw=[]
for panel,rows in [('开发',md),('确认',mc)]:
 lookup={(r['item_id'],r['condition']['id'],r['key'].split('__')[-1]):r for r in rows}
 clean={r['item_id']:r for r in joined['development' if panel=='开发' else 'confirmation'] if r['condition']['id']=='clean'}
 # historical anchor Q items use their verified clean generation in mechanism exports.
 for r in rows:
  if r['condition']['id']=='clean':clean[r['item_id']]=r
 for cid in ['N_L02_C5063_D+1','N_L12_C8296_D-1','N_L13_C248_D+1','N_L25_C2747_D+1']:
  for k in [4,16]:
   bins=[0,0,0,0];ids=[]
   for (item,c,mode),r in lookup.items():
    if c!=cid or mode!='full' or not abnormal(r):continue
    if item in clean and clean[item]['label']['fact']!='follows_fact':continue
    arms=[lookup.get((item,cid,f'fork{k:03d}_{b}')) for b in ['withdraw','rebuild']]
    if any(a is None for a in arms):continue
    a,b=map(abnormal,arms);idx=1 if a and not b else 2 if a and b else 3 if not a and b else 0
    bins[idx]+=1;ids.append(item)
   withdraw.append({'panel':panel,'condition':cid,'step':k,'counts':bins,'n':len(ids)})
# branch id is validated below; an empty denominator must never turn into a plotted zero result.
assert max(x['n'] for x in withdraw)>0
fig,ax=plt.subplots(figsize=(11.6,6));selected=[x for x in withdraw if x['panel']=='确认'];left=np.zeros(len(selected))
for i,(label,color) in enumerate(zip(['撤针及重建均恢复','仅重建恢复','两者仍异常','撤针好而重建坏'],[TEAL,NAVY,RED,GOLD])):
 vals=np.array([v['counts'][i] for v in selected]);ax.barh(range(len(selected)),vals,left=left,color=color,label=label)
 for j,v in enumerate(vals):
  if v:ax.text(left[j]+v/2,j,str(v),ha='center',va='center',color='white',fontsize=10)
 left+=vals
ax.set_yticks(range(len(selected)),[x['condition'].replace('N_','')+f" · k={x['step']} · n={x['n']}" for x in selected]);ax.invert_yaxis();ax.set_xlabel('可实际分叉且原版正确、full异常的输入数');ax.set_xlim(0,26);ax.legend(frameon=False,loc='upper center',bbox_to_anchor=(.5,-.12),ncol=2,fontsize=9)
withdrawplot=figout(fig,'撤针与无针重建的四种结果','mechanism confirmation locked labels')
patchsummary=[]
for panel,stage in [('开发','patch-development'),('确认','patch-confirmation')]:
 groups=collections.defaultdict(list)
 for r in joined[stage]:groups[tuple(r['key'].split('__')[1:])].append(r)
 for (candidate,arm),rows in sorted(groups.items()):patchsummary.append([panel,candidate,arm,len(rows),sum(abnormal(r) for r in rows),sum(r['mech']['tokens']==1 and r['mech']['end_reason']=='eos_token' for r in rows)])
fig,ax=plt.subplots(figsize=(11.6,4.8));ps=[r for r in patchsummary if r[0]=='确认'];cands=sorted(set(r[1] for r in ps));arms=sorted(set(r[2] for r in ps));a=np.full((len(cands),len(arms)),np.nan)
for r in ps:a[cands.index(r[1]),arms.index(r[2])]=r[4]/r[3] if r[3] else np.nan
candlabels={'content_error_a_L13_mlp':'内容错误 · L13 MLP','content_error_b_L15_attention':'内容错误 · L15 注意力','first_step_stop_a_L00_mlp':'首步停止 · L0 MLP','first_step_stop_b_L03_attention':'首步停止 · L3 注意力'}
arm_labels={'clean_self':'干净自替换','counterfactual':'另一事实来源','neighbor':'邻近对照','repair':'干净修复','reverse':'反向重现','treated_self':'受针自替换'}
im=ax.imshow(a,vmin=0,vmax=1,cmap='OrRd',aspect='auto');ax.set_yticks(range(len(cands)),[candlabels[c] for c in cands],fontsize=10);ax.set_xticks(range(len(arms)),[arm_labels[a] for a in arms],fontsize=10)
for r in ps:
 y,x=cands.index(r[1]),arms.index(r[2]);ax.text(x,y,f'{r[4]}/{r[3]}',ha='center',va='center',color='white' if a[y,x]>.65 else NAVY)
ax.set_title('新题确认：每个候选×替换臂的异常数 / 有效记录数',loc='left');fig.colorbar(im,ax=ax,label='异常比例')
patchplot=figout(fig,'局部替换完整候选与六臂对照','patch-confirmation joined labels')

# 4. Fact sensitivity and cache components: independent axes; no knowledge-erasure claims.
fig,axs=plt.subplots(1,2,figsize=(11.6,3.8),sharey=True)
for ax,p,title in zip(axs,['development','confirmation'],['开发题','新题确认']):
 for i,(w,lab) in enumerate([('early','早层'),('middle','中层'),('late','后层')]):
  vals=[v['R'] for v in readout[p]['conditions'].values() if v['kind']=='native' and abs(v['dose'])==1 and v['window']==w];assert len(vals)==16
  ax.scatter(np.full(16,i)+np.linspace(-.12,.12,16),vals,s=25,color=[RED,GOLD,TEAL][i],alpha=.65)
  med=float(np.median(vals));ax.plot([i-.25,i+.25],[med,med],color=NAVY,lw=2.5);ax.text(i,med+.08,f'{med:.3f}',ha='center')
 ax.axhspan(*readout['development']['reference_band'],color='#dce8ee',alpha=.7);ax.axhline(0,color='#999',lw=.5);ax.set_xticks(range(3),['早 L0-3','中 L12-15','后 L24-27']);ax.set_ylabel('事实敏感度保留比 R');ax.set_title(title,loc='left');ax.set_ylim(-.25,1.2)
readoutplot=figout(fig,'各条件事实敏感度及中位数','readout-development/confirmation-r01.json')
# Build human-readable sections separately, keeping the original HTML byte-for-byte as a substring except insertion points.
context={'jointheat':jointheat,'jointcurve':jointcurve,'depthplot':depthplot,'symptoms':symptoms,'timingplot':timingplot,'withdrawplot':withdrawplot,'patchplot':patchplot,'readoutplot':readoutplot}
exec((HERE/'sections.py').read_text(),globals())
base=subprocess.check_output(['git','show',REF+':'+OLD],cwd=ROOT).decode();basehash=hashlib.sha256(base.encode()).hexdigest()
(HERE/'original-report-20261028.html').write_text(base)
# Insert-only preservation: original sections/scripts/styles remain unchanged and independently usable.
page=base.replace('</style>',(HERE/'extra.css').read_text()+'</style>',1)
page=page.replace('<header>','<header>'+overview,1)
page=page.replace('<section id="trace">','<section id="trace">'+note('<strong>版本提示：</strong>本节保留10月28日的观察结论。当时没有实际撤针；新增的时段、撤针、重建和替换实验已在本页后半部完成展示。'),1)
page=page.replace('<section id="direction">','<section id="direction">'+note('<strong>历史展望：</strong>以下是旧版在10月28日的研究方向，保留原文。其后已执行的验证与仍未解决的问题，请看新增第10–19节。'),1)
page=page.replace('<section id="evidence">',extensions+'<section id="evidence">'+note('下面保留旧版完整数据账（截至10月28日）。新增实验的完整统计、合同、原文和验收见上方新增章节，不能把新旧分母直接相加。'),1)
page=page.replace('</body>',f'<script id="extended-data" type="application/json">{dump(payload).replace("<",chr(92)+"u003c")}</script><script id="answers-gzip" type="application/octet-stream">{pack(datasets)}</script><script>'+ (HERE/'viewer.js').read_text()+'</script></body>')
assert page.count('id="answers-gzip"')==1
OUT.write_text(page)
(HERE/'report-extension.md').write_text('\n\n'.join(d['title']+'\n\n'+d['text'] for d in documents))
manifest={'source_git':subprocess.check_output(['git','rev-parse',REF],cwd=ROOT).decode().strip(),'base_html_sha256':basehash,'output_sha256':hashlib.sha256(page.encode()).hexdigest(),'output_bytes':len(page.encode()),'new_figures':figures,'data_counts':{k:len(v) for k,v in datasets.items()},'checks':checks,'sources':sources,'documents':[{'title':d['title'],'sha256':d['sha256'],'path':d['path']} for d in documents]}
(HERE/'build-audit.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print(json.dumps({k:manifest[k] for k in ['output_bytes','data_counts','checks']},ensure_ascii=False));print('new figures',len(figures))
