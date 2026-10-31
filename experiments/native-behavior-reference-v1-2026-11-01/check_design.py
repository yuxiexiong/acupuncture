"""Offline checks for design artifacts only; stdlib, no model or GPU imports."""
import datetime as dt
import hashlib
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def read(path):
    return json.loads(path.read_text())


def main():
    questions = read(HERE / 'questions.json')
    spec = read(HERE / 'conditions.json')
    audit = read(HERE / 'offline-check.json')
    by_id = {q['id']: q for q in questions}
    assert len(by_id) == len(questions) == 168
    assert len({q['prompt'] for q in questions}) == 168
    assert len(spec['conditions']) == 25
    assert len({c['id'] for c in spec['conditions']}) == 25
    assert len(questions) * len(spec['conditions']) == 4200
    assert len({q['reference_id'] for q in questions}) == 96
    for q in questions:
        assert q['reference_id'] in by_id
        assert q['split'] == 'exploratory_reference'
        if q['fact_version'] == 0:
            other = by_id[q['scenario_id'] + '-f1']
            assert q['gold_core'] != other['gold_core']
            assert q['reference_id'] == other['reference_id']
    source = ROOT / spec['directions_source']
    assert hashlib.sha256(source.read_bytes()).hexdigest() == spec['directions_source_sha256']
    for vector in read(source):
        assert len(vector['values']) == 2560
        assert abs(sum(x*x for x in vector['values']) - 1) < 1e-10
    for filename, digest in audit['files'].items():
        assert hashlib.sha256((HERE / filename).read_bytes()).hexdigest() == digest
    historical = []
    for shard in ('preflight-gpu0-r01', 'preflight-gpu1-r01'):
        folder = ROOT / 'experiments/x-recipe-reproduction-v1-2026-10-29' / shard / 'records'
        for path in folder.glob('*.json'):
            output = read(path)['output']
            historical.append((output['generated_token_count'], output['batch_seconds']))
    assert len(historical) == 48
    rate = statistics.median(n/t for n, t in historical if n >= 32)
    assert abs(rate - audit['historical_timing']['median_tokens_per_second_over_records_at_least_32_tokens']) < 1e-12
    # Independently recompute arithmetic/time golds; other truth/rubric checks
    # remain explicitly assistant-reviewed, not certified by these assertions.
    arithmetic = [
        ([35-12+8, 35-17+8], '个'), ([6*5+4, 6*7+4], '支'),
        ([48//6, 48//8], '张'), ([80*75//100, 80*90//100], '元'),
        ([50-2*12, 50-2*18], '元'), ([3000-800, 3000-1250], '米'),
        ([(6+10+14)//3, (6+10+20)//3], ''), ([9*4-3, 9*6-3], '件'),
        ([150*2//3, 210*2//3], '克'), ([18+13, 18+27], '件'),
        ([2*(8+3), 2*(8+5)], '厘米'),
        ([(25-2*6+5)//6, (25-3*6+5)//6], '箱'),
    ]
    for i, (values, unit) in enumerate(arithmetic, 1):
        for fact, value in enumerate(values):
            assert by_id[f'AR{i:02}-f{fact}']['gold_core'] == str(value) + unit
    clock = lambda m: f'{(m//60)%24}:{m%60:02}'
    date = lambda n: (dt.date(2026, 6, 29) + dt.timedelta(days=n))
    temporal = [
        [clock(9*60+20+x) for x in (35,50)],
        ['满足' if 14*60-t >= 15 else '不满足' for t in (13*60+40,13*60+50)],
        ['星期' + '一二三四五六日'[(2+x)%7] for x in (2,5)],
        ['有' if max(600,t)<min(660,720) else '没有' for t in (630,690)],
        [clock(23*60+40+x) for x in (40,80)],
        [f'{date(x).month}月{date(x).day}日' for x in (1,3)],
        ['开放' if 480<=t<720 else '关闭' for t in (719,720)],
        [f'{40+10+x}分钟' for x in (30,50)],
        ['有效' if t<=1080 else '无效' for t in (1080,1081)],
        ['是' if 1<=day<=4 else '否' for day in (4,5)],
        [clock(420+20*(n-1)) for n in (3,4)],
        ['已开始' if t<=15*60-120 else '未开始' for t in (750,810)],
    ]
    for i, values in enumerate(temporal, 1):
        for fact, value in enumerate(values):
            assert by_id[f'TM{i:02}-f{fact}']['gold_core'] == value
    print(json.dumps({'status': 'passed', 'questions': 168, 'conditions': 25,
                      'generations_planned': 4200, 'arithmetic_time_golds_checked': 48,
                      'model_calls': 0, 'gpu_calls': 0}))


if __name__ == '__main__':
    main()
