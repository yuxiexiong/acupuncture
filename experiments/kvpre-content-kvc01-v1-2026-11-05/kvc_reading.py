"""KVC-01 blind reading (CONTRACT r01 §4): same procedure as WIN-01/02.  C and M_same answers are bit-identical to WIN-01/02
records and reuse their labels by (item, text); identical texts within an item share one label (WIN-01 D7); the rest is read.
python kvc_reading.py build RUN_DIR OUT_DIR | join OUT_DIR"""
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kvc_analysis as A  # noqa: E402
import kvc_core as K  # noqa: E402

W1_LABELS = HERE.parent / 'window-recovery-win01-v1-2026-11-04/reading/formal-r01/labels.json'
W2_LABELS = HERE.parent / 'window-prediction-win02-v1-2026-11-04/reading/formal-r01/labels.json'
W2_DIR = HERE.parent / 'window-prediction-win02-v1-2026-11-04'
SEED, SECOND_FRAC = 20261106, 0.15
PROMPT_RULES = (W2_DIR / 'reading/formal-r01/packets').glob('*.json')


def instructions():
    p = next(iter(sorted(PROMPT_RULES)))
    return json.load(open(p))['instructions']


def build(run, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    recs = A.load_records(run)
    l1, l2 = json.load(open(W1_LABELS)), json.load(open(W2_LABELS))
    conflict = {k for k in set(l1) & set(l2) if l1[k] != l2[k]}
    source = {'C': l1, 'N_L00_C4146_D-1|M_same': l1, 'N_L03_C7666_D-1|M_same': l2, 'R0_L00_D-1|M_same': l2}
    prior = {k: v for k, v in {**l1, **l2}.items() if k not in conflict}   # non-bridged reuse only when both sources agree (DECISIONS D3)
    sys.path.insert(0, str(W2_DIR))
    import w2_run as W2R
    items = {}
    for stage in ('g_development', 'g_history'):
        for r in W2R.st.items_for(stage):
            items[r['id']] = r
    reused, new, must = {}, {}, 0
    rows = []
    for rec in recs:
        for v in ('f0', 'f1'):
            ver = rec['versions'][v]
            u, res = ver['item_id'], ver['results']
            cells = [('C', res['C'], True), ('B_pre', res['B_pre'], False)]
            cells += [(f'{d}|{c}', res[d][c], c == 'M_same') for d in K.NEEDLES for c in K.CELLS]
            rows += [(u, cell, x, bridged) for cell, x, bridged in cells]
    for u, cell, x, bridged in [r for r in rows if r[3]]:          # pass 1: bridged cells take their source label
        k = A.text_key(u, x['answer_text'])
        if k in conflict:                                           # DEVIATIONS V1: WIN-01/02 disagree on this text -> read it fresh
            continue
        assert k in source[cell], ('bridged answer without a prior label', cell, u)
        assert reused.get(k, source[cell][k]) == source[cell][k], ('bridged label clash', cell, u)
        reused[k] = source[cell][k]
        must += 1
    for u, cell, x, bridged in [r for r in rows if not r[3] or A.text_key(r[0], r[2]['answer_text']) in conflict]:      # pass 2
        k = A.text_key(u, x['answer_text'])
        if k in reused:
            continue
        if k in prior and k not in conflict:
            reused[k] = prior[k]
        else:
            new.setdefault(k, {'item_id': u, 'text': x['answer_text'], 'cells': []})['cells'].append(cell)
    rng = random.Random(SEED)
    key, packets = {}, {}
    ins = instructions()
    for k in sorted(new):
        aid = 'K' + hashlib.sha256(f'{SEED}|{k}'.encode()).hexdigest()[:10]
        key[aid] = {'text_key': k, 'item_id': new[k]['item_id'], 'cells': new[k]['cells']}
        it = items[new[k]['item_id']]
        pk = packets.setdefault(it['base_id'], {'base_id': it['base_id'], 'instructions': ins, 'items': {}})
        e = pk['items'].setdefault(it['id'], {'item_id': it['id'], 'prompt': it['prompt'], 'expected_answer': it['choices'][it['target_index']],
                                              'other_fact_answer': it['choices'][1 - it['target_index']], 'truth_explanation': it.get('truth_explanation'), 'responses': []})
        e['responses'].append({'id': aid, 'text': new[k]['text']})
    ids = sorted(key)
    second = set(rng.sample(ids, max(1, round(SECOND_FRAC * len(ids))))) if ids else set()
    for d in ('packets', 'second-packets', 'labels', 'second'):
        (out / d).mkdir()
    for base, pk in packets.items():
        for e in pk['items'].values():
            rng.shuffle(e['responses'])
        with open(out / 'packets' / f'{base}.json', 'x') as fh:
            json.dump({**pk, 'items': list(pk['items'].values())}, fh, ensure_ascii=False, indent=1)
        sec = [{**e, 'responses': [x for x in e['responses'] if x['id'] in second]} for e in pk['items'].values()]
        sec = [e for e in sec if e['responses']]
        if sec:
            with open(out / 'second-packets' / f'{base}.json', 'x') as fh:
                json.dump({**pk, 'items': sec}, fh, ensure_ascii=False, indent=1)
    for name, val in (('key.json', key), ('reused.json', reused)):
        with open(out / name, 'x') as fh:
            json.dump(val, fh, ensure_ascii=False, indent=1)
    info = {'run': str(run), 'bridged_answers': must, 'reused_texts': len(reused), 'new_texts': len(new), 'second_sample': len(second),
            'packets': sorted(packets), 'seed': SEED, 'instructions_sha256': hashlib.sha256(ins.encode()).hexdigest()}
    with open(out / 'build.json', 'x') as fh:
        json.dump(info, fh, ensure_ascii=False, indent=1)
    return info


def join(out):
    sys.path.insert(0, str(HERE.parent / 'window-recovery-win01-v1-2026-11-04'))
    import win_reading as WR
    return WR.join(out)


if __name__ == '__main__':
    print(json.dumps(build(sys.argv[2], sys.argv[3]) if sys.argv[1] == 'build' else join(sys.argv[2]), ensure_ascii=False, indent=1))
