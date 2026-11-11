"""Read-only check of the first output divergence; no model imports."""
import collections
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
run = HERE.parents[1]/'runs/formal-20261111-r01'
receipt = json.loads((run/'receipt.json').read_text())
counts = {c:collections.Counter() for c in ('CH','HC','HH')}
same = {c:{'t1':0,'t2':0} for c in counts}
scenes, manifest = {}, {}
for rel, h in receipt['files'].items():
    if not rel.startswith('records/') or rel.endswith('bases.json'):
        continue
    raw=(run/rel).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h
    manifest[rel]=h
    r=json.loads(raw)
    base=r['CC']['answer']['N']['ids']
    scene=Path(rel).parts[1].split('-')[3]
    scenes.setdefault(scene,{c:collections.Counter() for c in counts})
    for c in counts:
        seq=r[c]['answer']['N']['ids']
        first=next((str(i+1) for i in range(max(len(base),len(seq)))
                    if i>=len(base) or i>=len(seq) or base[i]!=seq[i]),'same')
        counts[c][first]+=1
        scenes[scene][c][first]+=1
        same[c]['t1']+=r[c]['snapshot']['logits']['zero_canonical']==r['CC']['snapshot']['logits']['zero_canonical']
        same[c]['t2']+=r[c]['answer']['N']['t2_sha']==r['CC']['answer']['N']['t2_sha']
result=dict(status='completed',pairs=len(manifest),token_first_difference_vs_CC=counts,
            logit_hash_equal_to_CC=same,per_scenario=scenes,manifest=manifest,model_forwards=0,gpu_hours=0)
assert len(manifest)==348
if len(sys.argv)==2:
    with Path(sys.argv[1]).open('x') as f:
        json.dump(result,f,indent=2)
else:
    assert result==json.loads((HERE/'token-audit.json').read_text())
    print('Archived token audit exactly reproduced')
