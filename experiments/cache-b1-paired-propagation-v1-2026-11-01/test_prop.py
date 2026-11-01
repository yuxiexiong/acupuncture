"""CPU tests for the frozen screening / unit-response rules (prop_core.py). No data, no model.

python test_prop.py
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import prop_core as P  # noqa: E402

S6 = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6']
SCEN = {f'{s}-{k}': s for s in S6 for k in (0, 1)}


def mk(del_vals, rnd=0.1):
    return {i: {'DEL': del_vals[i] if isinstance(del_vals, dict) else del_vals, 'RAND0': rnd, 'RAND1': -rnd} for i in SCEN}


class Screen(unittest.TestCase):
    def test_selected(self):
        r = P.screen(mk(-0.6), SCEN)
        self.assertTrue(r['selected'])
        self.assertEqual(r['n_pass'], 6)

    def test_not_beyond_random(self):
        self.assertFalse(P.screen(mk(-0.6, rnd=0.55), SCEN)['selected'])         # 0.6 not > 0.55 + 0.1

    def test_facts_disagree(self):
        v = {i: (-0.6 if i.endswith('0') else 0.6) for i in SCEN}
        self.assertEqual(P.screen(mk(v), SCEN)['n_pass'], 0)

    def test_sign_flip_across_scenarios(self):
        v = {i: (-0.6 if SCEN[i] in ('S1', 'S2', 'S3') else 0.6) for i in SCEN}
        r = P.screen(mk(v), SCEN)
        self.assertEqual(r['n_pass'], 6)
        self.assertFalse(r['selected'])                                          # passes but signs inconsistent

    def test_four_of_six(self):
        v = {i: (-0.6 if SCEN[i] in ('S1', 'S2', 'S3', 'S4') else 0.0) for i in SCEN}
        self.assertFalse(P.screen(mk(v), SCEN)['selected'])


class Decide(unittest.TestCase):
    def test_branches(self):
        sel = P.screen(mk(-0.6), SCEN)
        sel2 = P.screen(mk(-0.9), SCEN)
        no = P.screen(mk(0.0), SCEN)
        d = P.decide({'14:mix': sel, '15:rest': sel2, '16:mix': no}, {})
        self.assertEqual(d['decision'], 'candidate')
        self.assertEqual(d['priority'], '15:rest')
        self.assertEqual(d['alternates'], ['14:mix'])
        self.assertEqual(P.decide({'14:mix': no}, {'14:mix': sel})['decision'], 'end_branch_mixed_lead_only')
        self.assertEqual(P.decide({'14:mix': no}, {'14:mix': no})['decision'], 'end_branch_no_candidate')
        self.assertEqual(len(P.modules()), 36)


class Unit(unittest.TestCase):
    def test_display_rule(self):
        self.assertAlmostEqual(P.unit_response(0.5, 0.1, 100.0)['gamma'], 5.0)
        self.assertIsNone(P.unit_response(0.5, 0.001, 100.0)['gamma'])            # rel 1e-5 < 1e-4
        sc = P.scenario_unit_response({'S1-0': {'num': 1.0, 'den': 0.2}, 'S1-1': {'num': 0.0, 'den': 0.6}}, {'S1-0': 'S1', 'S1-1': 'S1'},
                                      {'S1-0': 100.0, 'S1-1': 100.0})
        self.assertAlmostEqual(sc['S1']['gamma'], 0.5 / 0.4)                      # mean num / mean den, not mean of ratios

    def test_closure(self):
        self.assertTrue(P.closure_ok([1.0, -0.5, 0.25], 0.75)[0])
        self.assertFalse(P.closure_ok([1.0, -0.5, 0.25], 0.76)[0])


if __name__ == '__main__':
    unittest.main(verbosity=2)
