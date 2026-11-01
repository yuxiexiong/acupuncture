"""CPU tests for NFC-01 (no weights).  python test_nfc.py [RECEIPT_JSON]"""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nfc_core as K  # noqa: E402
import nfc_run as R  # noqa: E402

A_TOK = 1000


def cell(z44, z46, za, nonstop_max, vm, nonstop_winner=A_TOK, sha='x'):
    stop_max = max(z44, z46)
    D = stop_max - nonstop_max
    return {'readout': {'raw': {'s44': z44, 's46': z46, 'a': za}, 'D': D, 'vocab_mean': vm},
            'score': {'stop_winner': 248044 if z44 >= z46 else 248046, 'nonstop_winner': nonstop_winner,
                      'first_step_eos': D > 0, 'stop_advantage': D, 'logits_sha256': sha}}


def shift(c, k):
    c = copy.deepcopy(c)
    for key in ('s44', 's46', 'a'):
        c['readout']['raw'][key] += k
    c['readout']['vocab_mean'] += k
    return c


class Terms(unittest.TestCase):
    def test_identity_and_shift_invariance(self):
        u = cell(1.0, 3.0, 5.0, 5.0, 0.0)
        v = cell(2.0, 6.0, 4.0, 4.5, 0.3, nonstop_winner=7)
        s0, q0 = 248046, A_TOK
        tu, tv = K.cell_terms(u['readout'], u['score'], s0, q0), K.cell_terms(v['readout'], v['score'], s0, q0)
        self.assertAlmostEqual(tu['identity_err'], 0.0)
        self.assertEqual((tu['A'], tu['B']), (0.0, 0.0))                      # on the clean cell A = B = 0
        self.assertGreater(tv['B'], 0.0)                                        # dynamic non-stop winner != q0
        e = K.edge(tu, tv)
        tv2 = K.cell_terms(*[shift(v, 10.0)[k] for k in ('readout', 'score')], s0, q0)
        e2 = K.edge(tu, tv2)
        for k in ('D', 'F', 'A', 'B', 'S_mean', 'Q_mean'):
            self.assertAlmostEqual(e[k], e2[k])                                 # common shift: no change
        self.assertNotAlmostEqual(e['dz_s0'], e2['dz_s0'])                      # raw one-sided change does move
        self.assertAlmostEqual(e['split_err'], 0.0)
        self.assertTrue(e['winner_change']['nonstop'])

    def test_chain_and_flip(self):
        s0, q0 = 248046, A_TOK
        Ds = [-2.0, -1.0, 1.5, 1.0, 2.0]
        cells = {}
        for n, D in zip(K.CHAIN, Ds):
            c = cell(0.0, 10.0, 10.0 - D, 10.0 - D, 0.0)
            cells[n] = K.cell_terms(c['readout'], c['score'], s0, q0)
        ch = K.chain(cells)
        self.assertAlmostEqual(ch['delta_native'], 4.0)
        self.assertAlmostEqual(ch['telescope_err'], 0.0)
        self.assertEqual(ch['largest_abs_edge'], 'e2')
        self.assertEqual(ch['eos_flip_edges'], ['e2'])
        self.assertAlmostEqual(sum(ch['concentration'].values()), 1.0)
        flat = {n: K.cell_terms(*[cell(0.0, 1.0, 1.0, 1.0, 0.0)[k] for k in ('readout', 'score')], s0, q0) for n in K.CHAIN}
        self.assertIsNone(K.chain(flat)['concentration'])

    def test_labels(self):
        self.assertEqual(K.aux_label(3.0, 0.4), 'native_small')
        self.assertEqual(K.aux_label(0.4, 3.0), 'mixed_small')
        self.assertEqual(K.aux_label(-1.0, 3.0), 'opposite')
        self.assertEqual(K.aux_label(3.75, 3.0), 'same_direction_close')       # |diff| = 0.75 = 25% of 3
        self.assertEqual(K.aux_label(3.76, 3.0), 'same_direction_different_size')
        self.assertEqual(K.aux_label(1.2, 1.0), 'same_direction_close')        # 0.25 absolute floor
        self.assertEqual(K.transition(False, True), 'nonstop_to_stop')
        c = K.crest_split({'N:CC': 0.0, 'N:CFIX': 3.0, 'N:CT': 2.5, 'N:CREST': 1.0})
        self.assertAlmostEqual(c['R_D'] + c['I_D'], c['e3'])
        self.assertNotAlmostEqual(c['I_D'], c['e3'])                           # e3 is not the interaction
        lab, _ = K.direction_label({f'P0{s}': ('e1', 'e1') for s in range(1, 7)})
        self.assertEqual(lab, 'e1')
        self.assertEqual(K.cross_label({0: 'e1', 1: 'e2', 2: None, 3: 'e1'}), 'condition_dependent')


