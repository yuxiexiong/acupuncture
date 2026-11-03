"""CPU tests for NSR-01.  Error types on hand-made answers (each type both reachable and not); type overlap; arm aggregation relative to C;
analysis entry point end to end with the real key structure; donor rule (same scenario, next ID, cyclic, never self); budget.
Replacement itself is the frozen NCC-01 code (covered by test_ncc.py and the NCC-01 real-model gates).
CUDA_VISIBLE_DEVICES= python test_nsr.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nsr_core as NS  # noqa: E402

SCN = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SCN for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
CODES = ['V47', 'V83', 'K12']


class ErrorTypes(unittest.TestCase):
    def test_types(self):
        self.assertEqual(NS.error_type(1, False, 'V47', 'V47', CODES), 'correct')
        self.assertEqual(NS.error_type(0, True, '<|im_end|>', 'V47', CODES), 'stop')
        self.assertEqual(NS.error_type(0, False, '<|im_end|>', 'V47', CODES), 'stop')          # empty body
        self.assertEqual(NS.error_type(0, False, 'V83<|im_end|>', 'V47', CODES), 'wrong')
        self.assertEqual(NS.error_type(0, False, 'V47 或 V83', 'V47', CODES), 'mixed')
        self.assertEqual(NS.error_type(0, False, '不知道', 'V47', CODES), 'other')
        self.assertEqual(NS.error_type(0, False, 'V47?', 'V47', CODES), 'other')                # only target yet judged wrong
        self.assertNotEqual(NS.error_type(0, False, 'V83', 'V47', CODES), 'mixed')

    def test_overlap(self):
        a = {'correct': 10, 'stop': 30, 'wrong': 8, 'mixed': 0, 'other': 0}
        b = {'correct': 0, 'stop': 47, 'wrong': 0, 'mixed': 1, 'other': 0}
        self.assertAlmostEqual(NS.type_overlap(a, a), 1.0)
        self.assertAlmostEqual(NS.type_overlap(a, b), 30 / 38)
        self.assertIsNone(NS.type_overlap(a, {'correct': 48, 'stop': 0, 'wrong': 0, 'mixed': 0, 'other': 0}))


def rec(y, b, et, fs=False):
    return {'Y': y, 'B': b, 'etype': et, 'first_stop': fs, 'cat': 'stop' if fs else 'code'}


class Aggregation(unittest.TestCase):
    def test_arm_block(self):
        R = {'C': {i: rec(1, 5.0, 'correct') for i in IDS},
             'X': {i: (rec(0, 1.0, 'stop', True) if i.endswith(('-0', '-1')) else rec(1, 5.0, 'correct')) for i in IDS}}
        draws = NS.NCC.boot_draws(IDS, SCEN, n=50)
        b = NS.arm_block(R, 'X', 'C', IDS, SCEN, draws)
        self.assertEqual(b['Y'], 36)
        self.assertEqual(b['vs_C'], {'net': -12, 'broken': 12, 'fixed': 0, 'n_scen_broken': 6})
        self.assertEqual(b['types']['stop'], 12)
        self.assertAlmostEqual(b['dB_vs_C']['eq'], -1.0)


class EndToEnd(unittest.TestCase):
    def test_analyse(self):
        import nsr_analysis as A
        recs = {}
        for k, i in enumerate(IDS):
            res = {'C': rec(1, 5.0, 'correct'), 'CSx': rec(1, 4.0, 'correct')}
            for d in A.NEEDLES:
                stopish = d.startswith('N_L00')
                res[d] = {'T': rec(0, -3.0, 'stop' if stopish else 'mixed', stopish)}
                for a in A.ARMS:
                    bad = a in ('CS', 'CJ') and k % 2 == 0
                    res[d][a] = rec(0 if bad else 1, 0.0 if bad else 5.0, ('stop' if stopish else 'mixed') if bad else 'correct', bad and stopish)
            recs[i] = {'scenario': SCEN[i], 'results': res}
        out = A.analyse(recs)
        b = out['needles']['N_L00_C4146_D-1']
        self.assertEqual(b['CS']['Y'], 24)
        self.assertAlmostEqual(b['type_overlap_with_T']['CS'], 1.0)
        self.assertIsNone(b['type_overlap_with_CSx']['CS'])
        self.assertAlmostEqual(b['CS_minus_CSx_paired']['eq'], -0.5)
        self.assertEqual(out['CSx']['vs_C']['broken'], 0)


class Wiring(unittest.TestCase):
    def test_donor_rule_and_budget(self):
        import nsr_run as R
        dm = R.donor_map()
        self.assertEqual(len(dm), 48)
        rows = {r['item_id']: r['base_id'] for r in R.LVKR.all_units() if r['panel'] == 'new'}
        self.assertTrue(all(dm[i] != i and rows[dm[i]] == rows[i] for i in dm))
        self.assertEqual(sorted(dm.values()), sorted(dm))                 # a permutation: every input donates once
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['trajectories'], f['formations'], f['prefix_prefills']), (576, 576, 192, 96))
        self.assertEqual((p['t1'], p['engineering']), (24, 4))
        self.assertEqual(R.ARMS, ('T', 'CS', 'CV', 'CK', 'CJ'))


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
            json.dump({'status': 'passed' if res.wasSuccessful() and not res.skipped else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'skipped': len(res.skipped), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if (res.wasSuccessful() and not res.skipped) else 1)


if __name__ == '__main__':
    main()
