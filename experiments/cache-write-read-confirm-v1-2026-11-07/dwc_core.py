"""Frozen DWC estimands: paired, within-family scene bootstrap; no exponential tests."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'cache-selection-precedence-v1-2026-11-06'))
import spf_core as S
M=.25
MAIN,SECOND,DIRS=S.MAIN,S.SECOND,S.DIRS
USES={'D':(1,0),'E':(0,1)}
DONOR_ARMS=('L11d','gainD','withdrawD','gainE','withdrawE')
ARMS=('L11o',)+DONOR_ARMS

def level(b):
    if b['lo']==b['hi']==M:return 'indeterminate'
    return 'holds' if b['lo']>=M else 'below' if b['hi']<M else 'indeterminate'

def decision(f,g,w,r,guards):
    if not all(guards.values()):return 'premise_or_delivery_indeterminate'
    if all(level(x)=='holds' for x in (f,g,w)) and r['lo']>0:return 'independent_magnitude_confirmation'
    if f['hi']<M:return 'write_endpoint_below_margin'
    if any(x['hi']<0 for x in (g,w,r)):return 'opposite_direction_evidence'
    if g['lo']>0 and w['lo']>0 and r['lo']>0:return 'positive_relation_magnitude_unconfirmed'
    return 'relation_indeterminate'

class Bootstrap:
    def __init__(self, scenes, n_boot=20000):
        self.scenes=sorted(scenes);self.families=sorted(set(scenes.values()))
        rng=np.random.default_rng(2026110703)
        self.groups=[np.array([i for i,s in enumerate(self.scenes) if scenes[s]==f]) for f in self.families]
        sizes={len(g) for g in self.groups};assert len(sizes)==1 and 0 not in sizes
        self.indices=[rng.choice(g,size=(n_boot,len(g)),replace=True) for g in self.groups]
    def interval(self, values):
        assert set(values)==set(self.scenes),'missing scene'
        v=np.array([values[s] for s in self.scenes],dtype=float);assert np.isfinite(v).all()
        draws=sum(v[ix].mean(axis=1) for ix in self.indices)/len(self.indices)
        lo,hi=np.percentile(draws,[2.5,97.5])
        return dict(mean=float(np.mean([v[g].mean() for g in self.groups])),lo=float(lo),hi=float(hi),
                    scenes=len(v),by_family={f:float(v[g].mean()) for f,g in zip(self.families,self.groups)},per_scene=values)

def mean(values):return sum(values)/len(values)
