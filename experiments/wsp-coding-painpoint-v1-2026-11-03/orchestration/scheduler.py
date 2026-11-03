"""WCP stage controller. All research entry points require recorded authorization."""
import argparse
import json
from pathlib import Path
import sys
import time
from ledger import Ledger,authorize,write,digest
import protocol as P
import editor


def run(cfg,backend):
    authorize(cfg)
    ledger=Ledger(cfg['run_root'],cfg)
    def step(ident,phase,next_phase,req,reserve=None):
        if ledger.get('overrun'):raise RuntimeError('RECORDED_RESOURCE_OVERRUN')
        return ledger.run(ident,phase,next_phase,req,reserve or {},backend.perform)
    def cpu(ident,phase,next_phase,req,fn):
        return ledger.run(ident,phase,next_phase,req,{},lambda q,o:fn())
    def gpu_reserve(stage,samples=0,tokens=0,tf=0):
        remain=ledger.remaining();seconds=min(remain['gpu_seconds'],remain['gpu_'+stage])
        if seconds<30:raise RuntimeError('GPU_BUDGET_EXHAUSTED')
        return dict(gpu_seconds=seconds,**{'gpu_'+stage:seconds},samples=samples,output_tokens=tokens,tf_tokens=tf,cpu_seconds=remain['cpu_seconds'])
    def generate(panel,arm,gain,phase,stage,n=2,thinking=True):
        rows=[];tasks=backend.panels[panel]
        for offset in range(0,len(tasks),32):
            subset=tasks[offset:offset+32];cap=32768 if panel=='M' else 16384
            req=dict(op='generate',panel=panel,arm=arm,gain=gain,keys=[str(t['task_id']) for t in subset],n=n,thinking=thinking,stage=stage)
            ident=f'{panel}-{arm}-{offset:03d}'
            # Stable reservations are part of action identity. Completed requests reuse their original reservation.
            old=ledger.db.execute('SELECT reserve FROM jobs WHERE id=?',(ident,)).fetchone()
            reserve=json.loads(old[0]) if old else gpu_reserve(stage,len(subset)*n,len(subset)*n*cap)
            req['deadline_seconds']=reserve['gpu_seconds']
            result=step(ident,phase,phase,req,reserve);rows.extend(result['rows'])
        expected={(str(t['task_id']),s) for t in tasks for s in range(n)}
        if len(rows)!=len(expected) or {(r['key'],r['sample']) for r in rows}!=expected:raise ValueError('INCOMPLETE_GENERATION')
        return rows
    def label(rows,role,phase,rule=None):
        annotations=[];frozen=rule
        # All evidence is preserved observer-side; only the selected panel's records enter this role.
        for offset in range(0,len(rows),8):
            batch=rows[offset:offset+8]
            if all(r['correct'] for r in batch):continue
            data=editor.payload(role,'D' if role=='diagnosis' else 'V',phase,batch,frozen)
            req=dict(op='labels',payload=data)
            ident=f'{role}-{offset:03d}'
            old=ledger.db.execute('SELECT reserve FROM jobs WHERE id=?',(ident,)).fetchone()
            remain=ledger.remaining()
            reserve=json.loads(old[0]) if old else dict(editor_turns=1,editor_input_tokens=min(remain['editor_input_tokens'],len(json.dumps(data).encode())+10000),editor_output_tokens=min(remain['editor_output_tokens'],16000),cpu_seconds=remain['cpu_seconds'])
            if min(reserve['editor_input_tokens'],reserve['editor_output_tokens'])<=0:raise RuntimeError('EDITOR_BUDGET_EXHAUSTED')
            result=step(ident,phase,phase,req,reserve)
            annotations.extend(result['annotations'])
            if frozen is None:frozen=result['rules']
            elif result['rules']!=frozen:raise ValueError('SYMPTOM_RULE_CHANGED')
        return annotations,frozen
    def stop(reason,phase):
        result=cpu('stop-'+reason,phase,'STOPPED',dict(reason=reason),lambda:dict(status='stopped',reason=reason))
        write(ledger.root/'receipt.json',dict(result,spent=ledger.get('spent'),remaining=ledger.remaining(),formal_search_started=cfg['mode']=='research'))
        return result
    try:
        d=generate('D','original',None,'D','A')
        cpu('D-complete','D','D_LABEL',dict(digest=digest(d)),lambda:dict(samples=len(d)))
        annotations,rules=label(d,'diagnosis','D_LABEL')
        diagnosis=cpu('diagnosis','D_LABEL','DIAGNOSED',dict(annotations=annotations,rules=rules),lambda:P.diagnose(d,annotations))
        if diagnosis['target'] is None:return stop('no-diagnosable-painpoint','DIAGNOSED')
        request=dict(op='locate',diagnosis=diagnosis,rows=d,stage='A')
        old=ledger.db.execute("SELECT reserve FROM jobs WHERE id='locate'").fetchone()
        reserve=json.loads(old[0]) if old else gpu_reserve('A',tf=backend.locate_tokens(request))
        request['deadline_seconds']=reserve['gpu_seconds']
        loc=step('locate','DIAGNOSED','S1',request,reserve)
        if len(loc['pairs'])<8:return stop('insufficient-phase-pairs','S1')
        supports=loc['supports'];scored=[]
        for i,c in enumerate(P.candidates(supports,[-.5,.5])):
            result=generate('S','c'+str(i),c,'S1','B',n=1);scored.append(dict(c,correct_count=sum(r['correct'] for r in result)))
        extra=cpu('S1-select','S1','S2',dict(scored=scored),lambda:dict(supports=P.select(scored,True)))
        for i,c in enumerate(P.candidates(extra['supports'],[-1,1]),8):
            result=generate('S','c'+str(i),c,'S2','B',n=1);scored.append(dict(c,correct_count=sum(r['correct'] for r in result)))
        selected=cpu('S2-select','S2','CALIBRATE',dict(scored=scored),lambda:dict(needle=P.select(scored)))['needle']
        request=dict(op='calibrate',needle=selected,location=loc,stage='B')
        old=ledger.db.execute("SELECT reserve FROM jobs WHERE id='calibrate'").fetchone()
        reserve=json.loads(old[0]) if old else gpu_reserve('B',tf=loc['calibration_tf_tokens'])
        request['deadline_seconds']=reserve['gpu_seconds']
        calibration=step('calibrate','CALIBRATE','CALIBRATED',request,reserve)
        if not calibration['valid']:return stop('random-calibration-invalid','CALIBRATED')
        controls=[{k:c[k] for k in ('layer','channels','gain')} for c in calibration['controls']]
        freeze=dict(needle=selected,controls=controls,rules=rules,target=diagnosis['target'],candidates=scored,diagnosis=digest(diagnosis),calibration=digest(calibration))
        frozen=cpu('freeze-before-V','CALIBRATED','V',freeze,lambda:dict(freeze=freeze,sha256=digest(freeze)))
        write(ledger.root/'frozen-candidate.json',frozen)
        arms={'original':None,'needle':selected,'opposite':dict(selected,gain=-selected['gain']),**{'random'+str(i+1):c for i,c in enumerate(controls)}}
        v={a:generate('V',a,c,'V','B') for a,c in arms.items()}
        cpu('V-complete','V','V_LABEL',dict(digest=digest(v)),lambda:dict(samples=768))
        # Independent observer role. Mask arm identity in keys, no new diagnostics or needle edits.
        masked=[];mapping={}
        for arm in ('original','needle'):
            for r in v[arm]:
                masked_key=digest([arm,r['key']])[:24];mapping[masked_key]=(arm,r['key']);masked.append(dict(r,key=masked_key))
        va,_=label(sorted(masked,key=lambda r:(r['key'],r['sample'])),'validation','V_LABEL',rules)
        for a in va:
            r=next(r for r in masked if (r['key'],r['sample'])==(a['key'],a['sample']))
            if not P.evidence_valid(a['evidence'],r['text']):raise ValueError('V annotation evidence missing')
        symptoms={arm:len({mapping[a['key']][1] for a in va if mapping[a['key']][0]==arm and diagnosis['target'] in a['labels']}) for arm in ('original','needle')}
        gate=cpu('V-gate','V_LABEL','VALIDATED',dict(symptoms=symptoms,digest=digest(v)),lambda:P.validation(v,symptoms))
        write(ledger.root/'validation.json',gate)
        if not gate['passed']:return stop('validation-negative','VALIDATED')
        cpu('open-T','VALIDATED','T',dict(freeze=frozen['sha256']),lambda:dict(opened=True))
        t={a:generate('T',a,c,'T','C',thinking=a!='thinking_off') for a,c in {'original':None,'needle':selected,'random1':controls[0],'thinking_off':None}.items()}
        cpu('T-complete','T','M',dict(digest=digest(t)),lambda:dict(samples=1312))
        m={a:generate('M',a,c,'M','C') for a,c in {'original':None,'needle':selected}.items()}
        def report():
            effects={a:P.paired_effect(t['original'],t[a]) for a in ('needle','random1','thinking_off')}
            guard=P.paired_effect(m['original'],m['needle'])
            return dict(status='completed',primary=effects['needle'],secondary=effects,math_guard=guard,math_alarm=guard['delta']<-.05,validation=gate,freeze_sha256=frozen['sha256'])
        result=cpu('report','M','COMPLETE',dict(T=digest(t),M=digest(m)),report)
        write(ledger.root/'receipt.json',dict(result,mode=cfg['mode'],spent=ledger.get('spent'),remaining=ledger.remaining(),formal_search_started=cfg['mode']=='research'))
        return result
    finally:ledger.close()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--config',type=Path,required=True);ap.add_argument('--check',action='store_true');a=ap.parse_args()
    cfg=json.loads(a.config.read_text());authorize(cfg)
    if cfg.get('editor_transport')=='mac_ssh':
        import os
        os.environ['WCP_EDITOR_URL']='http://127.0.0.1:18765/'
    if a.check:print('CONFIG_GATE_OK');return
    if cfg['backend']=='fixture':from acceptance import FixtureBackend as Backend
    else:from backend import Backend
    try:print(json.dumps(run(cfg,Backend(cfg))))
    except BaseException as exc:
        root=Path(cfg['run_root']);root.mkdir(parents=True,exist_ok=True)
        write(root/'controller-stopped.json',dict(error=type(exc).__name__+': '+str(exc),time=time.time(),automatic_retry=False));raise


if __name__=='__main__':main()