def synth(junction_ok=True, tie=False):
    b3, b4 = {}, {}
    for s in range(1, 7):
        for f in (0, 1):
            iid = f'P0{s}-f{f}'
            cn = cell(0.0, 8.0, 10.0, 10.0, 0.0, sha='cn')
            r3 = {'a_token': A_TOK, 'item': {'id': iid}, 'cells': {'C_native': cn}}
            r4 = {'a_token': A_TOK, 'item': {'id': iid}, 'cells': {'C_native': copy.deepcopy(cn)}}
            for d in R.DIRECTIONS:
                specs = {'T_native': 11.0, 'N:TT': 11.0, 'N:CC': 9.0, 'N:CFIX': 12.0, 'N:CT': 11.5, 'N:CREST': 9.5}
                for c, zs in specs.items():
                    r3['cells'][f'{c}|{d}'] = cell(0.0, zs, 10.0, 10.0 if not (tie and c == 'N:CC') else zs, 0.0, sha=f'{c}{d}' if c != 'N:TT' else f'T_native{d}')
                for n4, n3 in (('T_native', 'T_native'), ('CC', 'N:CC'), ('CFIX', 'N:CFIX')):
                    r4['cells'][f'{n4}|{d}'] = copy.deepcopy(r3['cells'][f'{n3}|{d}'])
                for c, zs in (('K', 11.8), ('M_nat', 11.9), ('M_rand', 12.0)):
                    r4['cells'][f'{c}|{d}'] = cell(0.0, zs, 10.0, 10.0, 0.0)
            if not junction_ok and iid == 'P03-f1':
                r4['cells'][f'CFIX|{R.DIRECTIONS[1]}']['score']['logits_sha256'] = 'other'
            b3[iid], b4[iid] = r3, r4
    return b3, b4


class Consumer(unittest.TestCase):
    def test_end_to_end(self):
        b3, b4 = synth()
        per, gates = R.analyse(b3, b4)
        S = R.summarise(per)
        d = R.DIRECTIONS[0]
        self.assertAlmostEqual(S[d]['mean_delta_native'], 3.0)
        self.assertAlmostEqual(sum(S[d]['mean_edges_D'].values()), 3.0)
        self.assertEqual(S[d]['largest_edge']['label'], 'e2')
        self.assertEqual(S[d]['transitions'], {'nonstop_to_stop': 12})
        self.assertEqual(S['cross']['aux_fix_vs_native'], 'same_direction_close')
        self.assertLess(gates['max_telescope_err'], 1e-12)

    def test_junction_and_tie(self):
        with self.assertRaises(AssertionError):
            R.analyse(*synth(junction_ok=False))
        per, gates = R.analyse(*synth(tie=True))
        self.assertIn('ties', gates)


def main():
    receipt = sys.argv[1] if len(sys.argv) > 1 else None
    res = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__]))
    if receipt:
        import hashlib
        repo = HERE.parent.parent
        src = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.glob('*.py'))}
        with open(receipt, 'x') as f:
            json.dump({'status': 'passed' if res.wasSuccessful() else 'failed', 'tests_run': res.testsRun, 'failures': len(res.failures),
                       'errors': len(res.errors), 'source_hashes': src}, f, indent=2)
            f.write('\n')
    sys.exit(0 if res.wasSuccessful() else 1)


if __name__ == '__main__':
    main()
