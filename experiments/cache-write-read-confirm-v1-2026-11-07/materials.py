"""Finite predeclared vocabulary; deterministic text-only construction, no model imports."""
import hashlib
import itertools
import json
from pathlib import Path
import random
import unicodedata

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FAMILIES = {
 'NQ01': ('仓储台账','U','茶杯 水桶 纸盒 毛巾 扫帚 托盘 皮包 铅笔 灯罩'),
 'NQ02': ('巡检名册','V','路灯 栏杆 长椅 井盖 门框 台阶 立柱 围墙 门牌'),
 'NQ03': ('图纸目录','W','叶轮 套筒 支架 卡扣 接头 导轨 底座 齿条 滚轮'),
 'NQ04': ('标本登记','X','水晶 砂岩 石英 萤石 玛瑙 玉石 云母 岩盐 长石'),
 'NQ05': ('航线编排','Y','石港 沙港 林港 河港 湖港 岩港 桥港 岭港 溪港'),
 'NQ06': ('乐谱清单','Z','钢琴 口琴 提琴 胡琴 号角 风笛 手鼓 锣鼓 竖笛'),
}
COLORS = '红 蓝 黄 绿 白 黑'.split()
INSTRUCTION = '请根据上面的记录，简短回答，只需给出编号。'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(t): return ''.join(unicodedata.normalize('NFKC',t).split())
def write(p,x):
    with Path(p).open('x') as f: json.dump(x,f,ensure_ascii=False,indent=1); f.write('\n')
def load(): return json.loads((HERE/'data/materials-r01.json').read_text())

def tables(items, receivers):
    primary, diagnostic = {}, {}
    for r in receivers:
        rr = items[r]; ds=[]; dx=[]
        for d,dd in sorted(items.items()):
            if dd['scenario'] != rr['scenario'] or d == r: continue
            row=dd['listed_codes'].index(dd['target'])
            key=rr['order'].index(dd['query'])
            if dd['binding_shift'] == 0:
                typ = 'AL' if dd['order']==rr['order'] else 'KS' if dd['query']==rr['query'] else 'RS' if row==rr['listed_codes'].index(rr['target']) else 'BD'
                ds.append(dict(id=d,type=typ,row=row,key=key))
            else:
                code=rr['listed_codes'].index(dd['target'])
                if len({row,key,code})==3: dx.append(dict(id=d,predicted_rows=[row,key,code]))
        assert len(ds)==8 and all(sum(d['type']==t for d in ds)==2 for t in ('AL','KS','RS','BD'))
        assert not dx or {tuple(d['predicted_rows']) for d in dx}==set(itertools.permutations(range(3)))
        primary[r],diagnostic[r]=ds,dx
    return primary,diagnostic

