"""WIN-02 fact-answer blind reading (as WIN-01; CONTRACT r01 §7).  Truncation rule from WIN-01 DEVIATIONS V4 is written into the instructions.  Same procedure as stage2 reading:
packets per scenario, identical texts within an item read once, anonymous ids, pre-written rule, 15% second reading.
python win_reading.py build RUN_DIR OUT_DIR       -> OUT_DIR/{packets,second-packets}/<base>.json, key.json, reused.json, build.json
python win_reading.py join OUT_DIR                -> OUT_DIR/labels.json (text_key -> label), agreement.json
Readers write OUT_DIR/labels/<base>.jsonl and OUT_DIR/second/<base>.jsonl (one JSON line per response id);
author adjudication of first/second disagreements goes to OUT_DIR/adjudication.json {id: label, ...: reason}."""
import hashlib
import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import w2_analysis as A  # noqa: E402
import w2_core as W  # noqa: E402

S2 = HERE.parent / 'early-state-localization-stage2-v2-2026-10-30'
READING = {'g_development-r01': 'development-r01', 'g_history-r01': 'g_history-r01'}
SEED, SECOND_FRAC = 20261105, 0.15
RULE = (S2 / 'reading/development-r01/RULE.txt').read_text().strip() if (S2 / 'reading/development-r01/RULE.txt').exists() else None
INSTRUCTIONS = ('逐条阅读每个回答，只依据题面判断，不猜测它来自何种条件。每条输出一行 JSON：{"id":..., "fact": follows_fact|other_fact|other_wrong|not_delivered|unclear, '
                '"contradiction": bool, "repetition": bool, "note": "≤30字具体描述"}。截断规则（阅读前写死）：答案写出前就截断（只有推导、算式或箭头链，没写出答案）→ not_delivered；'
                '先给出结论、随后在修正或否定它的过程中截断 → unclear；答案已明确写出、之后才截断 → 按该答案判。判读规则（阅读前写死）：')


def stage2_labels(panel_run):
    """(item_id, condition_id, code) -> label from the stage2 joined reading."""
    j = json.load(open(S2 / 'reading' / READING[panel_run] / 'joined.json'))
    out = {}
    for r in j['rows']:
        if not str(r['arm']).startswith('all:'):
            continue
        cid = r['condition'].get('id', 'clean')
        out[(r['item_id'], cid, r['arm'][4:])] = r['label']['fact']
    return out


def collect(recs):
    """Every in-scope fact answer: (item_id, cell, text, reuse_key or None)."""
    rows = []
    for rec in recs:
        if rec['task'] != 'fact':
            continue
        panel = rec['unit']['panel']
        for v in ('f0', 'f1'):
            ver = rec['versions'][v]
            u, res = ver['item_id'], ver['results']
            rows.append((panel, u, 'C', res['C']['answer_text'], ('clean', 'CCC')))
            for d in W.NEEDLES:
                for w in W.WINDOWS:
                    for arm, x in res[d][w].items():
                        reuse = (d, W.STAGE2_CODE[arm]) if (w == 'W_all' and arm in W.STAGE2_CODE and d != W.RANDOM) else None
                        rows.append((panel, u, f'{d}|{w}|{arm}', x['answer_text'], reuse))
    return rows


