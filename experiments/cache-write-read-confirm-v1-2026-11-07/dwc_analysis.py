"""Complete-answer consumer. Formal data only; never selects materials or run continuation."""
import json
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import materials as M
import dwc_core as K
import spf_analysis as A

def analyse(recs,stage='formal',n_boot=20000):
    data=M.load();units=[u for u in data['units'] if u['stage']==stage]
    expected={i for u in units for i in u['item_ids']};assert set(recs)==expected,'missing/extra material'
    primary={r:recs[r] for u in units for r in u['receivers']}
    scenes={u['key']:u['base_id'] for u in units};boot=K.Bootstrap(scenes,n_boot)
    diagboot=K.Bootstrap({u['key']:u['base_id'] for u in units if u['diagnostic']},n_boot)
    def aggregate(values):
        return boot.interval({s:K.mean([v for r,v in values.items() if primary[r]['scenario']==s]) for s in scenes})
    def answer(rec,a,direction,dn=None):
        key=a if dn is None else a+'|'+dn
        nr=(rec['once'] if a=='C0' else rec['directions'][direction])[key]['N']
        return A.row_out(nr,rec['item']),nr
    result=dict(stage=stage,scenes=len(scenes),receivers=len(primary),directions={})
    for direction in K.DIRS:
        cells={a:{} for a in K.ARMS};counts={};valid={};reach={};recover={j:{} for j in K.USES}
        for a in ('C0','L00')+K.ARMS:
            per={};vr={};tr={};cs={}; allcs=dict(n=0,valid_n=0,t2_reached=0,truncated=0,categories={c:0 for c in A.CATS})
            for r,rec in primary.items():
                ds=data['primary_donors'][r];assert rec['donors']==ds
                assert rec['diagnostic_donors']==data['diagnostic_donors'][r]
                rows={};local=[]
                dnlist=[None] if a in ('C0','L00','L11o') else [d['id'] for d in ds]
                for dn in dnlist:
                    row,nr=answer(rec,a,direction,dn);local.append((row,nr))
                    if dn is not None:rows[dn]=row
                    allcs['n']+=1;allcs['valid_n']+=int(row in (0,1,2));allcs['t2_reached']+=int(nr['reached_t2'])
                    allcs['truncated']+=int(nr['termination'] not in ('stop','first_step_stop'))
                    allcs['categories'][A.bucket(row,rec['self_row'])]+=1
                if a=='L11o':rows={d['id']:local[0][0] for d in ds}
                if a in K.ARMS:cells[a][r]=K.S.d_transfer(ds,rows)
                per[r]=K.mean([int(row==rec['self_row']) for row,_ in local])
                vr[r]=K.mean([int(row in (0,1,2)) for row,_ in local]);tr[r]=K.mean([int(nr['reached_t2']) for _,nr in local])
            counts[a]=dict(**allcs,self_correct=aggregate(per),valid=aggregate(vr),reach=aggregate(tr))
            valid[a]=counts[a]['valid']['mean'];reach[a]=counts[a]['reach']['mean']
        for r,rec in primary.items():
            conflicts=[d for d in data['primary_donors'][r] if d['type'] in ('AL','BD')]
            for j in K.USES:
                recover[j][r]=K.mean([int(answer(rec,'withdraw'+j,direction,d['id'])[0]==rec['self_row'])-
                                      int(answer(rec,'L11d',direction,d['id'])[0]==rec['self_row']) for d in conflicts])
        estimates={a:aggregate(v) for a,v in cells.items()}; uses={}
        for j in K.USES:
            g,w='gain'+j,'withdraw'+j
            G=aggregate({r:cells[g][r]-cells['L11o'][r] for r in primary})
            W=aggregate({r:cells['L11d'][r]-cells[w][r] for r in primary});R=aggregate(recover[j])
            guards=dict(clean_correct=counts['C0']['self_correct']['mean']>=.9,
                        O_reachable=reach['L11o']>=.9,F_reachable=reach['L11d']>=.9,
                        O_valid=valid['L11o']>=.9,F_valid=valid['L11d']>=.9,gain_valid=valid[g]>=.9,
                        withdrawal_valid=valid[w]>=.9,gain_drop=valid['L11o']-valid[g]<=.05+1e-12,
                        withdrawal_drop=valid['L11d']-valid[w]<=.05+1e-12)
            uses[j]=dict(G=G,W=W,R=R,guards=guards,decision=K.decision(estimates['L11d'],G,W,R,guards),
                         G_level=K.level(G),W_level=K.level(W),R_pairs=sum(4 for _ in primary))
        diagnostic={}
        for a in ('L11d','gainD','withdrawD'):
            per={s:{k:[] for k in ('row','entity','code','valid','self','truncated','reach')} for s in diagboot.scenes}
            for r,rec in primary.items():
                for d in data['diagnostic_donors'][r]:
                    row,nr=answer(rec,a,direction,d['id']);out=per[rec['scenario']]
                    for k,t in zip(('row','entity','code'),d['predicted_rows']):out[k].append(int(row==t))
                    out['valid'].append(int(row in (0,1,2)));out['self'].append(int(row==rec['self_row']))
                    out['truncated'].append(int(nr['termination'] not in ('stop','first_step_stop')));out['reach'].append(int(nr['reached_t2']))
            vals={k:{s:K.mean(v[k]) for s,v in per.items()} for k in next(iter(per.values()))}
            diagnostic[a]={k:diagboot.interval(v) for k,v in vals.items()}
            for x,y in (('row','entity'),('row','code'),('entity','code')):
                diagnostic[a][x+'_minus_'+y]=diagboot.interval({s:vals[x][s]-vals[y][s] for s in per})
        alignment=aggregate({r:K.mean([int(rec['directions'][direction]['L11d|'+d['id']]['x']==rec['directions'][direction]['L11o']['x']) for d in data['primary_donors'][r]]) for r,rec in primary.items()})
        damage=boot.interval({s:counts['C0']['self_correct']['per_scene'][s]-counts['L00']['self_correct']['per_scene'][s] for s in scenes})
        contrasts={name:aggregate({r:cells[x][r]-cells[y][r] for r in primary}) for name,x,y in
                   [('G_D_minus_E','gainD','gainE'),('W_D_minus_E','withdrawE','withdrawD')]}
        result['directions'][direction]=dict(cells=estimates,uses=uses,counts=counts,first_token_alignment=alignment,
                                            native_damage=damage,paired_comparison=contrasts,diagnostic=diagnostic)
    extras=[x for x in recs.values() if x.get('diagnostic_donor')]
    result['diagnostic_donor_identity']=dict(n=len(extras),correct=sum(A.row_out(x['once']['C0']['N'],x['item'])==x['item']['listed_codes'].index(x['item']['target']) for x in extras))
    return result

def main(run,target,stage='formal'):
    ver,records=A.load(run,stage)
    recs={r:x for r,x in records.items() if not x.get('old_reference')}
    out=analyse(recs,stage);out['source']=dict(verification_sha256=M.sha(Path(run)/'verification.json'),freeze_sha256=ver['freeze_sha256'])
    M.write(target,out)
    print({d:v['uses']['D']['decision'] for d,v in out['directions'].items()})
if __name__=='__main__':main(*sys.argv[1:])
