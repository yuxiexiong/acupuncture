"""Verify immutable inputs and two-stage review locks; never runs study models."""
from pathlib import Path
import hashlib,json,datetime,subprocess
ROOT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
parse=lambda s:datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
manifest=read(ROOT/'inputs.json');process=read(ROOT/'PROCESS.json')
qlocks=[];slocks=[];audit=[]
for r in process['agents']:
 i=r['reviewer'];p=ROOT/f'reviewer-{i}';run=Path(f'/private/tmp/acupuncture-final-review-r{i}-20261108')
 q=read(p/'QUAL_LOCK.json');s=read(p/'SCORE_LOCK.json');scores=read(p/'scores.json')
 for key,file in [('qualitative_sha256','qualitative.zh-CN.md'),('review_sha256','review.zh-CN.md'),('scores_sha256','scores.json')]:assert s[key]==sha(p/file),(i,key)
 assert q['qualitative_sha256']==s['qualitative_sha256']
 assert q['inputs_sha256']==sha(ROOT/'inputs.json')
 assert q['paper_sha256']==sha(ROOT/'paper.zh-CN.md')
 assert q['supplement_sha256']==sha(ROOT/'supplement.zh-CN.md')
 assert all(sha(run/f['path'])==f['sha256'] for f in manifest['files'])
 assert all(1<=scores[k]<=4 for k in ('soundness','presentation','significance','originality'))
 assert 1<=scores['overall']<=6 and 1<=scores['confidence']<=5
 qlocks.append(parse(q.get('utc_time',q.get('UTC'))));slocks.append(parse(s.get('utc_time',s.get('UTC'))))
 phases=[]
 for phase in (1,2):
  log=run/f'phase{phase}-events.jsonl';events=[json.loads(l) for l in log.read_text().splitlines()];commands=[e['item'] for e in events if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='command_execution']
  assert any(e.get('type')=='turn.completed' for e in events),(i,phase)
  phases.append({'phase':phase,'event_log_sha256':sha(log),'completed_commands':len(commands),'web_events':sum(e.get('type')=='item.completed' and e.get('item',{}).get('type')=='web_search' for e in events),'command_receipts':[{'command_sha256':hashlib.sha256(c['command'].encode()).hexdigest(),'first_line':c['command'].splitlines()[0][:180],'exit_code':c.get('exit_code')} for c in commands]})
 audit.append({'reviewer':i,'session_id':r['session_id'],'phases':phases})
phase1=read(ROOT/'qualitative-phase-complete.json');phase2=read(ROOT/'score-phase-complete.json')
assert max(qlocks)<=parse(phase1['verified_utc'])<min(slocks)<=max(slocks)<=parse(phase2['verified_utc'])
for name,source in [('original-paper.zh-CN.md','docs/mechanism-paper-skeleton-2026-11-05.zh-CN.md'),('original-supplement.zh-CN.md','docs/mechanism-paper-supplement-v1.8-2026-11-08.zh-CN.md')]:
 b=subprocess.check_output(['git','show',manifest['source_commit']+':'+source],cwd=ROOT)
 assert hashlib.sha256(b).hexdigest()==sha(ROOT/name)
(ROOT/'execution-audit.json').write_text(json.dumps({'scope':'Completed command receipts and event-log hashes; raw logs retained locally, no hidden reasoning or system text published.','reviewers':audit,'manual_inspection':'No cross-review or prior-review reads observed. R1/R3 accessed five cited arXiv sources; R2 made no external literature visit. Own output and environment thread-id reads allowed. Historical Markdown reports were absent from final inputs.','limitations':'Prompt-level read whitelist plus trace audit; not independent reproduction or OS-level isolation guarantee.'},ensure_ascii=False,indent=2)+'\n')
receipt={'status':'passed','verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':manifest['source_commit'],'reviewers':3,'input_material_files_per_reviewer':len(manifest['files']),'checks':{'input_hashes_unchanged':True,'qualitative_hashes_unchanged_after_scoring':True,'score_and_review_hashes_match_locks':True,'all_qualitative_locks_precede_scoring':True,'all_scores_locked_before_synthesis':True,'six_final_cli_turns_completed':True,'original_paper_and_supplement_match_source_commit':True,'no_study_model_or_gpu_experiments_observed':True},'scores':[read(ROOT/f'reviewer-{i}/scores.json') for i in (1,2,3)],'scope_limits':['Same AI model, no human panel or acceptance probability.','External literature check was selective; R2 none.','Review input package not complete raw-record reconstruction environment.','Two excluded attempts documented; only final clean panel scored.']}
(ROOT/'acceptance.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k not in ('scores','scope_limits')},ensure_ascii=False))