def generate():
    allitems={}; units=[]; inventories={}
    for fi,(family,(head,letter,nouns)) in enumerate(FAMILIES.items()):
        pool=[c+n for c in COLORS for n in nouns.split()]
        assert len(pool)==54 and len(set(pool))==54 and all(len(e)==3 for e in pool)
        rng=random.Random(2026110701+fi); rng.shuffle(pool)
        inventories[family]=pool
        sceneids=[f'DWC-{family}-S{k:02d}' for k in range(16)]
        diag=set(sorted(sceneids,key=lambda s:hashlib.sha256(('DWC-diagnostic|'+s).encode()).hexdigest())[:4])
        for k in range(17):
            stage='formal' if k<16 else 'preflight'; sid=sceneids[k] if k<16 else f'DWC-{family}-P00'
            rg=random.Random((2026110701 if k<16 else 2026110702)+fi*100+k)
            entities=pool[3*k:3*k+3]; rg.shuffle(entities)
            digits=rg.sample(range(1,10),6); codes=[letter+str(digits[j])+str(digits[j+3]) for j in range(3)]
            diagnostic=stage=='preflight' or sid in diag
            ids=[]; receivers=[]
            for b in range(3 if diagnostic else 1):
                binding={q:[entities[e],codes[(e+b)%3]] for e,q in enumerate('ABC')}
                for rotation in range(3):
                    order='ABC'[rotation:]+'ABC'[:rotation]
                    record=head+'：'+'，'.join(binding[e][0]+'编号为'+binding[e][1] for e in order)+'。'
                    listed=[binding[e][1] for e in order]
                    for q in 'ABC':
                        iid=f'{sid}-B{b}-{order}-{q}'; question=binding[q][0]+'的编号是什么？'
                        item=dict(id=iid,base_id=family,scenario=sid,family=family,order=order,query=q,query_name=binding[q][0],
                            binding_shift=b,target=binding[q][1],listed_codes=listed,first_listed=listed[0],binding=binding,
                            distractors=[c for c in listed if c!=binding[q][1]],record=record,question=question,
                            instruction=INSTRUCTION,boundary_text=record,prompt=record+'\n'+question+'\n'+INSTRUCTION,reference_id=family+'-ABC-A')
                        allitems[iid]=item;ids.append(iid)
                        if b==0: receivers.append(iid)
            units.append(dict(key=sid,base_id=family,stage=stage,diagnostic=diagnostic,item_ids=ids,receivers=receivers))
    primary,diagnostic=tables(allitems,[r for u in units for r in u['receivers']])
    # Scan all earlier material/ledger JSON in the actual repository, not prose claims.
    sources={}; oldentities=set(); oldprompts=set(); oldrecords=set(); oldbindings=set()
    def collect(x):
        if isinstance(x,dict):
            if isinstance(x.get('binding'),dict) and isinstance(x.get('prompt'),str):
                vals=list(x['binding'].values())
                if all(isinstance(v,list) and len(v)==2 and all(isinstance(s,str) for s in v) for v in vals):
                    oldentities.update(v[0] for v in vals);oldbindings.add(tuple(sorted(map(tuple,vals))))
                    oldprompts.add(norm(x['prompt']));oldrecords.add(norm(x.get('record','')))
            for v in x.values():collect(v)
        elif isinstance(x,list):
            for v in x:collect(v)
    candidates=[]
    for directory in ('cache-local-v-k-design-v1-2026-11-03','cache-local-v-k-v1-2026-11-03',
                      'cache-native-write-confirm-v1-2026-11-05','cache-selection-precedence-v1-2026-11-06',
                      'cache-donor-write-bridge-v2-2026-11-07','cache-donor-write-readout-v1-2026-11-07'):
        candidates.extend((HERE.parent/directory).rglob('*.json'))
    for p in sorted(candidates):
        if p.stat().st_size>30*2**20:continue
        x=json.loads(p.read_text());before=len(oldprompts);collect(x)
        if len(oldprompts)>before:sources[str(p.relative_to(ROOT))]=sha(p)
    assert oldentities and len(oldprompts)>=120
    assert not oldentities & {v[0] for x in allitems.values() for v in x['binding'].values()}
    assert all(norm(x['prompt']) not in oldprompts and norm(x['record']) not in oldrecords and tuple(sorted(map(tuple,x['binding'].values()))) not in oldbindings for x in allitems.values())
    assert len({norm(x['prompt']) for x in allitems.values()})==len(allitems)
    entitysets=[tuple(sorted(allitems[u['receivers'][0]]['binding'][q][0] for q in 'ABC')) for u in units]
    assert len(set(entitysets))==102 and len(set(itertools.chain.from_iterable(entitysets)))==306
    out=dict(schema=1,status='text_fixed_before_any_new_model_output',seeds=[2026110701,2026110702],
             inventories=inventories,units=units,items=allitems,primary_donors=primary,diagnostic_donors=diagnostic,
             overlap_audit=dict(old_sources_sha256=sources,old_entities=sorted(oldentities),old_prompt_count=len(oldprompts),
                                entity_overlap=0,prompt_overlap=0,record_overlap=0,binding_overlap=0,new_scene_entity_overlap=0))
    write(HERE/'data/materials-r01.json',out)
    print(dict(scenes=len(units),prompts=len(allitems),old_prompt_count=len(oldprompts)))
if __name__=='__main__':generate()
