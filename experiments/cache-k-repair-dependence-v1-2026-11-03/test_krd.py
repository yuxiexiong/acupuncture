"""CPU tests for KRD-01: frozen rules both pass and fail (transfer, delivery, interaction, specificity, P2); Q hook replace/capture on the
real torch kernel and wrapper restoration; budget arithmetic.  CUDA_VISIBLE_DEVICES= python test_krd.py [RECEIPT]"""
import json
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import krd_core as K  # noqa: E402

SC = [f'NQ0{k}' for k in range(1, 7)]
IDS = [f'{s}-{j}' for s in SC for j in range(8)]
SCEN = {i: i.split('-')[0] for i in IDS}
ALL = set(IDS)


def const(v):
    return {i: v(i) if callable(v) else v for i in IDS}


class Rules(unittest.TestCase):
    def test_transfer(self):
        Mr, Md = const(0.0), const(-2.0)                       # g = -2, need 0.5
        self.assertEqual(K.transfer(Mr, Md, const(-1.0), SCEN, ALL)['label'], 'transfer')
        self.assertAlmostEqual(K.transfer(Mr, Md, const(-1.0), SCEN, ALL)['ratio'], 0.5)
        self.assertEqual(K.transfer(Mr, Md, const(-0.4), SCEN, ALL)['label'], 'weak')                     # below max(0.25, 0.5)
        self.assertEqual(K.transfer(Mr, Md, const(+1.0), SCEN, ALL)['label'], 'weak')                     # wrong sign
        three = const(lambda i: -3.0 if SCEN[i] in SC[:3] else 0.5)                                    # mean -1.25 but 3/6 scenarios
        r = K.transfer(Mr, Md, three, SCEN, ALL)
        self.assertEqual((r['label'], r['n_scen_same']), ('weak', 3))
        self.assertEqual(K.transfer(Mr, const(0.3), const(0.3), SCEN, ALL)['label'], 'no_gap')

    def test_delivery(self):
        Yr, Yd = const(0), const(lambda i: int(i.endswith(('-0', '-1', '-2'))))                          # donor better by 18
        tr = {'transfer': True}
        Yc = const(lambda i: int(i.endswith(('-0',))))                                                 # +6
        self.assertEqual(K.delivery(Yr, Yd, Yc, tr)['label'], 'support')
        Yc1 = const(lambda i: int(i == 'NQ01-0'))
        self.assertEqual(K.delivery(Yr, Yd, Yc1, tr)['label'], 'no_support')                             # net 1 < 2
        self.assertEqual(K.delivery(Yr, Yd, Yc, {'transfer': False})['label'], 'no_support')            # needs M transfer
        self.assertEqual(K.delivery(Yr, Yr, Yc, tr)['label'], 'no_behaviour_gap')

    def test_interaction(self):
        y = {'00': const(0.0), '10': const(-0.2), '01': const(-0.2), '11': const(-2.0)}
        self.assertTrue(K.interaction(y, IDS, g=-2.0)['practical'])                                     # -1.6
        y['11'] = const(-0.5)
        self.assertFalse(K.interaction(y, IDS, g=-2.0)['practical'])                                    # -0.1
        yb = {'00': const(0), '10': const(0), '01': const(0), '11': const(lambda i: int(i.endswith('-0')))}
        self.assertTrue(K.interaction(yb, IDS, binary=True)['practical'])                               # 6 > 2
        yb['11'] = const(lambda i: int(i == 'NQ01-0'))
        self.assertFalse(K.interaction(yb, IDS, binary=True)['practical'])

    def test_specificity(self):
        tr = K.transfer(const(0.0), const(-2.0), const(-1.5), SCEN, ALL)
        self.assertEqual(K.specificity(tr, const(-1.5), const(-0.2), SCEN)['label'], 'specific')
        self.assertEqual(K.specificity(tr, const(-1.5), const(-1.4), SCEN)['label'], 'not_specific')
        self.assertEqual(K.specificity(tr, const(-1.5), const(-2.0), SCEN)['label'], 'not_specific')
        weak = K.transfer(const(0.0), const(-2.0), const(-0.1), SCEN, ALL)
        self.assertEqual(K.specificity(weak, const(-0.1), const(0.0), SCEN)['label'], 'no_common_transfer')

    def test_p2(self):
        self.assertEqual(K.p2(0.5, 0.7)['label'], 'holds')
        self.assertEqual(K.p2(0.95, 0.7)['label'], 'fails')
        self.assertEqual(K.p2(None, 0.7)['label'], 'not_evaluable')


