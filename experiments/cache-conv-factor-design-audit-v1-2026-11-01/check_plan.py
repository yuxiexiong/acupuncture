"""Offline design/evidence consistency, without torch, model imports or GPU."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent
p = json.loads((P / 'design.json').read_text())
e = json.loads((P / 'e2-audit.json').read_text())
z = json.loads((P / 'saved-logits.json').read_text())
cells = p['cells']
assert len(cells) == len({c['id'] for c in cells}) == 22
assert len(p['inputs']) == 12 and len({i.split('-')[0] for i in p['inputs']}) == 6
assert set(p['inputs']) == set(z['items']) == {i['id'] for i in e['items']}
assert all(p['clean_candidate_ids'][i] == z['items'][i]['clean_first_token'] for i in p['inputs'])
assert set(p['deep_G']).isdisjoint(p['deep_A'])
assert sorted(p['deep_G'] + p['deep_A']) == list(range(13, 32))
assert [j for lo, hi in p['conv_slices'].values() for j in range(lo, hi)] == list(range(8192))
m = [c for c in cells if c['kind'] == 'factorial']
n = [c for c in cells if c['kind'] == 'native_check']
assert len(m) == 8 and len(n) == 4
assert len({(c['S'], c['Q'], c['V']) for c in m}) == 8
assert all(c['K'] == 'T' and c['entry'] == 'C' for c in m)
assert all(c['S'] == c['K'] == c['entry'] == 'T' for c in n)
assert sum(c['Q'] == c['V'] for c in m) == 4  # COMBO corners
assert len([c for c in cells if c['kind'] == 'random_reference']) == 8
assert p['counts']['formal_scores'] == 12 * 22
assert p['counts']['preflight_scores'] == len(p['preflight_inputs']) * (22 + len(p['preflight_extras']))
assert p['counts']['total_scores'] == 316
assert p['counts']['total_model_forwards'] == p['counts']['total_scores'] + p['counts']['template_forwards'] == 319
assert p['counts']['new_formations'] == p['counts']['free_generations'] == 0
assert p['no_gpu_this_delivery'] and e['model_calls'] == e['gpu_calls'] == z['model_calls'] == z['gpu_calls'] == 0
# Contrast identities on arbitrary signed endpoint values, not favorable data.
x = {(s,q,v): (13*s - 7*q + 2*v + 5*s*q - 11*q*v + 17*s*q*v) for s in (0,1) for q in (0,1) for v in (0,1)}
for s in (0,1):
 g = x[s,1,1] - x[s,0,0]
 av = x[s,0,1] - x[s,0,0]
 aq = x[s,1,0] - x[s,0,0]
 interaction = x[s,1,1] - x[s,1,0] - x[s,0,1] + x[s,0,0]
 assert g == av + aq + interaction
 assert g == (x[s,1,1] - x[s,1,0]) + aq
# Absolute logits can move together without changing competition.
a, stop, shift = 5., 2., 11.
assert (stop + shift) - (a + shift) == stop - a
result = {'status':'OFFLINE_DESIGN_CHECK_PASS','scope':'matrix, counts, archived IDs, algebra; not runner or model acceptance','model_calls':0,'gpu_calls':0,'formal_scores_planned':264,'total_model_forwards_planned':319,'design_sha256':hashlib.sha256((P/'design.json').read_bytes()).hexdigest()}
print(json.dumps(result, ensure_ascii=False, indent=2))
