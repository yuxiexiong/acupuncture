"""Text/material and arithmetic design checks only; no model or tensor libraries."""
import hashlib
import itertools
import json
from pathlib import Path
import random

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEED = 2026111307


def transfer(outputs):
    # Donor query j has answer j. None denotes invalid/stopped output.
    hit = sum(y == j for j, y in enumerate(outputs))
    valid = sum(y in (0, 1, 2) for y in outputs)
    return (3 * hit - valid) / 6


def materials():
    rng = random.Random(SEED)
    nouns = '茶杯 水桶 纸盒 毛巾 扫帚 托盘 皮包 铅笔 灯罩 路灯 栏杆 长椅 井盖 门框 台阶 立柱 围墙 门牌 叶轮 套筒 支架 卡扣 接头 导轨 底座 齿条 滚轮 石英 玛瑙 云母'.split()
    pool = [c + n for c in '红蓝黄绿白黑' for n in nouns]
    rng.shuffle(pool)
    perms = list(itertools.permutations(range(3)))
    units = []
    for i in range(52):
        # Balanced mapping/permutations; no outcome-based material selection.
        mapping, order = perms[i % 6], perms[(i // 6 + i) % 6]
        entities = pool[3*i:3*i+3]
        aliases = [f'代号{i+1:02d}{s}' for s in '甲乙丙']
        digits = rng.sample(range(1, 10), 6)
        codes = [f'U{digits[j]}{digits[j+3]}' for j in range(3)]
        record = ('连接表：' + '；'.join(f'{aliases[j]}对应{entities[mapping[j]]}' for j in range(3))
                  + '。\n编号表：' + '；'.join(f'{entities[j]}的编号是{codes[j]}' for j in order) + '。')
        inputs = []
        for role in ('receiver', 'donor'):
            shift = int(role == 'donor')
            text = ('连接表：' + '；'.join(f'{aliases[j]}对应{entities[mapping[j]]}' for j in range(3))
                    + '。\n编号表：' + '；'.join(f'{entities[j]}的编号是{codes[(j+shift)%3]}' for j in order) + '。')
            for mode in ('direct', 'join'):
                for j in range(3):
                    question = (f'请查{entities[mapping[j]]}的编号。' if mode == 'direct'
                                else f'请查{aliases[j]}所对应物件的编号。')
                    inputs.append(dict(role=role, mode=mode, query=j,
                        target=codes[(mapping[j]+shift)%3], recipient_record_prediction=codes[mapping[j]],
                        prompt=text+'\n'+question+'\n请根据上面的记录，简短回答，只需给出编号。'))
        for start in (0,6):
            assert [x['target'] for x in inputs[start:start+3]] == [x['target'] for x in inputs[start+3:start+6]]
            assert len(set(x['target'] for x in inputs[start:start+3])) == 3
        assert all(x['target'] != x['recipient_record_prediction'] for x in inputs[6:])
        units.append(dict(id=f'SRT-{i:02d}', split='formal' if i < 48 else 'engineering',
                          mapping=mapping, entity_order=order, entities=entities,
                          aliases=aliases, codes=codes, record=record, inputs=inputs))
    return units


def counts(n_units, n_needles):
    receivers = n_units * 2 * 3
    nonself = receivers * 3 * n_needles
    baselines = receivers * (2 + 2*n_needles)  # receiver and donor C, receiver T/H per needle
    return dict(units=n_units, receivers=receivers, donor_prompts=receivers, nonself_pairs=nonself,
                baselines=baselines, arm_trajectories=10*nonself,
                natural_trajectories=baselines+10*nonself,
                requested_source_packages=2*nonself,
                # Formal: one baseline per source background and per arm self replay.
                max_zero_t1=receivers*(1+n_needles),
                max_diagonal_t1=2*nonself,
                max_zero_t2=2*nonself,
                max_self_coefficient_t2=2*nonself,
                clean_calibration_extra_trajectories=0)


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def coefficient_checks():
    # O = alpha S^T q - alpha beta (k.q) S^T k + beta (k.q) v.
    rng = random.Random(SEED + 1)
    maximum = 0.0
    for _ in range(100):
        S = [[rng.uniform(-1, 1) for _ in range(2)] for _ in range(3)]
        J = [[rng.uniform(-.2, .2) for _ in range(2)] for _ in range(3)]
        q, k, wref = [[rng.uniform(-1, 1) for _ in range(3)] for _ in range(3)]
        alpha, beta = rng.random(), rng.random()
        v = [rng.uniform(-1, 1) for _ in range(2)]
        w = [alpha*x for x in q]
        out = [alpha*sum(S[i][j]*q[i] for i in range(3))
               -alpha*beta*dot(k,q)*sum(S[i][j]*k[i] for i in range(3))
               +beta*dot(k,q)*v[j] for j in range(2)]
        patched = [out[j]+sum(J[i][j]*(wref[i]-w[i]) for i in range(3)) for j in range(2)]
        oracle = [alpha*sum((S[i][j]-J[i][j])*q[i] for i in range(3))
                  +sum(J[i][j]*wref[i] for i in range(3))
                  -alpha*beta*dot(k,q)*sum(S[i][j]*k[i] for i in range(3))
                  +beta*dot(k,q)*v[j] for j in range(2)]
        maximum = max(maximum, *(abs(a-b) for a,b in zip(patched, oracle)))
    assert maximum < 1e-12
    return maximum


def main():
    units = materials()
    assert len({p['prompt'] for u in units for p in u['inputs']}) == 624
    assert len({x for u in units for x in u['entities']}) == 156
    for y in (None, 0, 1, 2):
        assert transfer([y]*3) == 0
    assert transfer([0,1,2]) == 1
    assert transfer([1,2,0]) == -.5
    old=json.loads((ROOT/'experiments/cache-write-read-confirm-v1-2026-11-07/data/materials-r01.json').read_text())
    oldprompts={v['prompt'] for v in old['items'].values()}
    assert not oldprompts & {p['prompt'] for u in units for p in u['inputs']}
    selection = json.loads((ROOT/'experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json').read_text())
    selected = [x for x in selection['selected_channels'] if x['model_id']=='9b' and x['layer']==0]
    assert len(selected)==1 and selected[0]['channel']==978
    paths = ['experiments/cache-write-signal-background-v1-2026-11-11/wsb_core.py',
             'experiments/cache-state-read-use-v1-2026-11-03/sru_run.py',
             'experiments/cache-write-read-confirm-v1-2026-11-07/CONTRACT.zh-CN.md',
             'experiments/layer-dose-survey-toy-v1-2026-10-27/selection.json',
             'experiments/neuron-explorer-multimodel-v2-2026-10-26/models.json',
             'experiments/neuron-explorer-multimodel-v2-2026-10-26/model-assets-verification.json']
    sources = {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths}
    payload = dict(status='design_text_only_tokenization_and_model_acceptance_pending',
                   seed=SEED, units=units)
    raw = (json.dumps(payload,ensure_ascii=False,indent=2)+'\n').encode()
    report = dict(status='passed_design_checks_only', model_forwards=0, gpu_calls=0,
        material_sha256=hashlib.sha256(raw).hexdigest(), sources=sources,
        formal_4b=counts(48,2), engineering_4b=counts(4,2),
        formal_9b=counts(48,1), engineering_9b=counts(4,1),
        bridge=dict(receivers=6,nonself_pairs=42,natural_trajectories=516),
        four_b_max_natural=counts(48,2)['natural_trajectories']+2*(516+counts(4,2)['natural_trajectories']),
        nine_b_max_natural=counts(48,1)['natural_trajectories']+2*counts(4,1)['natural_trajectories'],
        storage_GiB_at_56MiB=dict(formal_4b=1728*5*56/1024,
            engineering_4b_with_bridge=(144+42)*5*56/1024,
            maximum_4b=(1728+2*(144+42))*5*56/1024,
            formal_9b=864*5*56/1024, maximum_9b=(864+2*72)*5*56/1024,
            per_stage_cap=768, includes_temporary_cache_and_small_arrays=False),
        coefficient_float64_max_error=coefficient_checks(), fixed_output_zero=True,
        nine_b_fixed_channel=978, normal_halfwidth_reference=1.96*.375/(48**.5))
    (HERE/'materials-draft.json').write_bytes(raw)
    (HERE/'design-check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
