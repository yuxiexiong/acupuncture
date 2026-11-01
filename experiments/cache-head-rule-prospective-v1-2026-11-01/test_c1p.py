"""CPU tests for C1-P (no weights).  CUDA_VISIBLE_DEVICES= python test_c1p.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import c1p_core as K  # noqa: E402
import c1p_analysis as A  # noqa: E402
import torch  # noqa: E402

H = [[30, j] for j in range(9)] + [[14, j] for j in range(5)] + [[25, j] for j in range(31)]


class Subsets(unittest.TestCase):
    def test_random_layer_matched_deterministic(self):
        u1, u1b, u2 = K.random_subset('P01-f0', 1, H), K.random_subset('P01-f0', 1, H), K.random_subset('P01-f0', 2, H)
        self.assertEqual(u1, u1b)
        self.assertNotEqual(u1, u2)
        cnt = lambda s: sorted((l, sum(1 for x in s if x[0] == l)) for l in {x[0] for x in s})   # noqa: E731
        self.assertEqual(cnt(u1), cnt(H))
        self.assertEqual(len({tuple(x) for x in u1}), 45)

    def test_conv_subset(self):
        g = torch.Generator().manual_seed(0)
        fT, fC = (torch.randn(1, 8192, 4, generator=g).to(torch.bfloat16) for _ in range(2))
        o = K.conv_subset(fT, fC, [[30, 2], [14, 5]], 30)
        self.assertTrue(torch.equal(o[:, :4096], fC[:, :4096]))
        for h in range(32):
            a = 4096 + 128 * h
            self.assertTrue(torch.equal(o[:, a:a + 128], (fT if h == 2 else fC)[:, a:a + 128]))
        self.assertTrue(torch.equal(K.conv_subset(fT, fC, [], 30), fC))

    def test_top_heads_ties(self):
        sc = [(0.5, 20, 3), (-0.5, 14, 7), (0.5, 14, 9), (0.1, 13, 0)]
        self.assertEqual(K.top_heads(sc, 3), [[14, 7], [14, 9], [20, 3]])


def facts(F, Hv, U, FIX=None):
    return [{'F': F[k], 'H': Hv[k], 'FIX': (FIX or Hv)[k], 'U': U[k]} for k in (0, 1)]


class Criteria(unittest.TestCase):
    def test_scenario(self):
        ok = K.scenario_check(facts((4, 5), (3, 3.5), ([0.5] * 4, [1.0] * 4)))
        self.assertTrue(ok['pass'])
        self.assertFalse(K.scenario_check(facts((4, 5), (1.5, 1.5), ([0.5] * 4, [0.5] * 4)))['retain_ok'])   # < 0.5 F
        e = K.scenario_check(facts((4, 5), (3, 3), ([2.9] * 4, [2.9] * 4)))                               # E = 0.1
        self.assertTrue(e['retain_ok'] and not e['E_ok'])
        self.assertFalse(K.scenario_check(facts((0.5, 0.6), (0.5, 0.6), ([0.0] * 4, [0.0] * 4)))['F_ok'])

    def test_judge(self):
        p = {'pass': True, 'F_ok': True, 'retain_ok': True}
        f = {'pass': False, 'F_ok': True, 'retain_ok': True}
        n = {'pass': False, 'F_ok': False, 'retain_ok': False}
        self.assertEqual(K.judge({i: p for i in range(6)})['decision'], 'support')
        self.assertEqual(K.judge({i: f for i in range(6)})['decision'], 'subset_effective_no_advantage')
        self.assertEqual(K.judge({**{i: n for i in range(2)}, **{i: p for i in range(2, 6)}})['decision'], 'insufficient_F')
        self.assertEqual(K.judge({**{i: {'pass': False, 'F_ok': True, 'retain_ok': False} for i in range(6)}})['decision'], 'rule_not_realized')


def synth(h_eff):
    recs = []
    for s in ['P01', 'P02', 'P03', 'P04', 'P05', 'P06']:
        for k in (0, 1):
            cells = {}
            vals = {'N:CC': 0.0, 'N:CT': 5.0, 'N:CH': h_eff, 'N:CFIX': h_eff, 'N:CU1': 0.5, 'N:CU2': 0.6, 'N:CU3': 0.4, 'N:CU4': 0.7}
            for c, z in vals.items():
                cells[c] = {'readout': {'primary': {'cz_s46': z, 'cz_a': -z}, 'eos': False}}
            recs.append({'item': {'id': f'{s}-f{k}', 'base_id': s}, 'cells': cells, 'overlap': {}})
    return recs


class Consumer(unittest.TestCase):
    def test_support_and_failure(self):
        self.assertEqual(A.analyse(synth(4.0))['primary_decision'], 'support')
        self.assertEqual(A.analyse(synth(1.0))['primary_decision'], 'rule_not_realized')
        self.assertEqual(A.analyse(synth(4.0))['sides']['answer']['arms']['H']['decision'], 'insufficient_F')


class Wiring(unittest.TestCase):
    def test_plan_inputs(self):
        import c1p_run as V
        rows = V.items()
        self.assertEqual(len(rows), 12)
        self.assertEqual([u['item_id'] for u in V.plan('preflight', 0, 1)], list(V.PREFLIGHT_ITEMS))
        w0, w1 = V.plan('formal', 0, 2), V.plan('formal', 1, 2)
        self.assertEqual(len(w0) + len(w1), 12)
        self.assertFalse({u['base_id'] for u in w0} & {u['base_id'] for u in w1})
        fx = json.loads(V.FIXED.read_text())['heads']
        self.assertEqual(len({tuple(x) for x in fx}), 45)
        self.assertEqual(V.LIMITS['formal'], {'formations': 24, 'scores': 132})


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun,
                       'failures': len(res.failures), 'errors': len(res.errors), 'skipped': len(res.skipped),
                       'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
