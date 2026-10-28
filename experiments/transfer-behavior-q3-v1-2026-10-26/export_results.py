"""Validate the bounded run and display all answers, including old 4B references."""
import datetime
import hashlib
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = HERE / 'runs/q3-r01'


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export():
    manifest = read(HERE / 'manifest.json')
    evidence = {name: digest(ROOT / name) for name in manifest['files']}
    assert evidence == manifest['files']
    launch = read(RUN / 'launch.json')
    assert launch['manifest_sha256'] == digest(HERE / 'manifest.json')
    questions = read(HERE / 'questions.json')
    rows, receipts = [], {}
    for size in ('9b', '2b'):
        receipt = read(RUN / size / 'receipt.json')
        assert receipt['status'] == 'completed' and receipt['completed_answers'] == 6
        assert receipt['hooks_removed']
        assert receipt['target_weight_sha256_after'] == receipt['engine']['target_weight_sha256_before']
        assert receipt['manifest_sha256'] == digest(HERE / 'manifest.json')
        assert len(receipt['engineering_checks']) == 2
        assert all(c['exact_historical_match'] and c['calibration_matches'] and c['input_matches']
                   for c in receipt['engineering_checks'])
        receipts[size] = receipt
        assert len(list((RUN / size / 'records').glob('*.jsonl'))) == 6
        for question in questions:
            pair = []
            for arm in ('T_0', 'true_S_recipe'):
                file = RUN / size / 'records' / (question['id'] + '-' + arm + '.jsonl')
                row = read(file)
                assert row['status'] == 'completed' and row['model'] == size
                assert row['question'] == question and row['condition'] == arm
                assert row['output']['max_new_tokens'] == 1024
                assert len(row['output']['token_ids']) == row['output']['generated_token_count']
                assert row['output']['input_token_sha256'] == row['calibration']['input_token_sha256']
                row['evidence_path'] = str(file.relative_to(ROOT))
                pair.append(row)
                rows.append(row)
            assert pair[0]['context'] == pair[1]['context']
            assert pair[0]['calibration'] == pair[1]['calibration']
    for question in questions:
        path = ROOT / 'experiments/qwen35-neuron-steering-2026-10-25/raw-corpus-cpu-bf16-r01' / (question['id'] + '.json')
        old = read(path)
        assert old['prompt'] == question['prompt']
        attempt = next(a for a in old['attempts'] if a['max_new_tokens'] == 1024)
        for arm, name in [('T_0', 'baseline'), ('true_S_recipe', 'modified')]:
            output = attempt[name]
            rows.append({'model': '4b-historical', 'question': question, 'condition': arm,
                         'output': output, 'evidence_path': str(path.relative_to(ROOT))})
    delivery = HERE / 'delivery-r01'
    delivery.mkdir(exist_ok=True)
    (delivery / 'answers.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n')
    plain = ['9B、2B 三题生成原文', '仅展示原文，未添加行为判断。每份最多1024新token；length_limit表示达到长度上限。']
    for question in questions:
        plain.append('\n' + question['id'] + '：' + question['prompt'])
        for size in ('9b', '2b'):
            for arm, label in [('T_0', '原版'), ('true_S_recipe', '两针版')]:
                row = next(r for r in rows if r['model'] == size and r['question']['id'] == question['id'] and r['condition'] == arm)
                output = row['output']
                plain.extend(['\n' + size.upper() + ' · ' + label + ' · ' + output['end_reason'], output['raw_text']])
    (delivery / '9B-2B-三题完整原文.txt').write_text('\n\n'.join(plain) + '\n')
    files = [HERE/'manifest.json', RUN/'launch.json'] + list(RUN.glob('*/receipt.json')) + list(RUN.glob('*/records/*.jsonl'))
    validation = {'status': 'PASS', 'validated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'new_answers': 12, 'historical_reference_answers': 6, 'human_blind_review': 'not performed',
                  'run_wall_seconds': (datetime.datetime.fromisoformat(max(r['ended_utc'] for r in receipts.values()).replace('Z', '+00:00')) - datetime.datetime.fromisoformat(launch['started_utc'])).total_seconds(),
                  'targets': {k: {'elapsed_seconds': v['elapsed_seconds'], 'started_utc': v['started_utc'],
                                  'ended_utc': v['ended_utc'], 'conditions': v['conditions']} for k,v in receipts.items()},
                  'evidence_sha256': {str(p.relative_to(ROOT)): digest(p) for p in files}}
    (delivery/'validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n')
    esc = html.escape
    blocks = []
    for question in questions:
        cards = []
        for size, label in [('4b-historical', '4B 历史参照'), ('9b', '9B 本轮'), ('2b', '2B 本轮')]:
            parts = []
            for arm, title in [('T_0', '原版'), ('true_S_recipe', '两针版')]:
                row = next(r for r in rows if r['model'] == size and r['question']['id'] == question['id'] and r['condition'] == arm)
                o = row['output']
                main = o['raw_text'].split('<|im_end|>')[0]
                opened = ' open' if arm == 'true_S_recipe' else ''
                meta = f"{o['generated_token_count']} token · {o['end_reason']}"
                parts.append(f'<details{opened}><summary>{title} · {esc(meta)}</summary><pre>{esc(main)}</pre><details><summary>完整原始字符串（含特殊 token）</summary><pre>{esc(o["raw_text"])}</pre></details></details>')
            cards.append('<article><h3>'+label+'</h3>'+''.join(parts)+'</article>')
        blocks.append(f'<section><h2>{question["id"]} · {esc(question["prompt"])}</h2><div class="grid">'+''.join(cards)+'</div></section>')
    document = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>三题行为检查：4B / 9B / 2B</title><style>
body{font:16px/1.65 system-ui,sans-serif;background:#f4f5f7;color:#18212b;margin:0;padding:28px;max-width:1800px;margin:auto}h1{font-size:28px}h2{font-size:20px;margin-top:38px}.note,article{background:white;border:1px solid #dde2e8;border-radius:10px;padding:18px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}pre{font:15px/1.65 system-ui,sans-serif;white-space:pre-wrap;overflow-wrap:anywhere;max-height:650px;overflow:auto;background:#f7f8fa;padding:14px}summary{cursor:pointer;font-weight:600;padding:8px 0}a{color:#125dbe}@media(max-width:950px){.grid{grid-template-columns:1fr}body{padding:14px}}h3{margin-top:0}
</style><h1>同样三道日常问题：能力损伤是否伴随有害内容？</h1><div class="note">本轮新生成 12 份回答：9B、2B 各三题，原版与固定两针迁移配方配对；BF16 / eager / greedy / batch1，最多 1024 新 token。全部回答展示，不筛选成功案例。<br>4B 为既有 CPU 历史参照，旧结束规则不同；主回答展示至首个 im_end，完整原串仍保留。三个开发题只能支持初步观察，不能估计总体发生率；尚未进行人工盲评。<br><a href="answers.json">完整结构化回答</a> · <a href="validation.json">证据校验</a> · <a href="../PROTOCOL.zh-CN.md">固定设计</a></div>'''+''.join(blocks)+'</html>'
    (delivery/'index.html').write_text(document)
    print(json.dumps(validation,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    export()
