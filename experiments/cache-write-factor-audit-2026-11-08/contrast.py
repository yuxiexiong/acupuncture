"""Extract paired support/scale/source contrasts from the frozen NMT summary.
Standard library only. No model, new interventions, fits or significance tests.
Run from the repository root: python contrast.py > contrast.json
"""
import hashlib
import json
import subprocess

REF = 'ce497e411'
PATH = 'experiments/cache-increment-norm-match-v2-2026-11-03/analysis/nmt-readouts-r01.json'
raw = subprocess.check_output(['git', 'show', f'{REF}:{PATH}'])
source = json.loads(raw)
rows = []
for direction, data in source['directions'].items():
    for subset in ('main_tnf', 'all48'):
        for receiver, record in data[subset]['receivers'].items():
            cells = record['cells']
            pair = lambda arm: [cells[f'{arm}|b{b}'] for b in '01']
            sub = lambda a, b: [x-y for x, y in zip(a, b)]
            z, native, restored, up, down = map(pair, ('Z','0','1','UP','DN'))
            pairs = dict(base=z, native_support=sub(native,z),
                         restored_support=sub(restored,z), amplitude_up=sub(up,native),
                         source_total=sub(restored,native), equal_norm_high=sub(restored,up),
                         amplitude_down=sub(restored,down), equal_norm_low=sub(down,native))
            delta = {k: v[1]-v[0] for k,v in pairs.items()}
            for b in (0,1):
                assert abs(pairs['source_total'][b]-pairs['amplitude_up'][b]-pairs['equal_norm_high'][b]) < 1e-12
                assert abs(pairs['source_total'][b]-pairs['amplitude_down'][b]-pairs['equal_norm_low'][b]) < 1e-12
            assert abs(delta['source_total']-record['D_src']['eq']) < 1e-12
            assert abs(delta['native_support']-record['H']['0']['eq']) < 1e-12
            assert abs(delta['restored_support']-record['H']['1']['eq']) < 1e-12
            rows.append(dict(direction=direction, subset=subset, receiver=receiver,
                             pairs_b0_b1=pairs, difference_b1_minus_b0=delta,
                             full_answer_counts_all48=data['Y'][receiver]['totals']))
assert len(rows)==16
print(json.dumps(dict(source_ref=REF,source_path=PATH,source_sha256=hashlib.sha256(raw).hexdigest(),
    definitions='F0-Z: native support; FUP-F0: amplitude at native direction; F1-FUP: source difference at matched block norms; F1-F0: total source effect. Telescoping contrasts, not independent or unique mediation components.',
    scope='main_tnf: 32 inputs, six-scenario equal means; all48: supplementary same aggregation; Y: all48',
    checks='16 rows, both telescoping paths and archived H/D_src agree within 1e-12',rows=rows),ensure_ascii=False,indent=2))
