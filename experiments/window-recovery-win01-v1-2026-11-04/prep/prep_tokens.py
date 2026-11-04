"""WIN-01 freeze prep (zero GPU, CPU tokenizer only): fact-item record boundary b, window sizes, f0/f1 token alignment.
Runs on the server; read-only on the repo.  Uses stage2's own context builder and encoder so ids equal the stage2 run,
and the C1-P segment rule (fact = record line + '\\n', b = last fact token) used by the NCC series for code items.
Usage: python prep_tokens.py OUT.json"""
import importlib.util, json, glob, sys
from pathlib import Path
EXP = Path('/workspace/acupuncture/experiments')
S2 = EXP / 'early-state-localization-stage2-v2-2026-10-30'
sys.path.insert(0, str(S2))
spec = importlib.util.spec_from_file_location('stage2', S2 / 'stage2.py'); st = importlib.util.module_from_spec(spec); spec.loader.exec_module(st)
sys.path.insert(0, str(st.SOURCE))
from control_engine import encode_text
spec = importlib.util.spec_from_file_location('c1p', EXP / 'cache-head-rule-prospective-v1-2026-11-01/c1p_core.py'); c1p = importlib.util.module_from_spec(spec); spec.loader.exec_module(c1p)
from transformers import AutoTokenizer
src = st.exp.read(st.SOURCE / 'contract.json')['source']
tok = AutoTokenizer.from_pretrained(src['model_path'])
out = {'model_path': src['model_path'], 'items': {}, 'pairs': {}}
for stage, run in (('g_development', 'g_development-r01'), ('g_history', 'g_history-r01')):
    rows = st.items_for(stage)
    ctx = st.exp.contexts_for(tok, rows)
    widths = {}
    for f in glob.glob(str(S2 / f'runs/{run}/*/caches/*__N_L00_C4146_D-1.json')):
        widths[Path(f).name.split('__')[0]] = json.load(open(f))['write_audit'][0]['width']
    for r in rows:
        record = r['prompt'].split('\n')[0]
        lab = c1p.label_tokens(tok, ctx[r['id']], record, encode_text)
        n, b = lab['n'], lab['b']
        out['items'][r['id']] = {'panel': run, 'base_id': r['base_id'], 'family': r['family'], 'fact_version': r['fact_version'],
            'n': n, 'b': b, 'record': record, 'straddling_tokens': lab['straddling_tokens'],
            'stage2_width': widths.get(r['id']), 'width_matches_stage2': widths.get(r['id']) == n - 1,
            'W_all': n - 1, 'W_pre': b + 1, 'W_post': n - 2 - b, 'ids': lab['ids'], 'labels': lab['labels']}
for iid, x in out['items'].items():
    if x['fact_version'] != 0:
        continue
    y = out['items'].get(iid.replace('-f0-', '-f1-'))
    if y is None:
        continue
    same_len = x['n'] == y['n']
    diff = [k for k in range(min(x['n'], y['n'])) if x['ids'][k] != y['ids'][k]] if same_len else None
    out['pairs'][iid] = {'panel': x['panel'], 'f1': iid.replace('-f0-', '-f1-'), 'same_len': same_len, 'same_b': x['b'] == y['b'],
        'diff_positions': diff, 'diff_all_in_fact': (same_len and bool(diff) and all(x['labels'][k] == 'fact' and y['labels'][k] == 'fact' for k in diff)),
        'n': [x['n'], y['n']], 'b': [x['b'], y['b']],
        'diff_tokens': ([[tok.decode([x['ids'][k]]), tok.decode([y['ids'][k]])] for k in diff] if diff else None)}
json.dump(out, open(sys.argv[1], 'w'), ensure_ascii=False, indent=1)
print('items', len(out['items']), 'width_match', sum(v['width_matches_stage2'] for v in out['items'].values()),
      'straddle', sum(bool(v['straddling_tokens']) for v in out['items'].values()))
print('pairs', len(out['pairs']), 'same_len', sum(p['same_len'] for p in out['pairs'].values()),
      'aligned(diff only in fact)', sum(p['diff_all_in_fact'] for p in out['pairs'].values()))
