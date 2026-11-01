"""CPU tests for EH-XC (CONTRACT §5 list).  CUDA_VISIBLE_DEVICES= python test_xc.py [RECEIPT_JSON]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import xc_core as K  # noqa: E402
import xc_analysis as A  # noqa: E402


def eff(D00=-12.0, D10=-11.0, D01=-7.0, D11=-4.0, DP=1.0):
    return K.effects(D00, D10, D01, D11, DP)


class Rules(unittest.TestCase):
    def test_applicability(self):
        self.assertEqual(K.applicability(eff()), 'applicable')
        self.assertEqual(K.applicability(eff(D11=-11.5)), 'native_strong_mixed_weak')       # N>=1, E<1
        self.assertEqual(K.applicability(eff(DP=-11.5, D11=-11.5)), 'native_insufficient')
        self.assertEqual(K.applicability(eff(D11=-14.0)), 'reverse_effect')                   # negative E
        self.assertEqual(K.applicability(eff(DP=-14.0)), 'reverse_effect')

    def test_p_h(self):
        self.assertTrue(K.p_h(eff()))                                                         # H0 5 >= 4, > X0 1
        self.assertFalse(K.p_h(eff(D01=-9.0)))                                                 # H0 3 < 0.5*8
        self.assertFalse(K.p_h(eff(D10=-6.0, D01=-7.0)))                                       # H0 5 < X0 6

    def test_p_i_boundaries(self):
        # E = 8 -> threshold max(0.5, 0.8) = 0.8 ; I = D11 - D10 - D01 + D00
        e = eff(D00=-12.0, D10=-11.0, D01=-5.8, D11=-4.0)                                     # I = 0.8 exactly
        self.assertAlmostEqual(e['I'], 0.8)
        self.assertTrue(K.p_i(e))
        self.assertFalse(K.p_i(eff(D00=-12.0, D10=-11.0, D01=-5.79, D11=-4.0)))
        e2 = eff(D00=-12.0, D10=-11.8, D01=-10.0, D11=-9.3)                                   # E = 2.7 -> threshold 0.5, I = 0.5
        self.assertAlmostEqual(e2['I'], 0.5)
        self.assertTrue(K.p_i(e2))
        self.assertFalse(K.p_i(eff(D00=-12.0, D10=-11.8, D01=-10.0, D11=-9.31)))

    def test_scenario_and_fact_disagreement(self):
        s = K.fact_status(eff())
        bad = K.fact_status(eff(D01=-9.0))
        na = K.fact_status(eff(D11=-11.5))
        self.assertEqual(K.scenario_support(s, s, 'hist'), 'support')
        self.assertEqual(K.scenario_support(s, bad, 'hist'), 'fact_disagreement')
        self.assertEqual(K.scenario_support(s, na, 'hist'), 'partly_not_applicable')
        self.assertEqual(K.scenario_support(na, na, 'hist'), 'native_strong_mixed_weak')

    def test_panels(self):
        L = {f'd{i}': {'replicated': i < 6} for i in range(8)}
        self.assertTrue(K.panel(L, list(L), 6)['met'])
        L5 = {f'd{i}': {'replicated': i < 5} for i in range(8)}
        self.assertFalse(K.panel(L5, list(L5), 6)['met'])
        R = {f'r{i}': {'replicated': i < 3} for i in range(4)}
        self.assertTrue(K.panel(R, list(R), 3)['met'])
        R2 = {f'r{i}': {'replicated': i < 2} for i in range(4)}
        self.assertFalse(K.panel(R2, list(R2), 3)['met'])
        self.assertEqual(K.panel(L5, list(L5), 6)['of'], 8)                                    # denominator not reduced

    def test_spacing(self):
        self.assertEqual(K.bf16_spacing(20.0), 0.125)
        self.assertEqual(K.bf16_spacing(-5.0), 2 ** -5)


def synth(world):
    """world 'all': every needle applicable and supporting; 'weak5': only 5 validation channels apply; 'Fdiff': D passes, F does not."""
    recs = {}
    for s in range(1, 7):
        for f in (0, 1):
            iid = f'P0{s}-f{f}'

            def cell(D, a_raw=10.0, eos=None, tv=None):
                c = {'readout': {'D': D, 'raw': {'s44': -5.0, 's46': 10.0 + D, 'a': a_raw}},
                     'score': {'first_step_eos': D > 0 if eos is None else eos, 'stop_winner': 248046, 'nonstop_winner': 7}}
                if tv is not None:
                    c['tv_vs_C'] = tv
                return c
            cells = {'C_native': cell(-12.0)}
            for j, d in enumerate(A.ALL):
                weak = world == 'weak5' and d in A.VALIDATION[5:]
                vals = (-11.0, -7.0, -4.0, 1.0) if not weak else (-12.0, -12.0, -12.0, -11.8)
                for c, D in zip(('X10', 'H01', 'XH11', 'T_native'), vals):
                    a_raw = 10.0
                    if world == 'Fdiff' and c == 'XH11':
                        a_raw = 10.0 + 1.5                                  # competitor changes F only
                    cells[f'{c}|{d}'] = cell(D, a_raw=a_raw, tv=0.1 if c in ('XH11', 'T_native') else None)
            recs[iid] = {'item': {'id': iid}, 'cells': cells}
    return recs


class Consumer(unittest.TestCase):
    def test_all_support(self):
        res = A.analyse(synth('all'))
        self.assertTrue(res['P_XC']['met'] and res['P_R']['met'])
        self.assertEqual(res['P_XC']['of'], 8)

    def test_weak_channels_keep_denominator(self):
        res = A.analyse(synth('weak5'))
        self.assertFalse(res['P_XC']['met'])
        self.assertEqual(res['P_XC']['n'], 5)
        self.assertEqual(res['P_XC']['of'], 8)
        d = A.VALIDATION[6]
        self.assertEqual(res['needles'][d]['applicability_counts'], {'native_insufficient': 12})

    def test_F_differs_from_D(self):
        res = A.analyse(synth('Fdiff'))
        self.assertGreater(res['needles'][A.VALIDATION[0]]['n_I_D_passes_F_not'], 0)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import eh_xc_run as R
        per_input = 1 + len(R.DIRECTIONS) * (1 + len(R.ARMS))
        self.assertEqual(len(R.DIRECTIONS), 14)
        self.assertEqual(per_input, 57)
        self.assertEqual(R.LIMITS['formal'], {'formations': 180, 'scores': 684, 'calibrations': 6})
        self.assertEqual(R.LIMITS['preflight'], {'formations': 17, 'scores': 59, 'calibrations': 1})
        self.assertEqual(set(R.DIRECTIONS), set(A.ALL))
        self.assertEqual(R.DIRECTIONS[:4], R.EH_DIRS)


def main():
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in sorted(HERE.glob('*.py')) + sorted((HERE / 'readiness').glob('*.py'))}
        import torch
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src, 'torch': torch.__version__}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
