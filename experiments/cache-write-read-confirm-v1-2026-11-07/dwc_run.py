"""DWC-01: independent material confirmation; frozen DWR/LVK/SRU operators.
Uses the frozen LVK LHook and SRU RHook unchanged. See CONTRACT for interpretation.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DWB_DIR = HERE.parent / 'cache-donor-write-bridge-v2-2026-11-07'
sys.path.insert(0, str(DWB_DIR))
import dwb_run as DW
from dwb_run import *
import sru_run as SR
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import dwc_core as K
import materials as M
DWR_DIR = HERE.parent / 'cache-donor-write-readout-v1-2026-11-07'
sys.path.insert(0, str(DWR_DIR))
import dwr_run as OLD
S = K.S
PLAN_ID = 'DWC-01-INDEPENDENT-CONFIRM-r01'
DIRS = tuple(K.DIRS)
MAIN, SECOND = K.MAIN, K.SECOND
STAGES = ('preflight', 'formal')
MAX_WORKERS = {'preflight': 1, 'formal': 2}
N_RECEIVERS = {'preflight': 60, 'formal': 864}
GPU_CAP_S = {'preflight': 5400, 'formal': 57600}
STORAGE_LIMIT = 2 * 2**30
BRIDGES = ('C0', 'L00', 'L11o', 'L11d')



def natural(engine, cache, x, n, counts, hook=None):
    if x in STOP:
        counts['trajectories']+=1
        return dict(ids=[x],termination='stop',reached_t2=False,unreachable_noop=hook is not None),None
    result,z=OLD.natural(engine,cache,x,n,counts,hook=hook)
    result['unreachable_noop']=False
    return result,z

def old_dwr_records():
    out={}
    assert exp.read(DWR_DIR/'runs/formal-r02/verification.json')['status']=='passed'
    for w in (DWR_DIR/'runs/formal-r02').glob('worker-*'):
        if not w.is_dir():continue
        for rel,digest in exp.read(w/'receipt.json')['record_hashes'].items():
            assert exp.sha(w/rel)==digest
            if not Path(rel).name.startswith('scenario-'):
                rec=exp.read(w/rel);out[rec['text']]=rec
    assert len(out)==48
    return out



def plan(stage, worker, n_workers):
    units=[u for u in M.load()['units'] if u['stage']==stage]
    # Equal family and diagnostic counts on both GPUs, entire scenes only.
    result=[]
    for family in M.FAMILIES:
        for diag in (False,True):
            group=sorted((u for u in units if u['base_id']==family and u['diagnostic']==diag),key=lambda u:u['key'])
            result.extend(u for j,u in enumerate(group) if j%n_workers==worker)
    if stage=='preflight':
        result=[{**u,'old_reference':True,'key':'reference-'+u['key']} for u in OLD.plan('preflight',0,1)]+result
    return result




def limits(stage, units=None):
    units=plan(stage,0,1) if units is None else units
    ledger=exp.read(HERE/'data/token-ledger-r01.json')['items']
    total={k:0 for k in COUNT_KEYS+('calibrations',)}
    for u in units:
        if u.get('old_reference'):
            lim,_=OLD.limits('preflight',[u])
        else:
            nr=len(u['receivers']); extra=len(u['item_ids'])-nr; diag=u['diagnostic']
            nf=nr*3+extra; np=nr*2*(8+(6 if diag else 0))
            t1=nr*5+np+extra; zero=nr*2+np
            runs=765+(342 if diag else 0)
            formation=sum(ledger[i]['plan']['L']*(3 if i in u['receivers'] else 1) for i in u['item_ids'])
            lim=dict(formations=nf,prefix_prefills=len(u['item_ids']),formation_token_forwards=formation,
                     t1=t1,refs=0,c_t2=zero,trajectories=runs,shadow=28*zero,n_steps=31*runs,
                     decode_forwards=t1+31*runs+zero,calibrations=0)
        for k,v in lim.items():total[k]+=v
    return total,total['c_t2']






def run_scenario(engine, unit, contexts, calibs, conds, stage, refs):
    import torch
    model, tok = engine.model, engine.tokenizer
    types = L.layer_types(model)
    G = B.g_layers(types, SPLIT)
    assert tuple(G) == G14 and tuple(STOP) == tuple(engine.stop_ids)
    QM = gdn_module()
    KRDR.QHOOK_ORIG[0] = QM.torch_recurrent_gated_delta_rule
    kern0, conv0 = QM.torch_recurrent_gated_delta_rule, QM.causal_conv1d_update
    items, order, vecs = refs['items'], refs['order'], refs['vecs']
    counts = {k: 0 for k in COUNT_KEYS}
    ids = list(unit['item_ids'])
    _, u_off, sign = ARMS_ALL['Rk']
    C, T, info, hC, hT, cconv = {}, {}, {}, {}, {}, {}
    for i in ids:
        C[i], T[i], info[i] = form_new(engine, refs['ledger'][i], contexts, calibs[unit['base_id']], conds if i in unit['receivers'] else {}, counts)
        hC[i] = comp_sha(C[i], types, ALLK, 0)
        hT[i] = {d: comp_sha(T[i][d], types, ALLK, 0) for d in T[i]}
        cconv[i] = {l: L._get(C[i].layers[l], 'conv_states').clone() for l in G}
    bodies = {}
    # Extra diagnostic donors get a clean identity run only; never needle formation.
    for i in ids:
        if i in unit['receivers']:continue
        ci,zi=t1(engine,copy.deepcopy(C[i]),info[i]['last'],info[i]['n'],counts,'t1')
        ni,_=natural(engine,ci,int(zi.argmax()),info[i]['n'],counts)
        ni['text']=tok.decode(ni['ids'],skip_special_tokens=False)
        bodies[i]=dict(text=i,scenario=unit['key'],family=unit['base_id'],diagnostic_donor=True,
                       item=items[i],once={'C0':{'x':int(zi.argmax()),'N':ni}},n_runs=1)
    for r in unit['receivers']:
        D = refs['primary_donors'][r]
        DX = refs['diagnostic_donors'][r]
        last, n = info[r]['last'], info[r]['n']
        once, by_dir = {}, {d: {} for d in DIRS}
        gates = {'bridges': {k: 0 for k in BRIDGES}, 'zero_t2': 0, 'read_hooks': 0,
                 'write_oracle_max': 0., 'read_oracle_max': 0., 'de_reference_max': 0.}

        def finish(c1, z1, d, arm, dn=None, donor_state=None, ab=None):
            hk = SR.RHook(model, G, 'cell', a=ab[0], b=ab[1], Sd=donor_state) if ab else None
            nr, z2 = natural(engine, copy.deepcopy(c1), int(z1.argmax()), n, counts, hook=hk)
            nr['text'] = tok.decode(nr['ids'], skip_special_tokens=False)
            value = {'x': int(z1.argmax()), 'N': nr}
            (once if d is None else by_dir[d])[run_key(arm, dn)] = value
            if hk and nr['reached_t2']:
                gates['read_hooks'] += 1
                gates['read_oracle_max'] = max(gates['read_oracle_max'], max(hk.oracle.values()))
                gates['de_reference_max'] = max(gates['de_reference_max'], max(hk.ref11.values(), default=0.))
            elif not hk:
                gates['bridges'][arm] += 1
            return z2

        def endpoint(d, src, vec):
            hk = LVKR.LHook(model, G, 'cell', a=1, b=1, vec=vec, sign=sign, cconv=cconv[src])
            c, z = LVKR.t1L(engine, copy.deepcopy(T[r][d]), last, n, counts, 't1', hk)
            gates['write_oracle_max'] = max(gates['write_oracle_max'], max(hk.oracle.values()))
            return c, z

        def state(c):
            return {l: L._get(c.layers[l], 'recurrent_states').clone() for l in G}

        def zero_check(c, z, sd, z2):
            hk = SR.RHook(model, G, 'cell', a=0, b=0, Sd=sd)
            _, zz = KRDR.fwd(engine, copy.deepcopy(c), int(z.argmax()), n, counts, 'c_t2', hook=hk)
            assert bit_equal(zz.cpu(), z2.cpu())[0], ('zero hook t2 mismatch', r)
            gates['zero_t2'] += 1

        c0, z0 = t1(engine, copy.deepcopy(C[r]), last, n, counts, 't1')
        finish(c0, z0, None, 'C0')
        del c0
        for d in DIRS:
            c0, z0 = t1(engine, copy.deepcopy(T[r][d]), last, n, counts, 't1')
            finish(c0, z0, d, 'L00')
            del c0
            vec = QKFR.mask_vec(vecs[u_off][f"{unit['base_id']}|{d}"].float(), 'k')
            co, zo = endpoint(d, r, vec)
            so, ho = state(co), comp_sha(co, types, ALLK, 0)
            z2o = finish(co, zo, d, 'L11o')
            if z2o is not None:zero_check(co, zo, so, z2o)
            for donor in D + DX:
                dn = donor['id']
                cf, zf = endpoint(d, dn, vec)
                sf, hf = state(cf), comp_sha(cf, types, ALLK, 0)
                z2f = finish(cf, zf, d, 'L11d', dn)
                if z2f is not None:zero_check(cf, zf, sf, z2f)
                by_dir[d][run_key('L11d',dn)]['first_matches_O']=int(zf.argmax())==int(zo.argmax())
                for j, ab in K.USES.items():
                    if donor in DX and j!='D':continue
                    finish(co, zo, d, 'gain' + j, dn, sf, ab)
                    finish(cf, zf, d, 'withdraw' + j, dn, so, ab)
                assert comp_sha(cf, types, ALLK, 0) == hf, 'source F cache mutated'
                assert all(torch.equal(sf[l], L._get(cf.layers[l], 'recurrent_states')) for l in G)
                del cf, sf
            assert comp_sha(co, types, ALLK, 0) == ho, 'source O cache mutated'
            assert all(torch.equal(so[l], L._get(co.layers[l], 'recurrent_states')) for l in G)
            del co, so
            torch.cuda.empty_cache()
        gates['source_unchanged'] = True
        gates['hooks_removed'] = True
        F.assert_no_hooks(model)
        bodies[r] = {'text': r, 'panel': 'dwc-independent', 'scenario': unit['key'], 'family': unit['base_id'], 'item': info[r]['item'],
                     'self_row': S.row_of(items[r], items[r]['target']), 'donors': D, 'diagnostic_donors': DX, 'once': once,
                     'directions': by_dir, 'n_runs': 1 + sum(map(len, by_dir.values())),
                     'formation_hashes': info[r]['hashes'], 'gates': gates}
    assert all(comp_sha(C[i], types, ALLK, 0) == hC[i] for i in ids)
    assert all(comp_sha(T[i][d], types, ALLK, 0) == hT[i][d] for i in ids for d in T[i])
    assert all(torch.equal(cconv[i][l], L._get(C[i].layers[l], 'conv_states')) for i in ids for l in G)
    assert QM.torch_recurrent_gated_delta_rule is kern0 and QM.causal_conv1d_update is conv0
    F.assert_no_hooks(model)
    return bodies, {'scenario': unit['key'], 'receivers': unit['receivers'], 'directions': list(DIRS),
                    'counts': counts, 'kernel_identity': kernel_identity()}


def frozen_paths():
    own=list(HERE.glob('*.py'))+list((HERE/'data').glob('*.json'))+list((HERE/'readiness').glob('*.py'))
    own += [HERE/n for n in ('CONTRACT.zh-CN.md','DESIGN.zh-CN.md','DEVIATIONS.zh-CN.md')]
    own += [REPO/'docs'/n for n in ('cache-write-read-confirm-plan-v1-2026-11-07.zh-CN.md','cache-write-read-confirm-self-check-v1-2026-11-07.zh-CN.md')]
    own += list((HERE/'deviations').glob('*.md'))
    prior=[DWR_DIR/'freeze-r02.json',DWR_DIR/'runs/formal-r02/verification.json']
    for w in (DWR_DIR/'runs/formal-r02').glob('worker-*'):
        if w.is_dir():prior += [w/'receipt.json']+[w/rel for rel in exp.read(w/'receipt.json')['record_hashes']]
    return sorted(set(own+OLD.frozen_paths()+prior))

def freeze(path):
    value = {'experiment': HERE.name, 'plan_id': PLAN_ID, 'created_at': exp.utc(),
             'files': {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}}
    exp.write(path, value, immutable=True)
    return {'path': str(path), 'sha256': exp.sha(path), 'files': len(value['files'])}


def check_freeze(path):
    value = exp.read(path)
    actual = {str(p.relative_to(REPO)): exp.sha(p) for p in frozen_paths()}
    assert value['files'] == actual, 'Frozen source changed'
    return exp.sha(path)


def extrapolate(pre_root):
    w=Path(pre_root)/'worker-0';r=exp.read(w/'receipt.json')
    scenes=[exp.read(w/rel) for rel in r['record_hashes'] if Path(rel).name.startswith('scenario-')]
    work=sum(x['seconds'] for x in scenes); load=max(0,r['wall_seconds']-work)
    new=[x for x in scenes if not x.get('old_reference')]
    # Conservative: all 96 formal scenes cost as much as a complete diagnostic preflight scene.
    # Scale each family for actual frozen formation-token lengths (all sample lengths known before outputs).
    ledger=exp.read(HERE/'data/token-ledger-r01.json')['items']; formal=plan('formal',0,1)
    detail={}
    for x in new:
        fam=x['family']; pids=x['item_ids']
        premax=max(ledger[i]['plan']['L'] for i in pids)
        fm=max(ledger[i]['plan']['L'] for u in formal if u['base_id']==fam for i in u['item_ids'])
        detail[fam]=dict(preflight_scene_seconds=x['seconds'],length_factor=max(1,fm/premax),
                        formal_seconds=16*x['seconds']*max(1,fm/premax))
    assert set(detail)==set(M.FAMILIES)
    # Report longest observed natural continuation; the wall-time forecast includes those actual decodes.
    longest=max(len(v['N']['ids']) for rel in r['record_hashes'] if not Path(rel).name.startswith('scenario-')
                for rec in [exp.read(w/rel)] for armset in [rec.get('once',{})]+list(rec.get('directions',{}).values()) for v in armset.values())
    return dict(device_seconds=sum(x['formal_seconds'] for x in detail.values())+2*load,
                load_seconds=load,by_family=detail,longest_preflight_continuation=longest,
                method='six family diagnostic-scene times x16; all scenes charged full diagnostics; length scaling; two loads',runs=81648)


def authorize(path, stage):
    auth = exp.read(path)
    assert auth['budget_gpu_process_seconds'] == {'preflight':5400,'formal':57600,'all_in':68400}
    assert auth['output_root'] in ('runs/preflight-r01','runs/preflight-r02','runs/formal-r01')
    assert stage in auth['output_root']
    assert auth['maximum_workers']==len(set(auth['gpu_map'].values()))
    assert auth['required_evidence']
    assert auth['status'] == 'authorized' and auth['experiment'] == HERE.name and auth['plan_id'] == PLAN_ID
    assert auth['user_instruction'] and stage in auth['allowed_stages'] and 1 <= auth['maximum_workers'] <= MAX_WORKERS[stage]
    assert exp.sha(HERE / auth['freeze_path']) == auth['freeze_sha256']
    check_freeze(HERE / auth['freeze_path'])
    for rel, digest in auth['required_evidence'].items():
        assert exp.sha(HERE / rel) == digest, rel
    cpu = exp.read(HERE / auth['cpu_receipt_path'])
    assert cpu['status'] == 'passed' and cpu['failures'] == cpu['errors'] == 0 and cpu['tests_run'] > 0
    for name, digest in cpu['source_hashes'].items():
        assert exp.sha(REPO / name) == digest, name
    SP.FB.S.check_freeze(SP.FB.N.SRU_DIR / 'freeze-r01.json')     # frozen SRU / LVK source tree unchanged
    SP.FB.N.check_freeze(NWR_DIR / 'freeze-r01.json')             # frozen NWR-01 sources unchanged
    SP.FB.check_freeze(SP.FBR_DIR / 'freeze-A-r03.json')          # frozen FBR-01 sources unchanged
    SP.check_freeze(SPF_DIR / 'freeze-A-r02.json')                # frozen SPF-01 sources unchanged
    DW.check_freeze(DWB_DIR / 'freeze-r02.json')
    OLD.check_freeze(DWR_DIR / 'freeze-r02.json')
    asset_check=exp.read(HERE/auth['asset_receipt_path'])
    assert asset_check['status']=='passed' and asset_check['model_calls']==0
    if stage=='formal':
        spent=sum(exp.read(p)['wall_seconds'] for p in (HERE/'runs').glob('preflight-*/worker-*/receipt.json') if exp.read(p)['status'] in ('completed','failed'))
        assert spent<=10800 and spent+GPU_CAP_S['formal']<=68400
    ki = kernel_identity()
    assert not ki['fla'] and not ki['kernels'] and not ki['causal_conv1d'], ('non-torch kernel available', ki)
    if stage == 'formal':
        pre = exp.read(HERE / auth['preflight_verification_path'])
        assert pre['status'] == 'passed' and pre['freeze_sha256'] == auth['freeze_sha256'] and pre['stage'] == 'preflight'
        ex = extrapolate(HERE / Path(auth['preflight_verification_path']).parent)
        assert ex['device_seconds'] <= GPU_CAP_S['formal'], ('preflight extrapolation exceeds the formal cap; stop and report, do not relax', ex)
    return auth


def check_limits(counts, stage, units=None):
    lim, _ = limits(stage, units)
    assert all(counts[k] <= lim[k] for k in lim), (counts, lim)


def execute(engine, stage, output, receipt, units, gpu):
    import threading
    led = exp.read(HERE/'data/token-ledger-r01.json')['items']
    if stage=='preflight':led={**led,**LVKR.ledger()}
    contexts = exp.contexts_for(engine.tokenizer, [v['item'] for v in led.values()])
    conds = conditions()
    receipt['kernel_identity'] = T1.kernel_identity()
    assert list(engine.stop_ids) == list(CFK.STOP)
    F.hook_baseline(engine.model)
    material=M.load(); items=material['items']; order=list(M.FAMILIES)
    refs = {'ledger':led,'items':items,'order':order,'vecs':load_vectors(),
            'primary_donors':material['primary_donors'],'diagnostic_donors':material['diagnostic_donors']}
    olditems,oldorder=OLD.panel()
    oldrefs=dict(ledger=LVKR.ledger(),items=olditems,order=oldorder,lvk=lvk_records(),prior=OLD.prior_records(),vecs=refs['vecs'])
    oldrecords=old_dwr_records() if stage=='preflight' else {}
    totals = {k: 0 for k in COUNT_KEYS + ('calibrations',)}
    calibs = {}
    for s in order:
        calibs[s], csha = QCR.nq_calibration(f'{s}-ABC-A')
        receipt.setdefault('calibration_sources', {})[s] = csha
    hb = {'totals': dict(totals), 'units_done': 0, 'stop': False}

    def beat():
        while not hb['stop']:
            try:
                exp.write(output / 'heartbeat.json', {'at': exp.utc(), 'pid': os.getpid(), 'units_done': hb['units_done'], 'units': len(units),
                                                     'model_calls': hb['totals'], 'device_seconds': time.monotonic() - gpu['t0'], 'bytes': B.dir_bytes(output)})
            except OSError:
                pass
            for _ in range(60):
                if hb['stop']:
                    break
                time.sleep(1)
    th = threading.Thread(target=beat, daemon=True)
    th.start()
    try:
        for u in units:
            started = time.monotonic()
            if u.get('old_reference'):
                bodies,scen=OLD.run_scenario(engine,u,contexts,calibs,conds,'preflight',oldrefs)
                for r,body in bodies.items():
                    reference=oldrecords[r]
                    for direction,armset in body['directions'].items():
                        for arm,value in armset.items():
                            expected=reference['directions'][direction][arm]
                            assert value['x']==expected['x'] and value['N']['ids']==expected['N']['ids']
                            assert value['N'].get('t2_sha')==expected['N'].get('t2_sha')
                    body['old_reference']=True
                scen['old_reference']=True
            else:
                bodies, scen = run_scenario(engine, u, contexts, calibs, conds, stage, refs)
            scen.update(family=u['base_id'],item_ids=u['item_ids'])
            for k in COUNT_KEYS:
                totals[k] += scen['counts'][k]
            check_limits(totals, stage, units)
            meta = {'schema': 1, 'experiment': HERE.name, 'plan_id': PLAN_ID, 'stage': stage, 'freeze_sha256': receipt['freeze_sha256'], 'created_at': exp.utc()}
            for r, body in bodies.items():
                L._store(output, receipt, f'records/{r}.json', {**meta, **body})
            L._store(output, receipt, f'records/scenario-{u["key"]}.json', {**meta, **scen, 'seconds': time.monotonic() - started})
            exp.write(output / 'receipt.json', receipt)
            assert B.dir_bytes(output) <= STORAGE_LIMIT, 'storage budget exceeded'
            hb['totals'], hb['units_done'] = dict(totals), hb['units_done'] + 1
            elapsed = time.monotonic() - gpu['t0']
            assert elapsed <= GPU_CAP_S[stage] / gpu['n_workers'], ('device-second cap reached; scheduling stopped', elapsed)
    finally:
        hb['stop'] = True
        th.join()
    receipt['model_calls'] = totals
    receipt['bytes'] = B.dir_bytes(output)
    if stage == 'preflight':
        exp.write(output / 'preflight.json', {'status': 'passed', 'units': [u['key'] for u in units], 'model_calls': totals, 'bytes': receipt['bytes']},
                  immutable=True)
    return {'units': len(units), 'model_calls': totals}


def run(stage, worker, output, authorization):
    auth = authorize(authorization, stage)
    n_workers, gpu = auth['maximum_workers'], int(auth.get('gpu_map', {}).get(str(worker), worker % 2))
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root'] / f'worker-{worker}').resolve()
    import fcntl
    lock = open(f'/tmp/acupuncture-dwc-worker{worker}.lock', 'w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    free_mib = int(subprocess.check_output(['nvidia-smi', f'--id={gpu}', '--query-gpu=memory.free', '--format=csv,noheader,nounits'], text=True).strip())
    need_mib = 49152
    if stage == 'formal':            # a formal scenario holds more caches than the preflight scenario: require twice the preflight peak
        pre = exp.read(HERE / auth['preflight_verification_path'])
        need_mib = max(need_mib, int(2 * max(w['peak_memory_bytes'] for w in pre['workers']) / 2 ** 20))
    assert free_mib >= need_mib, f'Only {free_mib} MiB free on GPU {gpu}; {need_mib} MiB required'
    output.mkdir(parents=True, exist_ok=False)
    receipt = {'status': 'running', 'stage': stage, 'worker': worker, 'n_workers': n_workers, 'gpu': gpu, 'pid': os.getpid(),
               'started_at': exp.utc(), 'freeze_path': auth['freeze_path'], 'freeze_sha256': auth['freeze_sha256'],
               'authorization_sha256': exp.sha(authorization), 'record_hashes': {}, 'gpu_free_mib_at_start': free_mib}
    exp.write(output / 'execution.json', dict(receipt), immutable=True)
    exp.write(output / 'authorization.json', auth, immutable=True)
    exp.write(output / 'receipt.json', receipt)
    started = time.monotonic()
    sys.path.insert(0, str(T1.SOURCE))
    from control_engine import ControlEngine
    import torch
    try:
        source = exp.read(T1.SOURCE / 'contract.json')['source']
        receipt['asset_identity'] = exp.model_assets()
        engine = ControlEngine(source['model_path'], exp.model_spec(), f'cuda:{gpu}')
        exp.metadata_check(engine)
        exp.write(output / 'metadata.json', engine.metadata, immutable=True)
        units = plan(stage, worker, n_workers)
        exp.write(output / 'plan.json', units, immutable=True)
        receipt['summary'] = execute(engine, stage, output, receipt, units, {'id': gpu, 't0': started, 'n_workers': n_workers})
        receipt['integrity'] = engine.verify_unchanged()
        receipt['peak_memory_bytes'] = int(torch.cuda.max_memory_allocated(gpu))
        receipt['status'] = 'completed'
    except BaseException:
        receipt.update(status='failed', error=traceback.format_exc())
        raise
    finally:
        receipt.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'receipt.json', receipt)
    return receipt


def verify_worker(path):
    path=Path(path);r=exp.read(path/'receipt.json')
    assert r['status']=='completed' and r['freeze_sha256']==check_freeze(HERE/r['freeze_path'])
    assert r['authorization_sha256']==exp.sha(path/'authorization.json')
    units=exp.read(path/'plan.json');assert units==plan(r['stage'],r['worker'],r['n_workers'])
    want={f'records/scenario-{u["key"]}.json' for u in units}
    want|={f'records/{i}.json' for u in units for i in (u['receivers'] if u.get('old_reference') else u['item_ids'])}
    assert set(r['record_hashes'])==want
    for rel,digest in r['record_hashes'].items():assert exp.sha(path/rel)==digest,rel
    material=M.load(); n_rec=0; trajectories=0;zero=0;actual={k:0 for k in COUNT_KEYS}
    for u in units:
        sc=exp.read(path/f'records/scenario-{u["key"]}.json')
        assert sc['receivers']==u['receivers'] and sc['directions']==list(DIRS)
        for k in COUNT_KEYS:actual[k]+=sc['counts'][k]
        for i in (u['receivers'] if u.get('old_reference') else u['item_ids']):
            rec=exp.read(path/f'records/{i}.json');trajectories+=rec['n_runs']
            assert set(rec['once'])=={'C0'}
            if rec.get('diagnostic_donor'):
                assert i not in u['receivers'] and rec['n_runs']==1 and 'directions' not in rec
                continue
            D=rec['donors'];DX=rec.get('diagnostic_donors',[])
            if u.get('old_reference'):
                expected={run_key(a,dn) for d,a,dn in OLD.arm_runs(D,DIRS) if d==MAIN}
            else:
                assert D==material['primary_donors'][i] and DX==material['diagnostic_donors'][i]
                expected={'L00','L11o'}|{run_key(a,d['id']) for d in D for a in K.DONOR_ARMS}
                expected|={run_key(a,d['id']) for d in DX for a in ('L11d','gainD','withdrawD')}
            assert rec['n_runs']==1+2*len(expected) and set(rec['directions'])==set(DIRS)
            for direction,arms in rec['directions'].items():
                assert set(arms)==expected
                for arm,v in arms.items():
                    if arm.startswith(('gain','withdraw')):
                        endpoint='L11o' if arm.startswith('gain') else 'L11d|'+arm.split('|',1)[1]
                        assert v['x']==arms[endpoint]['x']
                        if not v['N']['reached_t2']:
                            assert v['N']['unreachable_noop'] and v['N']['ids']==arms[endpoint]['N']['ids']
            g=rec['gates'];zero+=g['zero_t2']
            assert g['write_oracle_max']<=LVKR.KUCR.ORACLE_TOL
            assert max(g['read_oracle_max'],g['de_reference_max'])<=SR.ORACLE_TOL
            assert g['source_unchanged'] and g['hooks_removed']
            reachable=sum(v['N']['reached_t2'] for arms in rec['directions'].values() for a,v in arms.items() if a=='L11o' or a.startswith('L11d|'))
            hooks=sum(v['N']['reached_t2'] for arms in rec['directions'].values() for a,v in arms.items() if a.startswith(('gain','withdraw')))
            assert g['zero_t2']==reachable and g['read_hooks']==hooks
            n_rec+=1
    check_limits(r['model_calls'],r['stage'],units);lim,_=limits(r['stage'],units)
    assert all(r['model_calls'][k]==lim[k] for k in ('formations','prefix_prefills','t1'))
    assert all(r['model_calls'][k]==actual[k] for k in COUNT_KEYS)
    assert trajectories==lim['trajectories'] and zero==r['model_calls']['c_t2']
    # Legacy reference stops were not counted by old natural(); new trajectories must all be counted.
    legacy_expected=sum(exp.read(path/f'records/scenario-{u["key"]}.json')['counts']['trajectories'] for u in units if u.get('old_reference'))
    legacy_planned=sum(OLD.limits('preflight',[u])[0]['trajectories'] for u in units if u.get('old_reference'))
    assert r['model_calls']['trajectories']==trajectories-legacy_planned+legacy_expected
    assert r['integrity']['hooks_removed'] and r['integrity']['target_weight_sha256_after']==exp.read(path/'metadata.json')['target_weight_sha256_before']
    assert exp.read(path/'exit.json')['returncode']==0
    return dict(status='passed',stage=r['stage'],units=len(units),receivers=n_rec,freeze_sha256=r['freeze_sha256'],
                wall_seconds=r['wall_seconds'],model_calls=r['model_calls'],planned_trajectories=trajectories,bytes=r['bytes'],peak_memory_bytes=r['peak_memory_bytes'])


def launch(stage, authorization, output):
    auth = authorize(authorization, stage)
    output = Path(output).resolve()
    assert output == (HERE / auth['output_root']).resolve()
    output.mkdir(parents=True, exist_ok=False)
    controller = {'status': 'running', 'pid': os.getpid(), 'stage': stage, 'started_at': exp.utc(),
                  'authorization_sha256': exp.sha(authorization), 'freeze_sha256': auth['freeze_sha256'], 'workers': {}}
    exp.write(output / 'execution.json', dict(controller), immutable=True)
    procs, logs, started = {}, [], time.monotonic()
    try:
        for w in range(auth['maximum_workers']):
            log = (output / f'worker-{w}.log').open('x')
            logs.append(log)
            cmd = [sys.executable, '-u', str(HERE / 'dwc_run.py'), 'run', '--stage', stage, '--worker', str(w),
                   '--authorization', str(Path(authorization).resolve()), '--output', str(output / f'worker-{w}')]
            procs[w] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
            controller['workers'][str(w)] = {'pid': procs[w].pid, 'command': cmd}
        exp.write(output / 'controller.json', controller)
        pending, failure = dict(procs), False
        while pending:
            if time.monotonic() - started > GPU_CAP_S[stage] / auth['maximum_workers']:
                raise TimeoutError('stage wall-clock cap reached; stopping this experiment worker only')
            for w, p in list(pending.items()):
                code = p.poll()
                if code is None:
                    continue
                (output / f'worker-{w}').mkdir(exist_ok=True)
                exp.write(output / f'worker-{w}/exit.json', {'returncode': code, 'finished_at': exp.utc()}, immutable=True)
                controller['workers'][str(w)]['returncode'] = code
                failure |= code != 0
                del pending[w]
            exp.write(output / 'controller.json', controller)
            if failure:
                for p in pending.values():
                    p.terminate()
            if pending:
                time.sleep(3)
        assert not failure, 'A worker failed; partial evidence preserved'
        results = [verify_worker(output / f'worker-{w}') for w in range(auth['maximum_workers'])]
        calls = {k: sum(x['model_calls'][k] for x in results) for k in results[0]['model_calls']}
        check_limits(calls, stage)
        assert sum(x['receivers'] for x in results) == N_RECEIVERS[stage]
        gpu_s = sum(x['wall_seconds'] for x in results)
        assert gpu_s <= GPU_CAP_S[stage], ('device-time cap exceeded', gpu_s)
        exp.write(output / 'verification.json', {'status': 'passed', 'stage': stage, 'freeze_sha256': auth['freeze_sha256'], 'workers': results,
                  'units': sum(x['units'] for x in results), 'receivers': N_RECEIVERS[stage], 'model_calls': calls, 'verified_at': exp.utc()}, immutable=True)
        controller['status'] = 'completed'
    except BaseException as error:
        controller.update(status='failed', error=repr(error))
        for w, p in procs.items():
            if p.poll() is None:
                p.terminate()
                p.wait()
        raise
    finally:
        for log in logs:
            log.close()
        controller.update(finished_at=exp.utc(), wall_seconds=time.monotonic() - started)
        exp.write(output / 'controller.json', controller)
    return controller


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest='cmd', required=True)
    sub.add_parser('freeze').add_argument('path')
    sub.add_parser('verify').add_argument('path')
    for name in ('run', 'launch'):
        q = sub.add_parser(name)
        q.add_argument('--stage', required=True, choices=STAGES)
        q.add_argument('--authorization', required=True)
        q.add_argument('--output', required=True)
        if name == 'run':
            q.add_argument('--worker', required=True, type=int, choices=range(2))
    a = p.parse_args()
    sys.path.insert(0, str(T1.SOURCE))
    if a.cmd == 'freeze':
        value = freeze(a.path)
    elif a.cmd == 'verify':
        value = verify_worker(a.path)
    elif a.cmd == 'run':
        value = run(a.stage, a.worker, a.output, a.authorization)
        value = {k: v for k, v in value.items() if k != 'record_hashes'}
    else:
        value = launch(a.stage, a.authorization, a.output)
    print(json.dumps(value, ensure_ascii=False, indent=2, default=str))


if __name__ == '__main__':
    main()
