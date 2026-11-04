"""CPU tests for NWR-01 r02: outcome labels (every label reachable, strong both satisfiable and not), categories, random read (norm match, self-direction
equals the D cell, stored state native), structure comparison, budget.   CUDA_VISIBLE_DEVICES= python test_nwr.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import nwr_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}


def arm(n_correct, n_wrong=0, n_stop=None):
    """Per scenario: first n_correct inputs correct, next n_wrong explicit wrong numbers, rest stop_no_code."""
    out = {}
    for i in IDS:
        j = int(i.split('-')[1])
        out[i] = 'correct' if j < n_correct else ('wrong_num' if j < n_correct + n_wrong else 'stop_no_code')
    return out


def case(L00=0, L11=7, D=(2, 5), E=(7, 0), R=(7, 0), **kw):
    cat = {'L00': arm(L00), 'L11': arm(L11), 'D00': arm(*D), 'E00': arm(*E), 'D10': arm(3, 4)}
    cat.update({x: arm(*R) for x in K.RAND})
    return K.decide(K.rates(cat, SCEN), **kw)


class Rules(unittest.TestCase):
    def test_labels(self):
        self.assertEqual(case()['label'], 'strong')
        self.assertEqual(case(D=(2, 0))['label'], 'stop_only')                       # loss is all stops, no explicit wrong number
        self.assertEqual(case(D=(2, 5), R=(2, 5))['label'], 'not_selective')         # random of equal size does the same
        self.assertEqual(case(D=(2, 5), E=(1, 6))['label'], 'not_selective')         # the other use does more
        self.assertEqual(case(D=(6, 1))['label'], 'weak_or_opposite')                # l_D = 0.125 < 0.20
        self.assertEqual(case(D=(8, 0))['label'], 'weak_or_opposite')                # opposite sign
        self.assertEqual(case(L00=6, L11=7)['label'], 'unjudgeable')                 # b too small
        self.assertEqual(case(unreached_frac=0.3)['label'], 'unjudgeable')
        self.assertEqual(case(budget_frac_D=0.25)['label'], 'unjudgeable')
        self.assertEqual(case(D=(2, 5), R=(2, 0))['label'], 'not_selective')         # random loses as much (as stops)
        self.assertEqual(case(D=(2, 5), R=(6, 1))['label'], 'strong')                # random weaker on both axes
        self.assertEqual(case(L00=0, L11=4, D=(3, 1))['label'], 'weak_or_opposite')  # 0.125 < 0.20
        self.assertEqual(case(L00=0, L11=8, D=(5, 3))['label'], 'weak_or_opposite')  # l_D = 0.375 <= 0.5 b = 0.5

    def test_numbers(self):
        r = case()
        self.assertAlmostEqual(r['b'], 7 / 8)
        self.assertAlmostEqual(r['l_D'], 5 / 8)
        self.assertAlmostEqual(r['e_D'], 5 / 8)
        self.assertAlmostEqual(r['l_R'], 0.0)
        self.assertAlmostEqual(r['l_D10'], 4 / 8)

    def test_boot(self):
        cat = {'L00': arm(0), 'L11': arm(7), 'D00': arm(2, 5), 'E00': arm(7), 'D10': arm(3, 4)}
        cat.update({x: arm(7) for x in K.RAND})
        bt = K.scen_boot(cat, SCEN, n=200)
        self.assertAlmostEqual(bt['l_D']['point'], 5 / 8)
        self.assertLessEqual(bt['l_D']['lo'], bt['l_D']['point'])

    def test_categories(self):
        it = {'target': 'U25', 'listed_codes': ['U68', 'U25', 'U94'], 'first_listed': 'U68', 'question': '木箱的编号是什么？'}
        c = lambda t, term='stop', **kw: K.category(t, term, it, **kw)   # noqa: E731
        self.assertEqual(c('U25<|im_end|>'), ('correct', None))
        self.assertEqual(c('U68<|im_end|>'), ('wrong_num', 'first_listed'))
        self.assertEqual(c('U94<|im_end|>'), ('wrong_num', 'other_listed'))
        self.assertEqual(c('U77<|im_end|>'), ('wrong_num', 'unlisted'))
        self.assertEqual(c('<|im_end|>'), ('stop_no_code', None))
        self.assertEqual(c('<|im_end|>', reached_t2=False), ('stop_no_code', 'unreached'))
        self.assertEqual(c('U25 U68<|im_end|>')[0], 'multi_code')
        self.assertEqual(c('U68 U68 U68', 'budget')[0], 'budget')
        self.assertEqual(c('<think>U68<|im_end|>')[0], 'other')
        self.assertEqual(c('<think>\n\n</think>\n\nU68<|im_end|>'), ('wrong_num', 'first_listed'))


class Kernel(unittest.TestCase):
    def test_random_read(self):
        import torch
        import nwr_run as R
        QM = R.gdn_module()
        orig = QM.torch_recurrent_gated_delta_rule
        g = torch.Generator().manual_seed(7)
        rnd = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        q, k, v = [rnd(1, 1, 32, 128).to(torch.bfloat16) for _ in range(3)]
        gg, b = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g).to(torch.bfloat16)
        Sr, Sd = rnd(1, 32, 128, 128) * 0.1, rnd(1, 32, 128, 128) * 0.1
        o0, S0 = orig(q, k, v, g=gg, beta=b, initial_state=Sr.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        oD, SD, preD, stD, _ = R.read_use(q, k, v, gg, b, Sr.clone(), Sd, 1, 0, QM.l2norm, oracle=True)
        u = R.unit_dir(5, 13, (1, 32, 128))
        self.assertTrue(torch.allclose(u.double().norm(dim=-1), torch.ones(1, 32, dtype=torch.float64), atol=1e-6))
        self.assertTrue(torch.equal(u, R.unit_dir(5, 13, (1, 32, 128))) and not torch.equal(u, R.unit_dir(5, 14, (1, 32, 128))))
        oR, SR, preR, st, err = R.read_use_rand(q, k, v, gg, b, Sr.clone(), Sd, u, QM.l2norm)
        self.assertTrue(R.bit_equal(SR, S0)[0])                                   # stored state is the receiver's native update
        self.assertLessEqual(err, R.NORM_TOL)
        self.assertTrue(torch.allclose(st[:, 0], stD[:, 0], rtol=1e-5))           # |Dc| equals the D cell's |Dc|
        self.assertTrue(torch.allclose(st[:, 0], st[:, 1], rtol=1e-5))            # |R| == |Dc| per head
        self.assertLess(float(st[:, 2].abs().max()), 0.5)                         # random direction is not Dc
        self.assertFalse(torch.equal(oR, o0) or torch.equal(oR, oD))
        # self-direction: a unit vector along Dc reproduces the D cell
        dS = Sd.float() - Sr.float()
        _, _, pre0, _, _ = R.read_use(q, k, v, gg, b, Sr.clone(), Sd, 0, 0, QM.l2norm)
        Dc = (preD - pre0)[:, :, 0]
        us = (Dc.double() / Dc.double().norm(dim=-1, keepdim=True)).float()
        _, _, preS, _, _ = R.read_use_rand(q, k, v, gg, b, Sr.clone(), Sd, us, QM.l2norm)
        rel = float((preS.double() - preD.double()).abs().max() / max(1.0, float(preD.double().abs().max())))
        self.assertLessEqual(rel, 1e-5)
        # zero difference: nothing injected
        oZ, _, _, stZ, errZ = R.read_use_rand(q, k, v, gg, b, Sr.clone(), Sr, u, QM.l2norm)
        self.assertTrue(R.bit_equal(oZ, o0)[0] and errZ == 0.0)

    def test_structure(self):
        import torch
        import nwr_run as R
        t = lambda: torch.ones(2, 3)   # noqa: E731
        a = {13: {n: t() for n in R.SFIELDS}, 14: {n: t() for n in R.SFIELDS}}
        b = {13: {n: t() for n in R.SFIELDS}, 14: {n: t() for n in R.SFIELDS}}
        b[13]['v'] = t() * 2
        b[14]['v'], b[14]['q'] = t() * 2, t() * 3
        s = R.struct_compare(a, b, (13, 14))
        self.assertTrue(R.struct_ok(s, (13, 14)))
        self.assertEqual((s['13']['q'], s['13']['v'], s['14']['q'], s['14']['S0']), (True, False, False, True))
        b[13]['k'] = t() * 5
        self.assertFalse(R.struct_ok(R.struct_compare(a, b, (13, 14)), (13, 14)))


class Wiring(unittest.TestCase):
    def test_budget(self):
        import nwr_run as R
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['trajectories'], f['c_t2'], f['refs'], f['shadow']), (48 * 4, 48 * 12, 48 * 9, 48 * 3, 48 * 56))
        self.assertEqual(f['decode_forwards'], 48 * (4 + 3 + 9 + 12 * 31))
        self.assertEqual(p['trajectories'], 24)
        self.assertEqual(len(R.ARMS), 12)
        self.assertLessEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 1.5 * 3600)
        self.assertEqual(len(R.plan('formal', 0, 2)) + len(R.plan('formal', 1, 2)), 48)
        self.assertEqual(sorted(u['item_id'] for u in R.plan('preflight', 0, 1)), sorted(R.PREFLIGHT_ITEMS))
        self.assertEqual(list(R.conditions()), [R.DIR])
        self.assertEqual(R.SEEDS, (202611051, 202611052, 202611053, 202611054, 202611055))


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
