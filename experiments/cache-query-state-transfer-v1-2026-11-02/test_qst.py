"""CPU tests for QST-01 (synthetic worlds that must pass AND fail each rule; frozen design structure; wiring).
CUDA_VISIBLE_DEVICES= python test_qst.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import qst_core as K  # noqa: E402

LISTED = ['U17', 'U43', 'U86']
SC = ['NQ01', 'NQ03', 'NQ05', 'NQ06']


class Yfull(unittest.TestCase):
    def test_cases(self):
        self.assertTrue(K.y_full('U43<|im_end|>', 'stop', 'U43', LISTED))
        self.assertTrue(K.y_full('竹篮的编号是U43。<|im_end|>', 'stop', 'U43', LISTED))          # prefix text allowed
        self.assertFalse(K.y_full('U43<|im_end|>', 'stop', 'U17', LISTED))
        self.assertFalse(K.y_full('U17 铁锚、U43 竹篮、U86 陶罐<|im_end|>', 'stop', 'U17', LISTED))   # listing
        self.assertFalse(K.y_full('U43 U43 U43 U43', 'budget', 'U43', LISTED))                    # truncated
        self.assertFalse(K.y_full('<think>U43', 'budget', 'U43', LISTED))


def row(J=None, scen='NQ01', sub=False, b_b=True, c_c=True, b_c=False, c_b=False, rec='r'):
    y = {('b', 'b'): b_b, ('c', 'c'): c_c, ('b', 'c'): b_c, ('c', 'b'): c_b}
    return {'receiver': rec, 'scenario': scen, 'subset': sub, **K.contrast(y)}


def world(kind_by_scen, n=9, sub_n=3):
    rows = []
    for s in SC:
        for k in range(n):
            kind = kind_by_scen[s] if isinstance(kind_by_scen[s], str) else kind_by_scen[s][k]
            args = {'follow': dict(b_b=True, c_c=True), 'fixed_b': dict(b_b=True, c_c=False, c_b=True), 'none': dict(b_b=False, c_c=False),
                    'reverse': dict(b_b=False, c_c=False, b_c=True, c_b=True), 'half': dict(b_b=True, c_c=False)}[kind]
            rows.append(row(scen=s, sub=k < sub_n, rec=f'{s}-{k}', **args))
    return rows, [r for r in rows if r['subset']]


class Contrast(unittest.TestCase):
    def test_values(self):
        self.assertEqual(K.contrast({('b', 'b'): True, ('c', 'c'): True, ('b', 'c'): False, ('c', 'b'): False}), {'J': 1.0, 'W': 1, 'W_rev': 0})
        self.assertEqual(K.contrast({('b', 'b'): True, ('c', 'c'): False, ('b', 'c'): False, ('c', 'b'): True})['J'], 0.0)   # fixed output b
        self.assertEqual(K.contrast({('b', 'b'): True, ('c', 'c'): False, ('b', 'c'): False, ('c', 'b'): False}), {'J': 0.5, 'W': 0, 'W_rev': 0})
        self.assertEqual(K.contrast({('b', 'b'): False, ('c', 'c'): False, ('b', 'c'): True, ('c', 'b'): True}), {'J': -1.0, 'W': 0, 'W_rev': 1})


class Stable(unittest.TestCase):
    def test_pass_fail(self):
        a, s = world({x: 'follow' for x in SC})
        self.assertTrue(K.stable(a, s)['ok'])
        a, s = world({x: 'fixed_b' for x in SC})                       # a fixed output never counts
        self.assertFalse(K.stable(a, s)['ok'])
        a, s = world({x: 'half' for x in SC})                          # J = 0.5 but W = 0
        self.assertFalse(K.stable(a, s)['ok'])
        a, s = world({'NQ01': 'follow', 'NQ03': 'follow', 'NQ05': 'none', 'NQ06': 'none'})   # 2/4 scenarios
        self.assertFalse(K.stable(a, s)['ok'])
        a, s = world({'NQ01': ['none'] * 3 + ['follow'] * 6, 'NQ03': ['none'] * 3 + ['follow'] * 6, 'NQ05': ['none'] * 3 + ['follow'] * 6, 'NQ06': ['none'] * 3 + ['follow'] * 6})
        r = K.stable(a, s)                                             # all-36 passes, the 12 subset (first 3) fails
        self.assertTrue(r['all']['ok'])
        self.assertFalse(r['ok'])

    def test_reverse(self):
        a, s = world({x: 'reverse' for x in SC})
        self.assertTrue(K.stable(a, s, reverse=True)['ok'])
        self.assertFalse(K.stable(a, s)['ok'])


class Attenuation(unittest.TestCase):
    def test_pass_fail(self):
        hc = world({x: 'follow' for x in SC})
        ht = world({x: 'none' for x in SC})
        self.assertTrue(K.attenuation(hc[0], ht[0], hc[1], ht[1])['ok'])
        ht2 = world({x: 'follow' for x in SC})                         # both forward: no attenuation
        self.assertFalse(K.attenuation(hc[0], ht2[0], hc[1], ht2[1])['ok'])
        hc3 = world({x: 'none' for x in SC})                           # H_C not forward: not applicable
        self.assertFalse(K.attenuation(hc3[0], ht[0], hc3[1], ht[1])['ok'])
        ht4 = world({x: 'reverse' for x in SC})                        # H_T reverse-stable: excluded by condition 1
        self.assertFalse(K.attenuation(hc[0], ht4[0], hc[1], ht4[1])['ok'])


class Design(unittest.TestCase):
    def test_structure_and_wiring(self):
        d = json.load(open(HERE / 'data/design-r01.json'))
        self.assertEqual((len(d['texts']), len(d['pairs']), len(d['primary_contrasts'])), (48, 132, 36))
        T = {t['id']: t for t in d['texts']}
        sub = [p for p in d['primary_contrasts'] if p['both_foreign_nonfirst']]
        self.assertEqual(len(sub), 12)
        # the 12-subset is exactly the receivers whose own target is listed first (CONTRACT §4.1)
        self.assertTrue(all(T[p['receiver']]['item']['target_position'] == 'first' for p in sub))
        self.assertTrue(all(T[p['receiver']]['item']['target_position'] != 'first' for p in d['primary_contrasts'] if not p['both_foreign_nonfirst']))
        import qst_run as R
        g = R.groups()
        self.assertEqual(len(g), 18)
        self.assertEqual(sorted(len(v) for v in g.values()), [2] * 6 + [3] * 12)
        p0, p1 = R.plan('formal', 0, 2), R.plan('formal', 1, 2)
        self.assertEqual(len(p0) + len(p1), 18)
        self.assertFalse({u['base_id'] for u in p0} & {u['base_id'] for u in p1})
        n_traj = sum(1 + 8 for p in d['pairs']) + 48 * 4
        self.assertEqual(n_traj, R.LIMITS['formal']['trajectories'])
        pre = [m for k in R.PREFLIGHT_GROUPS for m in g[k]]
        self.assertEqual(sorted(pre), sorted(d['preflight_ids']))
        pre_pairs = [p for p in d['pairs'] if p['receiver'] in pre]
        self.assertEqual(len(pre_pairs) * 9 + len(pre) * 4 + len(pre) + 8, R.LIMITS['preflight']['trajectories'])


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