def build(run, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    recs = A.load_records(run)
    items = {}
    for panel in READING:
        import importlib.util
        spec = importlib.util.spec_from_file_location('s2', S2 / 'stage2.py')
        st = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(S2))
        spec.loader.exec_module(st)
        for r in st.items_for({'g_development-r01': 'g_development', 'g_history-r01': 'g_history'}[panel]):
            items[r['id']] = r
    rows = collect(recs)
    s2 = {p: stage2_labels(p) for p in READING}
    reused, new = {}, {}
    for panel, u, cell, text, reuse in rows:
        k = A.text_key(u, text)
        if reuse is not None:
            lab = s2[panel][(u, reuse[0], reuse[1])]
            assert reused.get(k, lab) == lab, ('conflicting stage2 labels for one text', k)
            reused[k] = lab
    for panel, u, cell, text, reuse in rows:
        k = A.text_key(u, text)
        if k not in reused:
            new.setdefault(k, {'item_id': u, 'text': text, 'cells': []})['cells'].append(cell)
    rng = random.Random(SEED)
    key, packets = {}, {}
    for k in sorted(new):
        aid = 'W' + hashlib.sha256(f'{SEED}|{k}'.encode()).hexdigest()[:10]
        assert aid not in key
        key[aid] = {'text_key': k, 'item_id': new[k]['item_id'], 'cells': new[k]['cells']}
        it = items[new[k]['item_id']]
        base = it['base_id']
        pk = packets.setdefault(base, {'base_id': base, 'instructions': INSTRUCTIONS + RULE, 'items': {}})
        entry = pk['items'].setdefault(it['id'], {'item_id': it['id'], 'prompt': it['prompt'], 'expected_answer': it['choices'][it['target_index']],
                                                  'other_fact_answer': it['choices'][1 - it['target_index']],
                                                  'truth_explanation': it.get('truth_explanation'), 'responses': []})
        entry['responses'].append({'id': aid, 'text': new[k]['text']})
    ids = sorted(key)
    second = set(rng.sample(ids, max(1, round(SECOND_FRAC * len(ids))))) if ids else set()
    for d in ('packets', 'second-packets', 'labels', 'second'):
        (out / d).mkdir()
    for base, pk in packets.items():
        for e in pk['items'].values():
            rng.shuffle(e['responses'])
        body = {**pk, 'items': list(pk['items'].values())}
        json.dump(body, open(out / 'packets' / f'{base}.json', 'x'), ensure_ascii=False, indent=1)
        sec = {**pk, 'items': [{**e, 'responses': [x for x in e['responses'] if x['id'] in second]} for e in pk['items'].values()]}
        sec['items'] = [e for e in sec['items'] if e['responses']]
        if sec['items']:
            json.dump(sec, open(out / 'second-packets' / f'{base}.json', 'x'), ensure_ascii=False, indent=1)
    json.dump(key, open(out / 'key.json', 'x'), ensure_ascii=False, indent=1)
    json.dump(reused, open(out / 'reused.json', 'x'), ensure_ascii=False, indent=1)
    info = {'run': str(run), 'answers_in_scope': len(rows), 'reused_texts': len(reused), 'new_texts': len(new), 'second_sample': len(second),
            'packets': sorted(packets), 'seed': SEED, 'rule_sha256': hashlib.sha256(RULE.encode()).hexdigest()}
    json.dump(info, open(out / 'build.json', 'x'), ensure_ascii=False, indent=1)
    return info


def _read_jsonl(path):
    out = {}
    for line in open(path):
        line = line.strip()
        if line:
            x = json.loads(line)
            assert x['fact'] in A.LABELS, x
            out[x['id']] = x['fact']
    return out


def join(out):
    out = Path(out)
    key = json.load(open(out / 'key.json'))
    first, second = {}, {}
    for p in sorted((out / 'labels').glob('*.jsonl')):
        first.update(_read_jsonl(p))
    for p in sorted((out / 'second').glob('*.jsonl')):
        second.update(_read_jsonl(p))
    assert set(first) == set(key), ('first reading incomplete', len(set(key) - set(first)), len(set(first) - set(key)))
    want_second = {x['id'] for p in (out / 'second-packets').glob('*.json') for e in json.load(open(p))['items'] for x in e['responses']}
    assert set(second) == want_second, 'second reading incomplete'
    dis = sorted(i for i in second if second[i] != first[i])
    adj = json.load(open(out / 'adjudication.json')) if (out / 'adjudication.json').exists() else {}
    assert all(i in adj for i in dis), ('disagreements without adjudication', [i for i in dis if i not in adj][:10])
    final = dict(first)
    for i in dis:
        assert adj[i]['label'] in A.LABELS
        final[i] = adj[i]['label']
    labels = json.load(open(out / 'reused.json'))
    for i, lab in final.items():
        labels[key[i]['text_key']] = lab
    agree = sum(second[i] == first[i] for i in second) / len(second) if second else None
    yb = lambda x: int(x == 'follows_fact')   # noqa: E731
    agree_y = sum(yb(second[i]) == yb(first[i]) for i in second) / len(second) if second else None
    json.dump(labels, open(out / 'labels.json', 'x'), ensure_ascii=False, indent=1)
    res = {'labels': len(labels), 'new': len(final), 'second': len(second), 'agreement_5class': agree, 'agreement_Y': agree_y,
           'disagreements': dis}
    json.dump(res, open(out / 'agreement.json', 'x'), ensure_ascii=False, indent=1)
    return res


if __name__ == '__main__':
    cmd = sys.argv[1]
    print(json.dumps(build(sys.argv[2], sys.argv[3]) if cmd == 'build' else join(sys.argv[2]), ensure_ascii=False, indent=1))