class Hook(unittest.TestCase):
    def test_replace_and_capture_on_kernel(self):
        import torch
        import krd_run as R
        QM = R.gdn_module()
        orig = QM.torch_recurrent_gated_delta_rule
        g = torch.Generator().manual_seed(1)
        mk = lambda *s: torch.randn(*s, generator=g)   # noqa: E731
        q, q2, k, v = mk(1, 1, 32, 128), mk(1, 1, 32, 128), mk(1, 1, 32, 128), mk(1, 1, 32, 128)
        gg, b, S = -torch.rand(1, 1, 32, generator=g), torch.rand(1, 1, 32, generator=g), mk(1, 32, 128, 128) * 0.1
        kw = dict(g=gg, beta=b, initial_state=S.clone(), output_final_state=True, use_qk_l2norm_in_kernel=True)
        want, _ = orig(q2, k, v, **{**kw, 'initial_state': S.clone()})
        base, _ = orig(q, k, v, **{**kw, 'initial_state': S.clone()})
        fake = SimpleNamespace(model=SimpleNamespace(layers=[]))
        h = R.QHook(fake, (13,), 'replace', {13: q2})
        with h:
            h.layer = 13
            got, _ = QM.torch_recurrent_gated_delta_rule(q, k, v, **{**kw, 'initial_state': S.clone()})
            h.layer = 12
            passed, _ = QM.torch_recurrent_gated_delta_rule(q, k, v, **{**kw, 'initial_state': S.clone()})
        self.assertIs(QM.torch_recurrent_gated_delta_rule, orig)
        self.assertTrue(torch.equal(got, want) and torch.equal(passed, base) and not torch.equal(got, base))
        h.check()
        c = R.QHook(fake, (13,), 'capture')
        with c:
            c.layer = 13
            out, _ = QM.torch_recurrent_gated_delta_rule(q, k, v, **{**kw, 'initial_state': S.clone()})
        self.assertTrue(torch.equal(c.got[13], q) and torch.equal(out, base))
        bad = R.QHook(fake, (13, 14), 'capture')
        with bad:
            bad.layer = 13
            QM.torch_recurrent_gated_delta_rule(q, k, v, **{**kw, 'initial_state': S.clone()})
        with self.assertRaises(AssertionError):
            bad.check()                                                       # layer 14 never fired
        wrong = R.QHook(fake, (13,), 'replace', {13: q2[..., :64]})
        with self.assertRaises(AssertionError):
            with wrong:
                wrong.layer = 13
                QM.torch_recurrent_gated_delta_rule(q, k, v, **{**kw, 'initial_state': S.clone()})
        self.assertIs(QM.torch_recurrent_gated_delta_rule, orig)


class Wiring(unittest.TestCase):
    def test_budget(self):
        import krd_run as R
        ki = R.kernel_identity()
        self.assertFalse(ki['fla'] or ki['kernels'] or ki['causal_conv1d'])
        self.assertEqual(len(R.ORDERED), 8)
        per = 4 * (6 + 8 * 3)                                                    # 30 conditions x 4 directions per input
        f, p = R.LIMITS['formal'], R.LIMITS['preflight']
        self.assertEqual((f['t1'], f['c_t2'], f['trajectories'], f['n_steps'], f['q_extra']), (48 * 24, 48 * per, 48 * per, 48 * per * 31, 48 * 4 * 8))
        self.assertEqual(f['decode_forwards'], f['t1'] + f['c_t2'] + f['n_steps'] + f['q_extra'])
        self.assertEqual(f['decode_forwards'], 187008)
        self.assertEqual((p['t1'], p['c_t2'], p['n_steps'], p['q_extra'], p['engineering']), (2 * 24, 2 * per, 2 * per * 31, 2 * 4 * 8, R.N_ENG))
        self.assertEqual(p['decode_forwards'], p['t1'] + p['c_t2'] + p['n_steps'] + p['q_extra'] + p['engineering'])
        self.assertEqual(p['decode_forwards'], 7888)
        self.assertEqual((f['formations'], p['formations'], f['formation_token_forwards'], p['formation_token_forwards']), (240, 10, 6375, 265))
        self.assertEqual(R.GPU_CAP_S['formal'] + 2 * R.GPU_CAP_S['preflight'], 3.0 * 3600)
        self.assertEqual(R.A_LAYERS, (15, 19, 23, 27, 31))


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
