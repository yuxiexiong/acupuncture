"""CPU tests for NQ-01 (synthetic worlds that must pass AND fail each rule).  CUDA_VISIBLE_DEVICES= python test_nq.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nq_core as K  # noqa: E402
import make_inputs as MI  # noqa: E402

ROWS = MI.build()
SCEN = sorted({r['base_id'] for r in ROWS})


def cells(policy, scen='NQ02', flip=0):
    """policy: 'query' | 'first' | 'identity' | 'stop'; flip = number of cells forced to stop (no code)."""
    out = []
    for k, r in enumerate([r for r in ROWS if r['base_id'] == scen]):
        code = {'query': r['target'], 'first': r['first_listed'], 'identity': r['binding']['B'][1], 'stop': None}[policy]
        if k < flip:
            code = None
        out.append({'delivered': code == r['target'], 'unique': code, 'first_listed': r['first_listed']})
    return out


class Scenario(unittest.TestCase):
    def test_categories_pass(self):
        self.assertEqual(K.scenario_category(cells('query')), 'follow_query')
        self.assertEqual(K.scenario_category(cells('first')), 'follow_first')
        self.assertEqual(K.scenario_category(cells('identity')), 'follow_identity')
        self.assertEqual(K.scenario_category(cells('query', flip=1)), 'follow_query')          # 8/9

    def test_categories_fail(self):
        self.assertEqual(K.scenario_category(cells('query', flip=2)), 'mixed')                 # 7/9
        self.assertEqual(K.scenario_category(cells('first', flip=2)), 'mixed')
        self.assertEqual(K.scenario_category(cells('stop')), 'mixed')
        # first-listed policy delivers the target in exactly 3/9 cells; identity in 3/9
        self.assertEqual(sum(c['delivered'] for c in cells('first')), 3)
        self.assertEqual(sum(c['delivered'] for c in cells('identity')), 3)
        self.assertEqual(sum(c['unique'] == c['first_listed'] for c in cells('identity')), 3)


class Direction(unittest.TestCase):
    def test_label(self):
        self.assertEqual(K.direction_label({s: 'follow_first' for s in SCEN}), 'follow_first')
        self.assertEqual(K.direction_label({s: ('follow_first' if s != 'NQ01' else 'mixed') for s in SCEN}), 'follow_first')
        self.assertEqual(K.direction_label({s: ('follow_first' if s not in ('NQ01', 'NQ02') else 'follow_query') for s in SCEN}), 'mixed')

    def test_applicability_and_status(self):
        good = {s: cells('query', s) for s in SCEN}
        bad = {s: cells('query', s, flip=(2 if s in ('NQ01', 'NQ02') else 0)) for s in SCEN}
        self.assertTrue(K.c_applicable(good)['panel_ok'])
        self.assertFalse(K.c_applicable(bad)['panel_ok'])                                     # 4/6 scenarios
        tstop = {s: cells('stop', s) for s in SCEN}
        self.assertTrue(K.damage_transfer(good, tstop)['transferred'])
        self.assertFalse(K.damage_transfer(good, good)['transferred'])
        part = {s: (cells('stop', s) if s in ('NQ01', 'NQ02', 'NQ03') else cells('query', s)) for s in SCEN}
        self.assertFalse(K.damage_transfer(good, part)['transferred'])                       # 3/6
        self.assertEqual(K.status(False, True, 'follow_first', 'follow_first'), 'not_applicable_baseline')
        self.assertEqual(K.status(True, False, 'follow_first', 'follow_first'), 'not_applicable_damage')
        self.assertEqual(K.status(True, True, 'follow_first', 'follow_first'), 'support')
        self.assertEqual(K.status(True, True, 'mixed', 'follow_first'), 'unsupported')

    def test_overall_fixed_denominator(self):
        self.assertTrue(K.overall({'a': 'support', 'b': 'support', 'c': 'support', 'd': 'unsupported'})['met'])
        r = K.overall({'a': 'support', 'b': 'support', 'c': 'not_applicable_damage', 'd': 'support'})
        self.assertTrue(r['met'])
        r = K.overall({'a': 'support', 'b': 'support', 'c': 'not_applicable_damage', 'd': 'unsupported'})
        self.assertFalse(r['met'])
        self.assertEqual(r['n_not_applicable'], 1)

    def test_paired(self):
        c, t, a = cells('query'), cells('stop'), cells('first')
        self.assertEqual(K.paired_improvement(c, t, a), 3)
        self.assertEqual(K.paired_improvement(c, c, a), 0)                                    # naturally right is not recovery
        self.assertEqual(K.pairing(cells('query'), cells('first')), {'a_only': 6, 'b_only': 0, 'both': 3, 'neither': 0})


class Q(unittest.TestCase):
    def test_q(self):
        base = {'A': 1.0, 'B': 0.5, 'C': 0.0}
        bonus = 2.0
        zq = {q: {k: v + (bonus if k == q else 0.0) for k, v in base.items()} for q in 'ABC'}
        self.assertEqual(K.q_values(zq), {'AB': 2.0, 'AC': 2.0, 'BC': 2.0})
        zn = {q: dict(base) for q in 'ABC'}                                                  # query-blind: Q = 0
        self.assertEqual(K.q_values(zn), {'AB': 0.0, 'AC': 0.0, 'BC': 0.0})
        shift = {q: {k: v + 5.0 * (q == 'A') for k, v in base.items()} for q in 'ABC'}       # vocab-wide shift is invisible
        self.assertEqual(K.q_values(shift), {'AB': 0.0, 'AC': 0.0, 'BC': 0.0})


class Panel(unittest.TestCase):
    def test_panel_and_wiring(self):
        self.assertTrue(MI.check(ROWS))
        import nq_run as R
        self.assertEqual([r['id'] for r in R.items()], [r['id'] for r in ROWS])
        self.assertEqual(R.items(), json.loads(json.dumps(ROWS, ensure_ascii=False)))
        self.assertEqual(R.LIMITS['formal'], {'formations': 270, 'trajectories': 702, 'decode_forwards': 22464, 'diagnostics': 702, 'calibrations': 6})
        p0, p1 = R.plan('formal', 0, 2), R.plan('formal', 1, 2)
        self.assertEqual(len(p0), 27)
        self.assertEqual(len(p1), 27)
        self.assertFalse({u['base_id'] for u in p0} & {u['base_id'] for u in p1})
        pre = R.plan('preflight', 0, 1)
        self.assertEqual([u['key'] for u in pre], ['NQ01-ABC-A', 'REPLAY-SP01-f0'])


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
